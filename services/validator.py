import re
from typing import Dict, Any, List, Tuple


def validate_job_description(jd_text: str) -> Tuple[bool, str]:
    """
    Validates that the entered Job Description meets quality and clarity standards.
    Checks for minimum length, presence of key requirement sections or technical keywords.
    """
    if not jd_text or not jd_text.strip():
        return False, "Job Description cannot be empty. Please enter the requirements, role, and responsibilities."

    text_clean = jd_text.strip()
    if len(text_clean) < 40:
        return False, f"Job Description is too short ({len(text_clean)} characters). Please provide a more comprehensive description (min 40 characters) including technical skills."

    # Check for basic role or skill cues
    tech_keywords = [
        "python", "java", "react", "javascript", "sql", "node", "aws", "docker", 
        "developer", "engineer", "lead", "analyst", "manager", "experience", "skills",
        "requirements", "responsibilities", "c++", "data", "cloud"
    ]
    has_cue = any(k in text_clean.lower() for k in tech_keywords)
    if not has_cue:
        return False, "Job Description appears vague. Please specify the target role or key technical skills required."

    return True, "Valid Job Description"


def validate_candidate_data(candidate: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates parsed or manually entered candidate data.
    Ensures name, contact, valid numerical ranges for experience/CTC/notice period.
    """
    errors = []
    
    # Validate Name
    name = candidate.get("name", "").strip()
    if not name or name == "Unknown" or len(name) < 2:
        errors.append("Invalid or missing candidate name.")

    # Validate Email (if provided)
    email = candidate.get("email", "").strip()
    if email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        errors.append(f"Invalid email format: '{email}'")

    # Validate Phone (if provided)
    phone = candidate.get("phone", "").strip()
    if phone and len(re.sub(r"[^\d]", "", phone)) < 7:
        errors.append(f"Phone number '{phone}' appears incomplete.")

    # Validate Numerical Ranges
    notice = candidate.get("notice_period_days")
    if notice is not None:
        try:
            n_int = int(notice)
            if n_int < 0 or n_int > 365:
                errors.append(f"Notice period ({n_int} days) is outside realistic range (0 - 365 days).")
        except ValueError:
            errors.append("Notice period must be an integer number of days.")

    c_ctc = candidate.get("current_ctc_lpa")
    if c_ctc is not None:
        try:
            if float(c_ctc) < 0:
                errors.append("Current CTC cannot be negative.")
        except ValueError:
            errors.append("Current CTC must be a numeric value.")

    e_ctc = candidate.get("expected_ctc_lpa")
    if e_ctc is not None:
        try:
            if float(e_ctc) < 0:
                errors.append("Expected CTC cannot be negative.")
        except ValueError:
            errors.append("Expected CTC must be a numeric value.")

    is_valid = len(errors) == 0
    return is_valid, errors
