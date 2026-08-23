import sqlite3
import os
import json
from typing import Dict, Any, List, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "candidates.db")


def get_connection():
    """Returns a SQLite connection object with Row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes SQLite database tables if they do not exist, and applies schema migrations."""
    conn = get_connection()
    cur = conn.cursor()

    # 1. Users Table (Role-Based Access Control)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL,
        email TEXT,
        department TEXT DEFAULT 'Engineering',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Jobs Table (Job Requisitions created by Hiring Managers)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        department TEXT DEFAULT 'Engineering',
        description TEXT,
        required_skills TEXT,
        min_experience REAL DEFAULT 0.0,
        budget_max_lpa REAL DEFAULT 0.0,
        location TEXT DEFAULT 'Bengaluru / Hybrid',
        status TEXT DEFAULT 'Open',
        created_by TEXT DEFAULT 'Vikram Malhotra',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 3. Candidates Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER DEFAULT 1,
        name TEXT,
        email TEXT,
        phone TEXT,
        skills TEXT,
        experience TEXT,
        education TEXT,
        score REAL,
        matched_skills TEXT,
        missing_skills TEXT,
        resume_text TEXT,
        stage TEXT DEFAULT 'Applied',
        notice_period_days INTEGER DEFAULT 30,
        current_ctc_lpa REAL DEFAULT 0.0,
        expected_ctc_lpa REAL DEFAULT 0.0,
        current_location TEXT DEFAULT 'Not Specified',
        preferred_locations TEXT DEFAULT 'Any',
        relocation_willingness TEXT DEFAULT 'Yes',
        college_tier TEXT DEFAULT 'Tier-3',
        degree TEXT DEFAULT 'B.Tech',
        assessment_provider TEXT,
        assessment_score REAL DEFAULT 0.0,
        assessment_status TEXT DEFAULT 'Not Sent',
        assessment_link TEXT,
        notes TEXT,
        offer_status TEXT DEFAULT 'Pending',
        manager_decision TEXT DEFAULT 'Under Review',
        manager_notes TEXT,
        is_archived BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Check and add missing columns to candidates table for backwards-compatibility
    cur.execute("PRAGMA table_info(candidates);")
    existing_cols = {col["name"] for col in cur.fetchall()}

    new_cols = [
        ("job_id", "INTEGER DEFAULT 1"),
        ("stage", "TEXT DEFAULT 'Applied'"),
        ("notice_period_days", "INTEGER DEFAULT 30"),
        ("current_ctc_lpa", "REAL DEFAULT 0.0"),
        ("expected_ctc_lpa", "REAL DEFAULT 0.0"),
        ("current_location", "TEXT DEFAULT 'Not Specified'"),
        ("preferred_locations", "TEXT DEFAULT 'Any'"),
        ("relocation_willingness", "TEXT DEFAULT 'Yes'"),
        ("college_tier", "TEXT DEFAULT 'Tier-3'"),
        ("degree", "TEXT DEFAULT 'B.Tech'"),
        ("assessment_provider", "TEXT"),
        ("assessment_score", "REAL DEFAULT 0.0"),
        ("assessment_status", "TEXT DEFAULT 'Not Sent'"),
        ("assessment_link", "TEXT"),
        ("notes", "TEXT"),
        ("offer_status", "TEXT DEFAULT 'Pending'"),
        ("manager_decision", "TEXT DEFAULT 'Under Review'"),
        ("manager_notes", "TEXT"),
        ("is_archived", "BOOLEAN DEFAULT 0"),
        ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    ]

    for col_name, col_type in new_cols:
        if col_name not in existing_cols:
            try:
                cur.execute(f"ALTER TABLE candidates ADD COLUMN {col_name} {col_type};")
            except sqlite3.OperationalError:
                pass

    # 4. Interview Slots Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS interview_slots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slot_time TEXT NOT NULL,
        is_booked BOOLEAN DEFAULT 0,
        candidate_name TEXT,
        candidate_email TEXT,
        role_title TEXT,
        meeting_link TEXT,
        status TEXT DEFAULT 'Available'
    );
    """)

    # 5. Interview Feedback Table (Technical Interviewer Scorecards)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS interview_feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_id INTEGER NOT NULL,
        interviewer_name TEXT NOT NULL,
        technical_rating INTEGER DEFAULT 4,
        system_design_rating INTEGER DEFAULT 4,
        cultural_fit_rating INTEGER DEFAULT 4,
        overall_recommendation TEXT NOT NULL,
        feedback_notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (candidate_id) REFERENCES candidates(id)
    );
    """)

    # Seed Default Roles & Sample Jobs if empty
    cur.execute("SELECT COUNT(*) as cnt FROM users;")
    if cur.fetchone()["cnt"] == 0:
        cur.executemany("""
        INSERT INTO users (username, full_name, role, email, department) VALUES (?, ?, ?, ?, ?);
        """, [
            ("recruiter_priya", "Priya Sharma", "Recruiter", "priya.sharma@techcorp.in", "Talent Acquisition"),
            ("manager_vikram", "Vikram Malhotra", "Hiring Manager", "vikram.m@techcorp.in", "Engineering Leadership"),
            ("interviewer_rahul", "Rahul Verma", "Technical Interviewer", "rahul.v@techcorp.in", "Backend Core Team"),
            ("admin_system", "System Administrator", "Admin", "admin@techcorp.in", "Operations & HR")
        ])

    cur.execute("SELECT COUNT(*) as cnt FROM jobs;")
    if cur.fetchone()["cnt"] == 0:
        cur.executemany("""
        INSERT INTO jobs (title, department, description, required_skills, min_experience, budget_max_lpa, location, status, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, [
            (
                "Senior Backend Engineer (Python/FastAPI)",
                "Backend Engineering",
                "Looking for a Senior Backend Engineer to build scalable asynchronous microservices, REST APIs, and event-driven architectures with Docker and AWS.",
                "Python, FastAPI, Docker, PostgreSQL, AWS, Redis",
                4.0,
                24.0,
                "Bengaluru / Hybrid",
                "Open",
                "Vikram Malhotra"
            ),
            (
                "Full Stack Developer (Java & React)",
                "Core Platform",
                "Design and develop robust enterprise web applications using Spring Boot, Hibernate, and modern React/Next.js frontends.",
                "Java, Spring Boot, React, Next.js, MySQL, Kafka",
                3.0,
                20.0,
                "Delhi-NCR / Gurgaon",
                "Open",
                "Vikram Malhotra"
            )
        ])

    conn.commit()
    conn.close()


# ---------------------------------------------------------
# User Management (Authentication & Directory)
# ---------------------------------------------------------
def get_all_users() -> List[Dict[str, Any]]:
    """Returns all system users."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users ORDER BY id ASC;")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_user_by_role(role: str) -> Optional[Dict[str, Any]]:
    """Fetches the first user matching a given role."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE role = ? LIMIT 1;", (role,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


# ---------------------------------------------------------
# Job Requisitions CRUD (Hiring Manager Features)
# ---------------------------------------------------------
def create_job(job_data: Dict[str, Any]) -> int:
    """Creates a new Job Requisition."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO jobs (title, department, description, required_skills, min_experience, budget_max_lpa, location, status, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        job_data.get("title", "Software Engineer"),
        job_data.get("department", "Engineering"),
        job_data.get("description", ""),
        job_data.get("required_skills", ""),
        float(job_data.get("min_experience", 0.0)),
        float(job_data.get("budget_max_lpa", 0.0)),
        job_data.get("location", "Bengaluru / Hybrid"),
        job_data.get("status", "Open"),
        job_data.get("created_by", "Hiring Manager")
    ))
    job_id = cur.lastrowid
    conn.commit()
    conn.close()
    return job_id


