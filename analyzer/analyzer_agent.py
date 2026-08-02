import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()

# Ensure analyzer folder and project root are in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
for p in [current_dir, project_root]:
    if p not in sys.path:
        sys.path.append(p)

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from parser.docx_parser import parse_docx
from parser.pdf_parser import parse_pdf
from json_maker import make_json
from matcher import match_skills
from skills import extract_skills
from jd_extractor import extract_jd_requirements

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=GROQ_API_KEY,
    temperature=0.0,
    max_tokens=2000
)

analyzer_tools = [make_json, parse_docx, parse_pdf, match_skills, extract_skills, extract_jd_requirements]

# Support both LangChain legacy create_tool_calling_agent and new create_agent
try:
    from langchain.agents import create_tool_calling_agent, AgentExecutor
    analyzer_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert Resume Analyzer Agent. Use your tools to parse the resume file, convert it to structured JSON, extract candidate skills, and compare them to the Job Description to create a skill match report."),
        ("user", "Here is the resume file path: {file_path}. Here is the JD: {jd_text}. Please analyze the resume and generate the skill match report."),
        ("placeholder", "{agent_scratchpad}"),
    ])
    analyzer_agent = create_tool_calling_agent(llm, analyzer_tools, analyzer_prompt)
    analyzer_executor = AgentExecutor(agent=analyzer_agent, tools=analyzer_tools, verbose=True)
except (ImportError, AttributeError):
    from langchain.agents import create_agent
    analyzer_executor = create_agent(
        model=llm,
        tools=analyzer_tools,
        system_prompt="You are an expert Resume Analyzer Agent. Use your tools to parse the resume file, convert it into structured JSON, extract candidate skills, and compare them to the Job Description to create a skill match report."
    )


def run_analyzer_pipeline(file_path: str, jd_text: str):
    """
    Executes resume parsing, JSON extraction, skill extraction, JD requirement extraction, and matching.
    Returns:
        dict: {
            'resume_json': dict,
            'skills': list,
            'match_report': dict,
            'jd_requirements': dict,
            'parsed_text': str
        }
    """
    # 1. Parse document based on extension
    if file_path.lower().endswith(".docx"):
        text = parse_docx.invoke({"file_path": file_path}) if hasattr(parse_docx, "invoke") else parse_docx(file_path)
    else:
        text = parse_pdf.invoke({"file_path": file_path}) if hasattr(parse_pdf, "invoke") else parse_pdf(file_path)

    # 2. Make JSON
    resume_json = make_json.invoke({"markdown": text}) if hasattr(make_json, "invoke") else make_json(text)

    # 3. Extract Skills
    candidate_skills = extract_skills.invoke({"resume_json": resume_json}) if hasattr(extract_skills, "invoke") else extract_skills(resume_json)

    # 4. Extract JD Requirements
    jd_reqs = {}
    if jd_text and jd_text.strip():
        jd_func = extract_jd_requirements.func if hasattr(extract_jd_requirements, "func") else extract_jd_requirements
        jd_reqs = jd_func(jd_text)

    # 5. Match with JD
    if jd_text and jd_text.strip():
        match_report = match_skills.invoke({"job_description": jd_reqs if jd_reqs else jd_text, "candidate_skills": candidate_skills}) if hasattr(match_skills, "invoke") else match_skills(jd_reqs if jd_reqs else jd_text, candidate_skills)
    else:
        match_report = {"matched_skills": [], "missing_skills": candidate_skills, "score": 0}

    return {
        "resume_json": resume_json,
        "skills": candidate_skills,
        "match_report": match_report,
        "jd_requirements": jd_reqs,
        "parsed_text": text
    }