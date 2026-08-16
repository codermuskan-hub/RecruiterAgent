import os
import sys

# Add project root and subdirectories to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
for folder in [project_root, "analyzer", "scorer", "services", "database"]:
    p = os.path.join(project_root, folder) if folder != project_root else project_root
    if p not in sys.path:
        sys.path.append(p)

from analyzer.indian_tech_recognizer import (
    classify_indian_college_tier,
    normalize_indian_degree,
    parse_notice_period,
    parse_ctc_lpa,
    normalize_indian_location
)
from analyzer.matcher import check_skill_match, match_skills
from database.database import (
    init_db,
    save_candidate_pipeline_record,
    get_all_candidates,
    update_candidate_stage
)
from services.assessment_service import (
    generate_assessment_invite,
    simulate_assessment_completion
)


def test_indian_recruitment_specialist():
    print("--- 1. Testing Indian College Tier Recognition ---")
    tier1, name1 = classify_indian_college_tier("Indian Institute of Technology, Delhi")
    tier2, name2 = classify_indian_college_tier("Vellore Institute of Technology (VIT)")
    tier3, name3 = classify_indian_college_tier("Global Institute of Technology & Management")

    print(f"IIT Delhi: {tier1}")
    print(f"VIT: {tier2}")
    print(f"GITM: {tier3}")

    assert tier1 == "Tier-1"
    assert tier2 == "Tier-2"
    assert tier3 == "Tier-3"

    print("\n--- 2. Testing Degree Normalization ---")
    assert normalize_indian_degree("Bachelor of Technology in CS") == "B.Tech"
    assert normalize_indian_degree("Master of Computer Applications") == "MCA"
    print("Degree normalization passed!")

    print("\n--- 3. Testing Notice Period and CTC Parsing ---")
    assert parse_notice_period("Currently serving notice, available immediately") == 0
    assert parse_notice_period("Notice Period: 15 days") == 15
    assert parse_notice_period("3 months notice period required") == 90
    print("Notice period parsing passed!")

    curr_lpa, exp_lpa = parse_ctc_lpa("Current CTC: 12 LPA, Expected: 18.5 LPA")
    assert curr_lpa == 12.0
    assert exp_lpa == 18.5
    print(f"CTC Parsing passed: Current={curr_lpa} LPA, Expected={exp_lpa} LPA")

    print("\n--- 4. Testing Location Normalization ---")
    assert normalize_indian_location("Gurugram, Haryana") == "Delhi-NCR"
    assert normalize_indian_location("Whitefield, Bangalore") == "Bengaluru"
    assert normalize_indian_location("Hitec City, Hyderabad") == "Hyderabad"
    print("Location normalization passed!")

    print("\n--- 5. Testing Tech-Specific Taxonomy Skill Matching ---")
    # Java requirement should match candidate with Spring Boot
    assert check_skill_match("Java", ["Spring Boot", "MySQL"]) is True
    # React requirement should match candidate with Next.js
    assert check_skill_match("React", ["Next.js", "TypeScript"]) is True
    # Python requirement should match candidate with FastAPI
    assert check_skill_match("Python", ["FastAPI", "Docker"]) is True
    print("Tech-specific taxonomy skill matching passed!")

    print("\n--- 6. Testing Pipeline DB Persistence ---")
    init_db()
    cid = save_candidate_pipeline_record({
        "name": "Pooja Verma",
        "email": "pooja.verma@test.com",
        "phone": "+91-9988776655",
        "skills": ["Java", "Spring Boot", "Kafka"],
        "score": 89.0,
        "stage": "Shortlisted",
        "notice_period_days": 15,
        "current_ctc_lpa": 14.0,
        "expected_ctc_lpa": 20.0,
        "college_tier": "Tier-1",
        "degree": "B.Tech"
    })
    assert cid > 0
    print(f"Pipeline candidate saved with ID: {cid}")

    print("\n--- 7. Testing HackerEarth Assessment API Flow ---")
    ok, invite, err = generate_assessment_invite(cid, "Pooja Verma", "pooja.verma@test.com", "Senior Java Engineer", "HackerEarth")
    assert ok is True
    assert "invite_url" in invite
    assert invite["status"] == "Assessment Sent"
    print(f"HackerEarth invite generated: {invite['invite_url']}")

    ok_sim, sim_res, err_sim = simulate_assessment_completion(cid, "HackerEarth")
    assert ok_sim is True
    assert sim_res["status"] == "Completed"
    assert sim_res["score"] > 0
    print(f"Assessment completed: Score={sim_res['score']}, Percentile={sim_res['percentile']}")


    stage_updated = update_candidate_stage(cid, "Interview Scheduled")
    assert stage_updated is True
    print("Stage updated to 'Interview Scheduled' successfully!")

    print("\n🎉 ALL INDIAN TECH RECRUITMENT SPECIALIST TESTS PASSED!")


if __name__ == "__main__":
    test_indian_recruitment_specialist()