def get_all_jobs(status: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves all jobs, optionally filtered by status ('Open'/'Closed')."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()
    if status and status != "All":
        cur.execute("SELECT * FROM jobs WHERE status = ? ORDER BY id DESC;", (status,))
    else:
        cur.execute("SELECT * FROM jobs ORDER BY id DESC;")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_job_by_id(job_id: int) -> Optional[Dict[str, Any]]:
    """Fetches a single job by its ID."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM jobs WHERE id = ?;", (job_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def update_job_status(job_id: int, new_status: str) -> bool:
    """Updates job status (e.g. 'Open' -> 'Closed')."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE jobs SET status = ? WHERE id = ?;", (new_status, job_id))
    affected = cur.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def delete_job(job_id: int) -> bool:
    """Deletes a job requisition."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM jobs WHERE id = ?;", (job_id,))
    affected = cur.rowcount
    conn.commit()
    conn.close()
    return affected > 0


# ---------------------------------------------------------
# Candidates CRUD (Recruiter & Manager Features)
# ---------------------------------------------------------
def save_candidate_pipeline_record(candidate_data: dict) -> int:
    """
    Inserts or updates a candidate record in the pipeline database.
    Links candidate to job_id and preserves historical talent pool data.
    """
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    job_id = int(candidate_data.get("job_id", 1))
    name = candidate_data.get("name", "Unknown")
    email = candidate_data.get("email", "")
    phone = candidate_data.get("phone", "")
    skills = json.dumps(candidate_data.get("skills", [])) if isinstance(candidate_data.get("skills"), (list, dict)) else str(candidate_data.get("skills", ""))
    experience = json.dumps(candidate_data.get("experience", [])) if isinstance(candidate_data.get("experience"), (list, dict)) else str(candidate_data.get("experience", ""))
    education = json.dumps(candidate_data.get("education", [])) if isinstance(candidate_data.get("education"), (list, dict)) else str(candidate_data.get("education", ""))
    score = float(candidate_data.get("score", 0.0))
    matched_skills = json.dumps(candidate_data.get("matched_skills", [])) if isinstance(candidate_data.get("matched_skills"), list) else str(candidate_data.get("matched_skills", ""))
    missing_skills = json.dumps(candidate_data.get("missing_skills", [])) if isinstance(candidate_data.get("missing_skills"), list) else str(candidate_data.get("missing_skills", ""))
    resume_text = candidate_data.get("resume_text", "")
    stage = candidate_data.get("stage", "Applied")
    notice_period_days = int(candidate_data.get("notice_period_days", 30))
    current_ctc_lpa = float(candidate_data.get("current_ctc_lpa", 0.0))
    expected_ctc_lpa = float(candidate_data.get("expected_ctc_lpa", 0.0))
    current_location = candidate_data.get("current_location", "Not Specified")
    preferred_locations = candidate_data.get("preferred_locations", "Any")
    relocation_willingness = candidate_data.get("relocation_willingness", "Yes")
    college_tier = candidate_data.get("college_tier", "Tier-3")
    degree = candidate_data.get("degree", "B.Tech")
    assessment_provider = candidate_data.get("assessment_provider", None)
    assessment_score = float(candidate_data.get("assessment_score", 0.0))
    assessment_status = candidate_data.get("assessment_status", "Not Sent")
    assessment_link = candidate_data.get("assessment_link", "")
    notes = candidate_data.get("notes", "")
    offer_status = candidate_data.get("offer_status", "Pending")
    manager_decision = candidate_data.get("manager_decision", "Under Review")
    manager_notes = candidate_data.get("manager_notes", "")
    is_archived = 1 if candidate_data.get("is_archived") else 0

    # Check if candidate exists by email or name
    if email:
        cur.execute("SELECT id FROM candidates WHERE email = ?;", (email,))
    else:
        cur.execute("SELECT id FROM candidates WHERE name = ?;", (name,))
    
    existing = cur.fetchone()

    if existing:
        cand_id = existing["id"]
        cur.execute("""
            UPDATE candidates SET
                job_id = ?, name = ?, phone = ?, skills = ?, experience = ?, education = ?,
                score = ?, matched_skills = ?, missing_skills = ?, resume_text = ?,
                stage = ?, notice_period_days = ?, current_ctc_lpa = ?, expected_ctc_lpa = ?,
                current_location = ?, preferred_locations = ?, relocation_willingness = ?,
                college_tier = ?, degree = ?, assessment_provider = ?, assessment_score = ?,
                assessment_status = ?, assessment_link = ?, notes = ?, offer_status = ?,
                manager_decision = ?, manager_notes = ?, is_archived = ?
            WHERE id = ?;
        """, (
            job_id, name, phone, skills, experience, education,
            score, matched_skills, missing_skills, resume_text,
            stage, notice_period_days, current_ctc_lpa, expected_ctc_lpa,
            current_location, preferred_locations, relocation_willingness,
            college_tier, degree, assessment_provider, assessment_score,
            assessment_status, assessment_link, notes, offer_status,
            manager_decision, manager_notes, is_archived, cand_id
        ))
    else:
        cur.execute("""
            INSERT INTO candidates (
                job_id, name, email, phone, skills, experience, education,
                score, matched_skills, missing_skills, resume_text,
                stage, notice_period_days, current_ctc_lpa, expected_ctc_lpa,
                current_location, preferred_locations, relocation_willingness,
                college_tier, degree, assessment_provider, assessment_score,
                assessment_status, assessment_link, notes, offer_status,
                manager_decision, manager_notes, is_archived
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            job_id, name, email, phone, skills, experience, education,
            score, matched_skills, missing_skills, resume_text,
            stage, notice_period_days, current_ctc_lpa, expected_ctc_lpa,
            current_location, preferred_locations, relocation_willingness,
            college_tier, degree, assessment_provider, assessment_score,
            assessment_status, assessment_link, notes, offer_status,
            manager_decision, manager_notes, is_archived
        ))
        cand_id = cur.lastrowid

    conn.commit()
    conn.close()
    return cand_id


