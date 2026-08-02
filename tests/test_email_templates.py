import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from services.email_templates import (
    generate_interview_invite_email,
    generate_shortlist_email,
    generate_rejection_email
)


def test_email_templates():
    print("--- Testing Interview Invite Email ---")
    invite = generate_interview_invite_email(
        candidate_name="Jane Doe",
        role_title="Senior Python Developer",
        scheduled_time="2026-08-10 10:00 AM",
        meeting_link="https://meet.jit.si/Interview-JaneDoe"
    )
    print("Invite Subject:", invite["subject"])
    print("Invite Body Preview:\n", invite["body"][:200])
    assert "Jane Doe" in invite["body"]
    assert "https://meet.jit.si/Interview-JaneDoe" in invite["body"]

    print("\n--- Testing Shortlist Email ---")
    shortlist = generate_shortlist_email(
        candidate_name="Jane Doe",
        role_title="Senior Python Developer",
        match_score=88.5
    )
    print("Shortlist Subject:", shortlist["subject"])
    assert "88.5" in shortlist["body"]

    print("\n--- Testing Rejection Email ---")
    rejection = generate_rejection_email(
        candidate_name="Bob Smith",
        role_title="Senior Python Developer",
        missing_skills=["Kubernetes", "GraphQL"]
    )
    print("Rejection Subject:", rejection["subject"])
    assert "Kubernetes" in rejection["body"]

    print("\n✅ All Email Template tests passed!")


if __name__ == "__main__":
    test_email_templates()
