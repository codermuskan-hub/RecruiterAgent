import os
import sys
import datetime

# Ensure project root & database dir are accessible
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
db_dir = os.path.join(project_root, "database")

for p in [project_root, db_dir]:
    if p not in sys.path:
        sys.path.append(p)

from database.database import (
    add_interview_slot,
    get_available_slots,
    book_interview_slot,
    get_all_scheduled_interviews
)


def seed_default_slots_if_empty():
    """Populates initial sample interview time slots if none exist."""
    slots = get_available_slots()
    if not slots:
        today = datetime.date.today()
        sample_times = [
            f"{(today + datetime.timedelta(days=1)).strftime('%Y-%m-%d')} 10:00 AM",
            f"{(today + datetime.timedelta(days=1)).strftime('%Y-%m-%d')} 02:00 PM",
            f"{(today + datetime.timedelta(days=2)).strftime('%Y-%m-%d')} 11:00 AM",
            f"{(today + datetime.timedelta(days=2)).strftime('%Y-%m-%d')} 04:00 PM",
        ]
        for slot in sample_times:
            add_interview_slot(slot)


def get_available_time_slots() -> list:
    """Returns all unbooked interview time slots."""
    seed_default_slots_if_empty()
    return get_available_slots()


def schedule_candidate_interview(
    candidate_name: str,
    candidate_email: str = "candidate@example.com",
    role_title: str = "General Role",
    slot_id: int = None
) -> dict:
    """
    Schedules an interview slot for a candidate and generates a meeting link.
    """
    slots = get_available_time_slots()
    if not slots:
        return {"status": "Error", "message": "No available interview slots found."}

    selected_slot = None
    if slot_id:
        selected_slot = next((s for s in slots if s["id"] == slot_id), None)

    if not selected_slot:
        selected_slot = slots[0]

    clean_name = "".join(e for e in candidate_name if e.isalnum())
    meeting_link = f"https://meet.jit.si/Interview-{clean_name}"

    booking = book_interview_slot(
        slot_id=selected_slot["id"],
        candidate_name=candidate_name,
        candidate_email=candidate_email or "candidate@example.com",
        role_title=role_title,
        meeting_link=meeting_link
    )

    if booking:
        return {
            "status": "Success",
            "message": f"Interview scheduled for {candidate_name}!",
            "booking": booking
        }

    return {"status": "Error", "message": "Failed to book selected slot."}


def list_scheduled_interviews() -> list:
    """Returns all booked interview records."""
    return get_all_scheduled_interviews()


def create_new_slot(slot_time_str: str) -> int:
    """Creates a new interviewer slot."""
    return add_interview_slot(slot_time_str)
