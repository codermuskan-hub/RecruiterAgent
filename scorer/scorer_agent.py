import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()

# Ensure scorer folder and project root are in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
for p in [current_dir, project_root]:
    if p not in sys.path:
        sys.path.append(p)

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from score_calculator import calculate_weighted_score

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=GROQ_API_KEY,
    temperature=0.0,
    max_tokens=2000
)

scorer_tools = [calculate_weighted_score]

# Support both LangChain legacy create_tool_calling_agent and new create_agent
try:
    from langchain.agents import create_tool_calling_agent, AgentExecutor
    scorer_prompt = ChatPromptTemplate.from_messages([
        ("system", 
         "You are an expert Indian Tech Recruiter Scoring Agent. Your task is to evaluate a candidate based on their "
         "parsed resume JSON, skill match report, Indian tech profile (Tier-1/2/3 college, notice period, CTC, location), "
         "and Job Description requirements.\n"
         "Use your tool `calculate_weighted_score` to calculate the final weighted candidate score out of 100 based on:\n"
         "- skill_fit_score (weight 50%)\n"
         "- experience_fit_score (weight 30%)\n"
         "- education_fit_score (weight 20%)\n"
         "- college_tier and notice_period_days\n"
         "Provide a detailed breakdown, strengths, gaps, and recruitment recommendation."
        ),
        ("user", 
         "Candidate Resume JSON:\n{resume_json}\n\n"
         "Skill Match Analysis:\n{match_report}\n\n"
         "Indian Tech Profile:\n{indian_profile}\n\n"
         "Job Description:\n{jd_text}\n\n"
         "Please evaluate and compute the final score for this candidate."
        ),
        ("placeholder", "{agent_scratchpad}"),
    ])
    scoring_agent = create_tool_calling_agent(llm, scorer_tools, scorer_prompt)
    scorer_executor = AgentExecutor(agent=scoring_agent, tools=scorer_tools, verbose=True)
except (ImportError, AttributeError):
    from langchain.agents import create_agent
    scorer_executor = create_agent(
        model=llm,
        tools=scorer_tools,
        system_prompt="You are an expert Recruiter Scoring Agent. Evaluate the candidate using `calculate_weighted_score` and produce a scored recruitment report."
    )


def run_scorer_pipeline(resume_json: dict, match_report: dict, jd_text: str, indian_profile: dict = None) -> dict:
    """
    Evaluates candidate details and JD to produce final weighted scores, recommendation, and assessment.
    """
    if indian_profile is None:
        indian_profile = {}

    matched = match_report.get("matched_skills", [])
    missing = match_report.get("missing_skills", [])
    total_skills = len(matched) + len(missing)
    
    # 1. Skill fit score (50% weight component)
    if total_skills > 0:
        skill_fit_score = (len(matched) / total_skills) * 100.0
    else:
        skill_fit_score = match_report.get("score", 0.0)

    # 2. Experience fit score (30% weight component)
    exp_entries = resume_json.get("experience", [])
    exp_score = 70.0  # Baseline score for having experience listed
    if isinstance(exp_entries, list) and len(exp_entries) > 0:
        exp_score = min(100.0, 70.0 + (len(exp_entries) * 10.0))
    elif isinstance(exp_entries, str) and len(exp_entries.strip()) > 10:
        exp_score = 75.0

    # 3. Education fit score (20% weight component)
    edu_entries = resume_json.get("education", [])
    cert_entries = resume_json.get("certifications", [])
    edu_score = 70.0
    if edu_entries:
        edu_score += 15.0
    if cert_entries:
        edu_score += 15.0
    edu_score = min(100.0, edu_score)

    college_tier = indian_profile.get("college_tier", "Tier-3")
    notice_days = int(indian_profile.get("notice_period_days", 30))

    # Compute weighted score via tool
    tool_args = {
        "skill_fit_score": skill_fit_score,
        "experience_fit_score": exp_score,
        "education_fit_score": edu_score,
        "college_tier": college_tier,
        "notice_period_days": notice_days
    }
    
    if hasattr(calculate_weighted_score, "invoke"):
        calc_json_str = calculate_weighted_score.invoke(tool_args)
    else:
        calc_json_str = calculate_weighted_score(**tool_args)
        
    calc_res = json.loads(calc_json_str)

    # Ask LLM agent to generate qualitative recruiter summary with Indian tech context
    prompt = (
        f"Candidate Name: {resume_json.get('name', 'Candidate')}\n"
        f"Calculated Weighted Score: {calc_res['overall_score']}/100\n"
        f"Recommendation: {calc_res['recommendation']}\n"
        f"College Tier: {college_tier} ({indian_profile.get('college_name', 'College')})\n"
        f"Notice Period: {notice_days} days\n"
        f"Location: {indian_profile.get('current_location', 'NCR/BLR/Remote')}\n"
        f"Skill Score: {calc_res['skill_fit_score']}%, Experience Score: {calc_res['experience_fit_score']}%, Education Score: {calc_res['education_fit_score']}%\n"
        f"Matched Skills: {matched}\n"
        f"Missing Skills: {missing}\n"
        f"Job Description: {jd_text}\n\n"
        "Provide a concise 3-bullet point recruiter evaluation summary explaining strengths, gaps (including notice period / college pedigree relevance), and why they got this score."
    )
    
    try:
        response = llm.invoke(prompt)
        assessment_text = response.content
    except Exception as e:
        assessment_text = f"Candidate matches {len(matched)} required skills. College: {college_tier}. Notice Period: {notice_days} days."

    return {
        "overall_score": calc_res["overall_score"],
        "recommendation": calc_res["recommendation"],
        "skill_fit_score": calc_res["skill_fit_score"],
        "experience_fit_score": calc_res["experience_fit_score"],
        "education_fit_score": calc_res["education_fit_score"],
        "college_tier": college_tier,
        "notice_period_days": notice_days,
        "assessment_text": assessment_text
    }
