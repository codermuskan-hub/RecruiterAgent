import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
for folder in [project_root, "services"]:
    p = os.path.join(project_root, folder) if folder != project_root else project_root
    if p not in sys.path:
        sys.path.append(p)

from services.validator import validate_job_description, validate_candidate_data
from services.export_service import export_candidates_to_csv, export_candidates_to_json, compute_hiring_analytics
from services.assessment_service import generate_assessment_invite, simulate_assessment_completion


def test_validation_and_exports():
    print("--- 1. Testing Job Description Validation ---")
    ok, msg = validate_job_description("")
    assert ok is False
    print("Empty JD rejected correctly.")

    ok, msg = validate_job_description("Short text")
    assert ok is False
    print("Short JD rejected correctly.")

    ok, msg = validate_job_description("We are looking for a Senior Python Developer with 4 years experience in FastAPI, Docker, and PostgreSQL.")
    assert ok is True
    print("Valid technical JD accepted correctly.")

    print("\n--- 2. Testing Candidate Data Validation ---")
    valid_cand = {
        "name": "Arjun Mehta",
        "email": "arjun.mehta@example.com",
        "phone": "+91-9876543210",
        "notice_period_days": 30,
        "current_ctc_lpa": 12.0,
        "expected_ctc_lpa": 18.0
    }
    ok_cand, errs = validate_candidate_data(valid_cand)
    assert ok_cand is True
    print("Valid candidate data verified.")

    invalid_cand = {
        "name": "",
        "email": "not-an-email",
        "phone": "123",
        "notice_period_days": 500,
        "current_ctc_lpa": -5
    }
    ok_inv, errs_inv = validate_candidate_data(invalid_cand)
    assert ok_inv is False
    assert len(errs_inv) >= 4
    print(f"Invalid candidate data caught {len(errs_inv)} errors correctly.")

    print("\n--- 3. Testing Candidate Exports & Analytics ---")
    mock_candidates = [
        {
            "id": 1,
            "name": "Arjun Mehta",
            "email": "arjun@example.com",
            "phone": "+91-9876543210",
            "stage": "Shortlisted",
            "score": 88.5,
            "college_tier": "Tier-1",
            "degree": "B.Tech",
            "notice_period_days": 15,
            "current_ctc_lpa": 14.0,
            "expected_ctc_lpa": 20.0,
            "current_location": "Bengaluru",
            "assessment_status": "Completed",
            "assessment_score": 92.0
        },
        {
            "id": 2,
            "name": "Kavita Rao",
            "email": "kavita@example.com",
            "phone": "+91-9123456780",
            "stage": "Applied",
            "score": 64.0,
            "college_tier": "Tier-2",
            "degree": "B.Tech",
            "notice_period_days": 60,
            "current_ctc_lpa": 8.0,
            "expected_ctc_lpa": 12.0,
            "current_location": "Delhi-NCR",
            "assessment_status": "Not Sent",
            "assessment_score": 0.0
        }
    ]

    csv_out = export_candidates_to_csv(mock_candidates)
    assert "Candidate ID,Name,Email" in csv_out
    assert "Arjun Mehta" in csv_out
    print("CSV export generated successfully.")

    json_out = export_candidates_to_json(mock_candidates)
    assert "Arjun Mehta" in json_out
    print("JSON export generated successfully.")

    analytics = compute_hiring_analytics(mock_candidates)
    assert analytics["total_candidates"] == 2
    assert analytics["avg_score"] == 76.2
    assert analytics["avg_notice_period"] == 37.5
    print("Analytics KPI computation verified.")

    print("\n--- 4. Testing Error Messages for Assessment Service ---")
    ok, inv, err = generate_assessment_invite(None, "", "invalid-email")
    assert ok is False
    assert "Candidate name is missing" in err
    print(f"Assessment validation error verified: '{err}'")

    ok_sim, sim, err_sim = simulate_assessment_completion(999999, "HackerEarth")
    assert ok_sim is False
    assert "not found in the pipeline database" in err_sim
    print(f"Assessment simulation error verified: '{err_sim}'")

    print("\n🎉 ALL VALIDATION, EXPORT, AND ASSESSMENT TESTS PASSED!")


if __name__ == "__main__":
    test_validation_and_exports()
