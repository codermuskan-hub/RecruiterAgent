import sqlite3

conn = sqlite3.connect("candidates.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE candidates (
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
)
""")

conn.commit()
conn.close()