from langchain_core.tools import tool
from jd_extractor import extract_jd_requirements


@tool
def match_skills(job_description, candidate_skills):
    """
    Input: job description string (or structured JD dict), candidate skills list
    Output: matched skills, missing skills, matched preferred skills, and match score
    """
    if isinstance(job_description, str):
        # Extract JD requirements
        jd_func = extract_jd_requirements.func if hasattr(extract_jd_requirements, "func") else extract_jd_requirements
        jd_reqs = jd_func(job_description)
    elif isinstance(job_description, dict):
        jd_reqs = job_description
    else:
        jd_reqs = {}

    required_skills = jd_reqs.get("required_skills", [])
    preferred_skills = jd_reqs.get("preferred_skills", [])

    candidate_skills_lower = {s.lower(): s for s in candidate_skills}

    # If extracted JD has required skills, match against candidate skills
    if required_skills:
        matched = []
        missing = []
        for skill in required_skills:
            if skill.lower() in candidate_skills_lower or any(skill.lower() in cs for cs in candidate_skills_lower):
                matched.append(skill)
            else:
                missing.append(skill)

        matched_preferred = []
        for skill in preferred_skills:
            if skill.lower() in candidate_skills_lower or any(skill.lower() in cs for cs in candidate_skills_lower):
                matched_preferred.append(skill)

        req_score = (len(matched) / len(required_skills) * 100) if required_skills else 100.0
        pref_score = (len(matched_preferred) / len(preferred_skills) * 100) if preferred_skills else 100.0

        if preferred_skills:
            score = (req_score * 0.8) + (pref_score * 0.2)
        else:
            score = req_score

        return {
            "matched_skills": matched,
            "missing_skills": missing,
            "matched_preferred_skills": matched_preferred,
            "score": round(score, 2)
        }

    # Fallback to simple skill matching if no required skills extracted
    jd_lower = str(job_description).lower()
    matched = []
    missing = []

    for skill in candidate_skills:
        if skill.lower() in jd_lower:
            matched.append(skill)
        else:
            missing.append(skill)

    score = (len(matched) / len(candidate_skills) * 100) if candidate_skills else 0.0

    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "matched_preferred_skills": [],
        "score": round(score, 2)
    }
