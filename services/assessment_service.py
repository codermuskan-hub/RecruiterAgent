import uuid
import random
from typing import Dict, Any
from database.database import update_candidate_assessment, get_candidate_by_id


def generate_assessment_invite(
    candidate_id: int,
    candidate_name: str,
    candidate_email: str,
    role_title: str = "Software Engineer",
    provider: str = "HackerEarth"
) -> Dict[str, Any]:
    """
    Generates a standardized assessment invite for a candidate via HackerEarth or Mercer | Mettl.
    Persists the assessment status into SQLite.
    """
    token = uuid.uuid4().hex[:12]
    
    if provider.lower() == "mettl":
        platform_name = "Mercer | Mettl"
        test_id = f"METTL-TECH-{token.upper()}"
        invite_url = f"https://tests.mettl.com/v2/authenticateKey/{token}"
    else:
        platform_name = "HackerEarth"
        test_id = f"HE-CODE-{token.upper()}"
        invite_url = f"https://assessment.hackerearth.com/challenges/test/{token}/login/"

    invite_data = {
        "candidate_id": candidate_id,
        "candidate_name": candidate_name,
        "candidate_email": candidate_email,
        "role_title": role_title,
        "provider": platform_name,
        "test_id": test_id,
        "invite_url": invite_url,
        "duration_minutes": 90,
        "status": "Assessment Sent"
    }

    # Update candidate in DB
    if candidate_id:
        update_candidate_assessment(
            candidate_id=candidate_id,
            provider=platform_name,
            score=0.0,
            status="Assessment Sent",
            link=invite_url
        )

    return invite_data


def simulate_assessment_completion(
    candidate_id: int,
    provider: str = "HackerEarth"
) -> Dict[str, Any]:
    """
    Simulates assessment webhook callback or API polling from HackerEarth/Mettl,
    generating realistic coding scores, percentiles, and anti-plagiarism checks.
    """
    candidate = get_candidate_by_id(candidate_id) if candidate_id else None
    cand_name = candidate["name"] if candidate else "Candidate"
    
    # Generate realistic tech score based on candidate prior score if available
    base = float(candidate["score"]) if (candidate and candidate.get("score")) else 75.0
    simulated_score = round(min(100.0, max(45.0, base + random.uniform(-10.0, 12.0))), 1)
    percentile = round(min(99.5, max(50.0, simulated_score + random.uniform(-5.0, 5.0))), 1)
    
    result = {
        "candidate_id": candidate_id,
        "candidate_name": cand_name,
        "provider": provider,
        "score": simulated_score,
        "percentile": percentile,
        "status": "Completed",
        "proctoring_status": "Clean (No Tab Switching Detected)",
        "plagiarism_flag": False,
        "sections": {
            "Data Structures & Algorithms": round(simulated_score * 0.95, 1),
            "Language Proficiency": round(simulated_score * 1.02, 1),
            "Core Problem Solving": round(simulated_score * 0.98, 1)
        }
    }

    if candidate_id:
        link = candidate.get("assessment_link", "") if candidate else ""
        update_candidate_assessment(
            candidate_id=candidate_id,
            provider=provider,
            score=simulated_score,
            status="Completed",
            link=link
        )

    return result
