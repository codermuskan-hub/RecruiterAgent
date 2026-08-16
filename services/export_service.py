import io
import json
import pandas as pd
from typing import List, Dict, Any


def export_candidates_to_csv(candidates: List[Dict[str, Any]]) -> str:
    """
    Exports candidates data into a clean CSV string for recruitment team sharing.
    """
    if not candidates:
        return ""

    flattened = []
    for c in candidates:
        flattened.append({
            "Candidate ID": c.get("id", ""),
            "Name": c.get("name", ""),
            "Email": c.get("email", ""),
            "Phone": c.get("phone", ""),
            "Pipeline Stage": c.get("stage", "Applied"),
            "Overall Score": c.get("score", 0.0),
            "College Tier": c.get("college_tier", "Tier-3"),
            "Degree": c.get("degree", "B.Tech"),
            "Notice Period (Days)": c.get("notice_period_days", 30),
            "Current CTC (LPA)": c.get("current_ctc_lpa", 0.0),
            "Expected CTC (LPA)": c.get("expected_ctc_lpa", 0.0),
            "Current Location": c.get("current_location", ""),
            "Assessment Provider": c.get("assessment_provider", "None"),
            "Assessment Score": c.get("assessment_score", 0.0),
            "Assessment Status": c.get("assessment_status", "Not Sent")
        })

    df = pd.DataFrame(flattened)
    return df.to_csv(index=False)


def export_candidates_to_json(candidates: List[Dict[str, Any]]) -> str:
    """
    Exports full candidate records including nested skills, experience, and notes to JSON.
    """
    return json.dumps(candidates, indent=2, default=str)


def compute_hiring_analytics(candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Computes hiring pipeline analytics and statistical KPIs.
    """
    if not candidates:
        return {
            "total_candidates": 0,
            "stage_distribution": {},
            "avg_score": 0.0,
            "tier_distribution": {},
            "avg_notice_period": 0.0,
            "avg_expected_ctc": 0.0,
            "assessment_completion_rate": "0%"
        }

    total = len(candidates)
    scores = [float(c.get("score", 0.0)) for c in candidates if c.get("score") is not None]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0

    notices = [int(c.get("notice_period_days", 30)) for c in candidates if c.get("notice_period_days") is not None]
    avg_notice = round(sum(notices) / len(notices), 1) if notices else 30.0

    ctcs = [float(c.get("expected_ctc_lpa", 0.0)) for c in candidates if c.get("expected_ctc_lpa") and float(c.get("expected_ctc_lpa", 0.0)) > 0]
    avg_ctc = round(sum(ctcs) / len(ctcs), 1) if ctcs else 0.0

    stage_counts = {}
    tier_counts = {}
    assessments_sent = 0
    assessments_completed = 0

    for c in candidates:
        stg = c.get("stage", "Applied")
        stage_counts[stg] = stage_counts.get(stg, 0) + 1

        tier = c.get("college_tier", "Tier-3")
        tier_counts[tier] = tier_counts.get(tier, 0) + 1

        a_status = c.get("assessment_status", "Not Sent")
        if a_status in ["Assessment Sent", "Completed"]:
            assessments_sent += 1
        if a_status == "Completed":
            assessments_completed += 1

    completion_rate = f"{round((assessments_completed / max(1, assessments_sent)) * 100, 1)}%"

    return {
        "total_candidates": total,
        "stage_distribution": stage_counts,
        "avg_score": avg_score,
        "tier_distribution": tier_counts,
        "avg_notice_period": avg_notice,
        "avg_expected_ctc": avg_ctc,
        "assessment_completion_rate": completion_rate,
        "assessments_sent": assessments_sent,
        "assessments_completed": assessments_completed
    }
