import uuid
import random
from typing import Dict, Any, Tuple
from database.database import update_candidate_assessment, get_candidate_by_id


def generate_assessment_invite(
    candidate_id: int,
    candidate_name: str,
    candidate_email: str,
    role_title: str = "Software Engineer",
    provider: str = "HackerEarth"
) -> Tuple[bool, Dict[str, Any], str]:
    """
    Generates a standardized assessment invite for a candidate via HackerEarth or Mercer | Mettl.
    Validates candidate details and returns (success, invite_data, error_message).
    """
    # Validation
    if not candidate_name or candidate_name.strip() in ["", "Unknown"]:
        return False, {}, "Cannot dispatch assessment: Candidate name is missing or invalid."

    if not candidate_email or "@" not in candidate_email:
        return False, {}, f"Cannot dispatch assessment: '{candidate_email}' is not a valid email address for delivery."

    token = uuid.uuid4().hex[:12]
    
    if provider.lower() in ["mettl", "mercer | mettl"]:
        platform_name = "Mercer | Mettl"
        test_id = f"METTL-TECH-{token.upper()}"
        invite_url = f"https://tests.mettl.com/v2/authenticateKey/{token}"
    elif provider.lower() == "hackerearth":
        platform_name = "HackerEarth"
        test_id = f"HE-CODE-{token.upper()}"
        invite_url = f"https://assessment.hackerearth.com/challenges/test/{token}/login/"
    else:
        return False, {}, f"Unsupported assessment provider: '{provider}'. Supported providers are HackerEarth and Mercer | Mettl."

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
        try:
            update_candidate_assessment(
                candidate_id=candidate_id,
                provider=platform_name,
                score=0.0,
                status="Assessment Sent",
                link=invite_url
            )
        except Exception as e:
            return False, invite_data, f"Assessment generated but database synchronization failed: {str(e)}"

    return True, invite_data, ""


def simulate_assessment_completion(
    candidate_id: int,
    provider: str = "HackerEarth"
) -> Tuple[bool, Dict[str, Any], str]:
    """
    Simulates assessment webhook callback or API polling from HackerEarth/Mettl,
    generating realistic coding scores, percentiles, and anti-plagiarism checks.
    Returns (success, result_dict, error_message).
    """
    if not candidate_id:
        return False, {}, "Missing candidate ID. Cannot fetch assessment result without a candidate reference."

    candidate = get_candidate_by_id(candidate_id)
    if not candidate:
        return False, {}, f"Candidate with ID #{candidate_id} was not found in the pipeline database."

    if candidate.get("assessment_status") == "Not Sent":
        return False, {}, f"Cannot evaluate test for '{candidate['name']}': An assessment invite has not been dispatched yet."

    cand_name = candidate["name"]
    base = float(candidate["score"]) if candidate.get("score") else 75.0
    simulated_score = round(min(100.0, max(45.0, base + random.uniform(-10.0, 12.0))), 1)
    percentile = round(min(99.5, max(50.0, simulated_score + random.uniform(-5.0, 5.0))), 1)
    
    result = {
        "candidate_id": candidate_id,
        "candidate_name": cand_name,
        "provider": provider,
        "score": simulated_score,
        "percentile": percentile,
        "status": "Completed",
        "proctoring_status": "Clean (No Tab Switching / Integrity Verified)",
        "plagiarism_flag": False,
        "sections": {
            "Data Structures & Algorithms": round(simulated_score * 0.95, 1),
            "Language Proficiency": round(simulated_score * 1.02, 1),
            "Core Problem Solving": round(simulated_score * 0.98, 1)
        }
    }

    try:
        link = candidate.get("assessment_link", "") or ""
        update_candidate_assessment(
            candidate_id=candidate_id,
            provider=provider,
            score=simulated_score,
            status="Completed",
            link=link
        )
    except Exception as e:
        return False, result, f"Assessment calculated successfully but database save failed: {str(e)}"

    return True, result, ""
