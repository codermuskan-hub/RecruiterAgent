import json
from langchain_core.tools import tool

@tool
def calculate_weighted_score(
    skill_fit_score: float,
    experience_fit_score: float,
    education_fit_score: float
) -> str:
    """
    Computes a weighted overall candidate score (0-100) based on three dimensions:
    - Skill Fit (Weight: 50%)
    - Experience & Role Fit (Weight: 30%)
    - Education & Certifications (Weight: 20%)
    
    Returns a JSON string containing individual dimension scores and the overall weighted score.
    """
    # Ensure inputs are capped between 0 and 100
    s_score = max(0.0, min(100.0, float(skill_fit_score)))
    e_score = max(0.0, min(100.0, float(experience_fit_score)))
    edu_score = max(0.0, min(100.0, float(education_fit_score)))
    
    # Weighted multi-dimensional calculation
    overall = (0.50 * s_score) + (0.30 * e_score) + (0.20 * edu_score)
    overall_rounded = round(overall, 2)
    
    if overall_rounded >= 85:
        recommendation = "Strong Hire"
    elif overall_rounded >= 70:
        recommendation = "Shortlist"
    elif overall_rounded >= 50:
        recommendation = "Hold / Secondary Review"
    else:
        recommendation = "Reject / Low Match"
        
    result = {
        "skill_fit_score": round(s_score, 2),
        "experience_fit_score": round(e_score, 2),
        "education_fit_score": round(edu_score, 2),
        "overall_score": overall_rounded,
        "recommendation": recommendation
    }
    return json.dumps(result)
