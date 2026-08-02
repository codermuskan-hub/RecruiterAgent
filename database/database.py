import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "candidates.db")


def get_connection():
    """Returns a SQLite connection object with Row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes SQLite database tables if they do not exist."""
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
        resume_text TEXT
    );
    """)

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
    """Books an interview slot for a specific candidate."""
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