def get_all_candidates(
    stage_filter: Optional[str] = None,
    job_id_filter: Optional[int] = None,
    include_archived: bool = False
) -> List[Dict[str, Any]]:
    """
    Returns candidate records, with flexible filtering by stage, job requisition, and archival status.
    """
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    query = "SELECT * FROM candidates WHERE 1=1"
    params = []

    if not include_archived:
        query += " AND (is_archived = 0 OR is_archived IS NULL)"

    if job_id_filter:
        query += " AND job_id = ?"
        params.append(job_id_filter)

    if stage_filter and stage_filter != "All":
        query += " AND stage = ?"
        params.append(stage_filter)

    query += " ORDER BY score DESC;"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_candidate_by_id(candidate_id: int) -> Optional[Dict[str, Any]]:
    """Fetches single candidate record by ID."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM candidates WHERE id = ?;", (candidate_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def update_candidate_stage(candidate_id: int, new_stage: str) -> bool:
    """Updates candidate pipeline stage."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE candidates SET stage = ? WHERE id = ?;", (new_stage, candidate_id))
    affected = cur.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def update_candidate_manager_decision(candidate_id: int, decision: str, notes: str = "") -> bool:
    """Updates hiring manager's executive decision (e.g. 'Approved for Offer', 'Rejected', 'Hold')."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()
    offer_status = "Approved" if "Approved" in decision else ("Rejected" if "Rejected" in decision else "Pending")
    new_stage = "Offer Extended" if offer_status == "Approved" else ("Rejected" if offer_status == "Rejected" else None)

    if new_stage:
        cur.execute("""
            UPDATE candidates SET manager_decision = ?, manager_notes = ?, offer_status = ?, stage = ?
            WHERE id = ?;
        """, (decision, notes, offer_status, new_stage, candidate_id))
    else:
        cur.execute("""
            UPDATE candidates SET manager_decision = ?, manager_notes = ?, offer_status = ?
            WHERE id = ?;
        """, (decision, notes, offer_status, candidate_id))

    affected = cur.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def archive_candidate(candidate_id: int, archive_state: bool = True) -> bool:
    """Soft deletes or unarchives a candidate (keeps historical data in talent pool)."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE candidates SET is_archived = ? WHERE id = ?;", (1 if archive_state else 0, candidate_id))
    affected = cur.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def delete_candidate(candidate_id: int) -> bool:
    """Hard deletes a candidate record permanently (for GDPR/compliance requests)."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM candidates WHERE id = ?;", (candidate_id,))
    cur.execute("DELETE FROM interview_feedback WHERE candidate_id = ?;", (candidate_id,))
    affected = cur.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def update_candidate_assessment(candidate_id: int, provider: str, score: float, status: str, link: str = "") -> bool:
    """Updates candidate assessment details (HackerEarth / Mettl)."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE candidates SET
            assessment_provider = ?,
            assessment_score = ?,
            assessment_status = ?,
            assessment_link = ?,
            stage = CASE WHEN ? = 'Completed' THEN 'Assessment Completed' ELSE stage END
        WHERE id = ?;
    """, (provider, score, status, link, status, candidate_id))
    affected = cur.rowcount
    conn.commit()
    conn.close()
    return affected > 0


# ---------------------------------------------------------
# Technical Interviewer Scorecards (Staff Role)
# ---------------------------------------------------------
def submit_interview_feedback(feedback_data: Dict[str, Any]) -> int:
    """Inserts an interview feedback scorecard and updates candidate status."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO interview_feedback (
            candidate_id, interviewer_name, technical_rating, system_design_rating,
            cultural_fit_rating, overall_recommendation, feedback_notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?);
    """, (
        int(feedback_data.get("candidate_id")),
        feedback_data.get("interviewer_name", "Interviewer"),
        int(feedback_data.get("technical_rating", 4)),
        int(feedback_data.get("system_design_rating", 4)),
        int(feedback_data.get("cultural_fit_rating", 4)),
        feedback_data.get("overall_recommendation", "Yes"),
        feedback_data.get("feedback_notes", "")
    ))
    feedback_id = cur.lastrowid

    # Update candidate notes with latest interviewer summary
    cand_id = int(feedback_data.get("candidate_id"))
    summary_note = f"Interviewer [{feedback_data.get('interviewer_name')}]: {feedback_data.get('overall_recommendation')} (Tech: {feedback_data.get('technical_rating')}/5)"
    cur.execute("UPDATE candidates SET notes = COALESCE(notes || ' | ', '') || ? WHERE id = ?;", (summary_note, cand_id))

    conn.commit()
    conn.close()
    return feedback_id


def get_interview_feedback_for_candidate(candidate_id: int) -> List[Dict[str, Any]]:
    """Retrieves all interview scorecards for a candidate."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM interview_feedback WHERE candidate_id = ? ORDER BY id DESC;", (candidate_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------
# Interview Slots Scheduling
# ---------------------------------------------------------
def add_interview_slot(slot_time: str) -> int:
    """Adds a new available interview time slot."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO interview_slots (slot_time, is_booked, status) VALUES (?, 0, 'Available');",
        (slot_time,)
    )
    slot_id = cur.lastrowid
    conn.commit()
    conn.close()
    return slot_id


def get_available_slots() -> List[Dict[str, Any]]:
    """Returns all available unbooked interview time slots."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM interview_slots WHERE is_booked = 0 ORDER BY id ASC;")
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def book_interview_slot(slot_id: int, candidate_name: str, candidate_email: str, role_title: str, meeting_link: str) -> Optional[Dict[str, Any]]:
    """Books an interview slot for a specific candidate and updates candidate stage."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE interview_slots
        SET is_booked = 1,
            candidate_name = ?,
            candidate_email = ?,
            role_title = ?,
            meeting_link = ?,
            status = 'Scheduled'
        WHERE id = ? AND is_booked = 0;
    """, (candidate_name, candidate_email, role_title, meeting_link, slot_id))

    rows_affected = cur.rowcount
    conn.commit()

    if rows_affected > 0:
        cur.execute("UPDATE candidates SET stage = 'Interview Scheduled' WHERE email = ? OR name = ?;", (candidate_email, candidate_name))
        conn.commit()

        cur.execute("SELECT * FROM interview_slots WHERE id = ?;", (slot_id,))
        result = dict(cur.fetchone())
        conn.close()
        return result

    conn.close()
    return None


def get_all_scheduled_interviews() -> List[Dict[str, Any]]:
    """Returns all booked interview records."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM interview_slots WHERE is_booked = 1 ORDER BY id DESC;")
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# Auto-initialize DB on import
init_db()