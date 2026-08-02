def generate_interview_invite_email(
    candidate_name: str,
    role_title: str,
    scheduled_time: str,
    meeting_link: str,
    company_name: str = "RecruiterAgent Team"
) -> dict:
    """Generates a professional interview invitation email."""
    subject = f"Interview Invitation: {role_title} at {company_name}"
    body = f"""Dear {candidate_name},

Thank you for applying for the {role_title} position at {company_name}. We were very impressed with your background and qualifications!

We would like to invite you for an interview to discuss your experience further.

📅 Interview Date & Time: {scheduled_time}
🔗 Video Meeting Link: {meeting_link}

Please let us know if you need to reschedule or have any questions prior to our discussion.

Best regards,
{company_name} Recruiting Team
"""
    return {"subject": subject, "body": body}


def generate_shortlist_email(
    candidate_name: str,
    role_title: str,
    match_score: float,
    company_name: str = "RecruiterAgent Team"
) -> dict:
    """Generates a shortlist notification email for top candidates."""
    subject = f"Application Update: {role_title} Position at {company_name}"
    body = f"""Dear {candidate_name},

Great news! We have reviewed your profile for the {role_title} position at {company_name}.

Your qualifications closely match our requirements (Overall Fit Score: {match_score}/100), and we have shortlisted your application for the next round of evaluation.

Our recruitment team will be reaching out shortly with details on the upcoming interview steps.

Best regards,
{company_name} Recruiting Team
"""
    return {"subject": subject, "body": body}


def generate_rejection_email(
    candidate_name: str,
    role_title: str,
    missing_skills: list = None,
    company_name: str = "RecruiterAgent Team"
) -> dict:
    """Generates a polite, constructive feedback rejection email."""
    subject = f"Update regarding your application for {role_title} at {company_name}"

    skills_text = ""
    if missing_skills and len(missing_skills) > 0:
        skills_formatted = ", ".join(f"'{s}'" for s in missing_skills[:4])
        skills_text = f"\nSpecifically, for this role we were seeking additional hands-on experience in: {skills_formatted}.\n"

    body = f"""Dear {candidate_name},

Thank you for taking the time to apply for the {role_title} position at {company_name}.

We carefully reviewed your background and resume. While your qualifications are impressive, we have decided to move forward with other candidates whose skill sets align more closely with our specific requirements for this role.{skills_text}
We appreciate your interest in joining {company_name} and encourage you to apply for future opportunities that match your experience.

We wish you all the best in your career search.

Best regards,
{company_name} Recruiting Team
"""
    return {"subject": subject, "body": body}
