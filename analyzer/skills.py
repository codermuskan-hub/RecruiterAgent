from langchain_core.tools import tool

@tool
def extract_skills(resume_json):
    """
    Input: JSON/dict from json_maker
    Output: list of skills, e.g. ["Python", "Docker", "SQL"]
    """
    skills = resume_json.get("skills", [])
    return skills