import sqlite3
import os
import json

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

    # Candidates table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Check and add missing columns to candidates table for seamless backwards-compatibility
    cur.execute("PRAGMA table_info(candidates);")
    existing_cols = {col["name"] for col in cur.fetchall()}

    new_cols = [
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
        ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    ]

    for col_name, col_type in new_cols:
        if col_name not in existing_cols:
            try:
                cur.execute(f"ALTER TABLE candidates ADD COLUMN {col_name} {col_type};")
            except sqlite3.OperationalError:
                pass

    # Interview slots table
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

    conn.commit()
    conn.close()


def save_candidate_pipeline_record(candidate_data: dict) -> int:
    """
    Inserts or updates a candidate record in the pipeline database.
    """
    init_db()
    conn = get_connection()
    cur = conn.cursor()

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

    # Check if candidate already exists by email (or name if no email)
    if email:
        cur.execute("SELECT id FROM candidates WHERE email = ?", (email,))
    else:
        cur.execute("SELECT id FROM candidates WHERE name = ?", (name,))
    
    existing = cur.fetchone()

    if existing:
        cand_id = existing["id"]
        cur.execute("""
            UPDATE candidates SET
                name = ?, phone = ?, skills = ?, experience = ?, education = ?,
                score = ?, matched_skills = ?, missing_skills = ?, resume_text = ?,
                stage = ?, notice_period_days = ?, current_ctc_lpa = ?, expected_ctc_lpa = ?,
                current_location = ?, preferred_locations = ?, relocation_willingness = ?,
                college_tier = ?, degree = ?, assessment_provider = ?, assessment_score = ?,
                assessment_status = ?, assessment_link = ?, notes = ?
            WHERE id = ?
        """, (
            name, phone, skills, experience, education,
            score, matched_skills, missing_skills, resume_text,
            stage, notice_period_days, current_ctc_lpa, expected_ctc_lpa,
            current_location, preferred_locations, relocation_willingness,
            college_tier, degree, assessment_provider, assessment_score,
            assessment_status, assessment_link, notes, cand_id
        ))
    else:
        cur.execute("""
            INSERT INTO candidates (
                name, email, phone, skills, experience, education,
                score, matched_skills, missing_skills, resume_text,
                stage, notice_period_days, current_ctc_lpa, expected_ctc_lpa,
                current_location, preferred_locations, relocation_willingness,
                college_tier, degree, assessment_provider, assessment_score,
                assessment_status, assessment_link, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, email, phone, skills, experience, education,
            score, matched_skills, missing_skills, resume_text,
            stage, notice_period_days, current_ctc_lpa, expected_ctc_lpa,
            current_location, preferred_locations, relocation_willingness,
            college_tier, degree, assessment_provider, assessment_score,
            assessment_status, assessment_link, notes
        ))
        cand_id = cur.lastrowid

    conn.commit()
    conn.close()
    return cand_id


def get_all_candidates(stage_filter: str = None) -> list:
    """
    Returns candidate records, optionally filtered by pipeline stage.
    """
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    if stage_filter and stage_filter != "All":
        cur.execute("SELECT * FROM candidates WHERE stage = ? ORDER BY score DESC", (stage_filter,))
    else:
        cur.execute("SELECT * FROM candidates ORDER BY score DESC")

    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_candidate_by_id(candidate_id: int) -> dict:
    """Fetches single candidate record by ID."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def update_candidate_stage(candidate_id: int, new_stage: str) -> bool:
    """Updates the pipeline stage of a candidate."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE candidates SET stage = ? WHERE id = ?", (new_stage, candidate_id))
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
        WHERE id = ?
    """, (provider, score, status, link, status, candidate_id))
    affected = cur.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def add_interview_slot(slot_time: str) -> int:
    """Adds a new available interview time slot."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO interview_slots (slot_time, is_booked, status) VALUES (?, 0, 'Available')",
        (slot_time,)
    )
    slot_id = cur.lastrowid
    conn.commit()
    conn.close()
    return slot_id


def get_available_slots():
    """Returns all available unbooked interview time slots."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM interview_slots WHERE is_booked = 0 ORDER BY id ASC")
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def book_interview_slot(slot_id: int, candidate_name: str, candidate_email: str, role_title: str, meeting_link: str) -> dict:
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
        WHERE id = ? AND is_booked = 0
    """, (candidate_name, candidate_email, role_title, meeting_link, slot_id))

    rows_affected = cur.rowcount
    conn.commit()

    if rows_affected > 0:
        # Also update candidate stage in candidates table if candidate exists
        cur.execute("UPDATE candidates SET stage = 'Interview Scheduled' WHERE email = ? OR name = ?", (candidate_email, candidate_name))
        conn.commit()

        cur.execute("SELECT * FROM interview_slots WHERE id = ?", (slot_id,))
        result = dict(cur.fetchone())
        conn.close()
        return result

    conn.close()
    return None


def get_all_scheduled_interviews():
    """Returns all booked interview records."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM interview_slots WHERE is_booked = 1 ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# Auto-initialize DB on import
init_db()