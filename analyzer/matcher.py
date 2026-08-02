from langchain_core.tools import tool

@tool
def match_skills(job_description, candidate_skills):
    """
    Input: job description string, candidate skills list
    Output: matched skills, missing skills, and a simple score
    """
    jd_lower = job_description.lower()

    matched = []
    missing = []

    for skill in candidate_skills:
        if skill.lower() in jd_lower:
            matched.append(skill)
        else:
            missing.append(skill)

    if candidate_skills:
        score = len(matched) / len(candidate_skills) * 100
    else:
        score = 0

    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "score": score
    }

