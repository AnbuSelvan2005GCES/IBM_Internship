import sqlite3
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "helpdesk.db"


def init_db():
    """Create the diagnoses table if it doesn't already exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS diagnoses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            problem TEXT NOT NULL,
            diagnosis TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def log_diagnosis(problem: str, diagnosis: str):
    """Store a single problem/diagnosis pair with a timestamp."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO diagnoses (problem, diagnosis, created_at) VALUES (?, ?, ?)",
        (problem, diagnosis, datetime.now(timezone.utc).isoformat())
    )
    conn.commit()
    conn.close()


def get_recent_diagnoses(limit: int = 20):
    """Return the most recent diagnoses, newest first."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, problem, diagnosis, created_at FROM diagnoses "
        "ORDER BY id DESC LIMIT ?",
        (limit,)
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows
