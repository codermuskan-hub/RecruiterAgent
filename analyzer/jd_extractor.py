import os
import json
import re
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.tools import tool

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def clean_text(text: str) -> str:
    """Cleans up markdown formatting from LLM JSON responses."""
    if text.startswith("```json"):
        text = text.replace("```json", "").replace("```", "").strip()
    elif text.startswith("```"):
        text = text.replace("```", "").strip()
    return text.strip()


@tool
def extract_jd_requirements(job_description_text: str) -> dict:
    """
    Input: Raw job description text string.
    Output: Dictionary with extracted role_title, required_skills, preferred_skills, min_experience_years, and education_level.
    """
    if not job_description_text or not job_description_text.strip():
        return {
            "role_title": "General Role",
            "required_skills": [],
            "preferred_skills": [],
            "min_experience_years": 0,
            "education_level": "None specified"
        }

    if GROQ_API_KEY:
        try:
            llm = ChatGroq(
                model="llama-3.3-70b-versatile",
                api_key=GROQ_API_KEY,
                temperature=0.0,
                max_tokens=1000,
                model_kwargs={"response_format": {"type": "json_object"}}
            )

            prompt = (
                "Extract structured requirements from this job description into valid JSON with these exact keys:\n"
                "- 'role_title': string (e.g. 'Senior Python Developer')\n"
                "- 'required_skills': list of strings (must-have skills)\n"
                "- 'preferred_skills': list of strings (nice-to-have skills)\n"
                "- 'min_experience_years': integer or float (e.g. 3)\n"
                "- 'education_level': string (e.g. 'Bachelor's' or 'None specified')\n\n"
                f"Job Description:\n{job_description_text}"
            )

            response = llm.invoke(prompt)
            json_str = clean_text(response.content)
            data = json.loads(json_str)

            return {
                "role_title": data.get("role_title", "General Role"),
                "required_skills": data.get("required_skills", []),
                "preferred_skills": data.get("preferred_skills", []),
                "min_experience_years": float(data.get("min_experience_years", 0)),
                "education_level": data.get("education_level", "None specified")
            }
        except Exception:
            pass

    return _fallback_extract_jd(job_description_text)


def _fallback_extract_jd(text: str) -> dict:
    """Rule-based fallback if LLM is unavailable."""
    exp_match = re.search(r"(\d+)\+?\s*(?:years|yrs)", text, re.IGNORECASE)
    min_exp = float(exp_match.group(1)) if exp_match else 0.0

    common_skills = [
        "python", "java", "c++", "javascript", "typescript", "react", "node",
        "sql", "postgresql", "mongodb", "docker", "kubernetes", "aws", "gcp",
        "azure", "git", "machine learning", "deep learning", "nlp", "fastapi",
        "django", "flask", "pandas", "numpy", "html", "css", "rest api"
    ]

    text_lower = text.lower()
    found_skills = [skill.title() for skill in common_skills if skill in text_lower]

    return {
        "role_title": "Position",
        "required_skills": found_skills,
        "preferred_skills": [],
        "min_experience_years": min_exp,
        "education_level": "None specified"
    }
