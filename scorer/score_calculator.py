import json
from langchain_core.tools import tool

@tool
def calculate_weighted_score(
    skill_fit_score: float,
    experience_fit_score: float,
    education_fit_score: float,
    college_tier: str = "Tier-3",
    notice_period_days: int = 30
) -> str:
    """
    Computes a weighted overall candidate score (0-100) based on three dimensions:
    - Skill Fit (Weight: 50%)
    - Experience & Role Fit (Weight: 30%)
    - Education & Certifications (Weight: 20%) with Indian college tier recognition (Tier-1/2/3)
    and notice period adjustments.
    
    Returns a JSON string containing individual dimension scores and the overall weighted score.
    """
    # Ensure inputs are capped between 0 and 100
    s_score = max(0.0, min(100.0, float(skill_fit_score)))
    e_score = max(0.0, min(100.0, float(experience_fit_score)))
    edu_score = max(0.0, min(100.0, float(education_fit_score)))

    # Indian College Tier adjustment on education score
    if college_tier == "Tier-1":
        edu_score = max(edu_score, 95.0)
    elif college_tier == "Tier-2":
        edu_score = max(edu_score, 85.0)

    # Weighted multi-dimensional calculation
    overall = (0.50 * s_score) + (0.30 * e_score) + (0.20 * edu_score)

    # Notice period bonus/adjustment (Indian tech market advantage)
    if int(notice_period_days) <= 15:
        overall = min(100.0, overall + 2.0)  # Immediate / 15-day joiner advantage
    elif int(notice_period_days) >= 90:
        overall = max(0.0, overall - 2.0)    # 90-day notice risk adjustment

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
        "college_tier": college_tier,
        "notice_period_days": notice_period_days,
        "recommendation": recommendation
    }
    return json.dumps(result)
