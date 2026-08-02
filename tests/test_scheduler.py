import os
import sys

# Ensure root directory is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from services.scheduler import (
    get_available_time_slots,
    schedule_candidate_interview,
    list_scheduled_interviews,
    create_new_slot
)


def test_interview_scheduler():
    print("--- Testing Slot Creation ---")
    new_slot_id = create_new_slot("2026-08-10 03:00 PM")
    print(f"Created Slot ID: {new_slot_id}")
    assert new_slot_id > 0

    print("\n--- Testing Available Slots ---")
    slots = get_available_time_slots()
    print("Available Slots:", len(slots))
    assert len(slots) > 0

    print("\n--- Testing Candidate Interview Scheduling ---")
    res = schedule_candidate_interview(
        candidate_name="Alice Smith",
        candidate_email="alice@example.com",
        role_title="Python Developer",
        slot_id=new_slot_id
    )
    print("Schedule Result:", res)
    assert res["status"] == "Success"
    assert "booking" in res
    assert res["booking"]["candidate_name"] == "Alice Smith"

    print("\n--- Testing Scheduled Interviews Listing ---")
    scheduled = list_scheduled_interviews()
    print(f"Total Scheduled Interviews: {len(scheduled)}")
    assert len(scheduled) > 0

    print("\n✅ All Interview Scheduler tests passed!")


if __name__ == "__main__":
    test_interview_scheduler()
