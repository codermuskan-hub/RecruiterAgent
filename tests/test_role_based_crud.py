import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
for folder in [project_root, "database", "services"]:
    p = os.path.join(project_root, folder) if folder != project_root else project_root
    if p not in sys.path:
        sys.path.append(p)

from database.database import (
    init_db,
    get_all_users,
    get_user_by_role,
    create_job,
    get_all_jobs,
    get_job_by_id,
    update_job_status,
    save_candidate_pipeline_record,
    get_all_candidates,
    update_candidate_stage,
    update_candidate_manager_decision,
    archive_candidate,
    delete_candidate,
    submit_interview_feedback,
    get_interview_feedback_for_candidate
)


def test_role_based_crud_suite():
    init_db()
    print("--- 1. Testing User Directory & Role-Based Access ---")
    users = get_all_users()
    assert len(users) >= 4
    roles = {u["role"] for u in users}
    assert "Recruiter" in roles
    assert "Hiring Manager" in roles
    assert "Technical Interviewer" in roles
    assert "Admin" in roles
    print(f"Users found ({len(users)}): {[u['username'] for u in users]}")

    recruiter = get_user_by_role("Recruiter")
    assert recruiter is not None
    print(f"Verified Recruiter Profile: {recruiter['full_name']} ({recruiter['department']})")

    print("\n--- 2. Testing Job Requisitions CRUD (Hiring Manager) ---")
    job_id = create_job({
        "title": "Lead Cloud & DevOps Architect",
        "department": "Infrastructure",
        "description": "Lead Kubernetes, Terraform, and AWS cloud migrations.",
        "required_skills": "Kubernetes, Docker, AWS, Terraform, CI/CD",
        "min_experience": 6.0,
        "budget_max_lpa": 35.0,
        "location": "Bengaluru / Remote",
        "status": "Open",
        "created_by": "Vikram Malhotra"
    })
    assert job_id > 0
    job = get_job_by_id(job_id)
    assert job["title"] == "Lead Cloud & DevOps Architect"
    assert job["budget_max_lpa"] == 35.0
    print(f"Created Job #{job_id}: {job['title']} (Budget: ₹{job['budget_max_lpa']} LPA)")

    update_job_status(job_id, "Closed")
    job_updated = get_job_by_id(job_id)
    assert job_updated["status"] == "Closed"
    print(f"Updated Job #{job_id} status to 'Closed'.")

    print("\n--- 3. Testing Candidate Ingestion linked to Job (Recruiter) ---")
    cand_id = save_candidate_pipeline_record({
        "job_id": job_id,
        "name": "Sameer Joshi",
        "email": "sameer.joshi@testcloud.com",
        "phone": "+91-9988112233",
        "skills": ["Kubernetes", "AWS", "Terraform", "Docker"],
        "score": 91.5,
        "stage": "Shortlisted",
        "notice_period_days": 15,
        "current_ctc_lpa": 22.0,
        "expected_ctc_lpa": 30.0,
        "college_tier": "Tier-1",
        "degree": "B.Tech Computer Science"
    })
    assert cand_id > 0
    print(f"Candidate #{cand_id} linked to Job #{job_id} saved.")

    cands_for_job = get_all_candidates(job_id_filter=job_id)
    assert any(c["id"] == cand_id for c in cands_for_job)
    print(f"Verified candidate #{cand_id} query by job_id.")

    print("\n--- 4. Testing Technical Interview Scorecard (Staff Role) ---")
    fb_id = submit_interview_feedback({
        "candidate_id": cand_id,
        "interviewer_name": "Rahul Verma",
        "technical_rating": 5,
        "system_design_rating": 5,
        "cultural_fit_rating": 4,
        "overall_recommendation": "Strong Yes",
        "feedback_notes": "Exceptional knowledge of Kubernetes container networking and zero-downtime blue/green deployments."
    })
    assert fb_id > 0
    feedback_list = get_interview_feedback_for_candidate(cand_id)
    assert len(feedback_list) >= 1
    assert feedback_list[0]["overall_recommendation"] == "Strong Yes"
    print(f"Submitted Interview Feedback #{fb_id} with recommendation 'Strong Yes'.")

    print("\n--- 5. Testing Manager Offer Decision & Approval (Hiring Manager) ---")
    decision_ok = update_candidate_manager_decision(
        candidate_id=cand_id,
        decision="Approved for Offer",
        notes="High assessment score and stellar feedback from lead architect. Extend ₹28 LPA offer."
    )
    assert decision_ok is True
    updated_cand = [c for c in get_all_candidates(include_archived=True) if c["id"] == cand_id][0]
    assert updated_cand["stage"] == "Offer Extended"
    assert updated_cand["offer_status"] == "Approved"
    print(f"Candidate #{cand_id} successfully moved to 'Offer Extended' with Offer Approved!")

    print("\n--- 6. Testing Talent Pool Archival & Hard Deletion (CRUD/Compliance) ---")
    # Soft archive
    archive_ok = archive_candidate(cand_id, True)
    assert archive_ok is True
    active_cands = get_all_candidates(include_archived=False)
    assert not any(c["id"] == cand_id for c in active_cands)
    archived_cands = get_all_candidates(include_archived=True)
    assert any(c["id"] == cand_id for c in archived_cands)
    print("Candidate soft-archival (talent pool preservation) verified.")

    # Permanent hard delete
    del_ok = delete_candidate(cand_id)
    assert del_ok is True
    all_cands_after_del = get_all_candidates(include_archived=True)
    assert not any(c["id"] == cand_id for c in all_cands_after_del)
    print("Candidate permanent GDPR purge verified.")

    print("\n🎉 ALL ROLE-BASED ACCESS AND CRUD DATABASE TESTS PASSED!")


if __name__ == "__main__":
    test_role_based_crud_suite()
