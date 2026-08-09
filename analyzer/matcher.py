import re
from langchain_core.tools import tool
try:
    from jd_extractor import extract_jd_requirements
except ImportError:
    from analyzer.jd_extractor import extract_jd_requirements


# Tech-specific skill taxonomy and ecosystem mapping
TECH_TAXONOMY = {
    "python": ["fastapi", "django", "flask", "pytorch", "pandas", "numpy", "scikit-learn", "tensorflow"],
    "java": ["spring", "spring boot", "hibernate", "microservices", "maven", "jvm", "jpa"],
    "javascript": ["typescript", "react", "next.js", "nextjs", "node.js", "nodejs", "express", "vue", "angular", "redux"],
    "react": ["next.js", "nextjs", "react.js", "redux", "react native"],
    "node.js": ["express", "nest.js", "fastify", "nodejs", "javascript", "typescript"],
    "c++": ["c", "stl", "cpp", "system programming", "embedded"],
    "docker": ["kubernetes", "containerization", "ci/cd", "devops"],
    "kubernetes": ["docker", "helm", "k8s", "cloud native", "devops"],
    "aws": ["ec2", "s3", "lambda", "cloudformation", "iam", "cloud"],
    "sql": ["postgresql", "postgres", "mysql", "sqlite", "oracle", "rdbms"],
    "nosql": ["mongodb", "redis", "cassandra", "dynamodb", "firebase", "supabase"],
    "machine learning": ["deep learning", "nlp", "computer vision", "tensorflow", "pytorch", "scikit-learn"],
    "computer vision": ["opencv", "mediapipe", "yolo", "image processing", "facial recognition"],
    "generative ai": ["llm", "langchain", "prompt engineering", "rag", "groq", "openai", "gemini"]
}


def check_skill_match(required_skill: str, candidate_skills: list) -> bool:
    """
    Checks if a required skill is present in candidate skills either directly,
    as a substring, or through the tech ecosystem taxonomy.
    """
    req_lower = required_skill.lower().strip()
    cand_lower = [s.lower().strip() for s in candidate_skills]

    # 1. Exact or substring match
    if req_lower in cand_lower:
        return True
    if any(req_lower in cs or cs in req_lower for cs in cand_lower):
        return True

    # 2. Tech Taxonomy / Ecosystem Alias Check
    # If req_skill is in taxonomy, check if any of its ecosystem tools are in candidate skills
    if req_lower in TECH_TAXONOMY:
        for alias in TECH_TAXONOMY[req_lower]:
            if any(alias in cs for cs in cand_lower):
                return True

    # Check reverse: if candidate has a parent tech that implies this skill
    for parent, children in TECH_TAXONOMY.items():
        if req_lower in children:
            if any(parent == cs or parent in cs for cs in cand_lower):
                return True

    return False


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

    # If extracted JD has required skills, match against candidate skills using tech taxonomy
    if required_skills:
        matched = []
        missing = []
        for skill in required_skills:
            if check_skill_match(skill, candidate_skills):
                matched.append(skill)
            else:
                missing.append(skill)

        matched_preferred = []
        for skill in preferred_skills:
            if check_skill_match(skill, candidate_skills):
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
