"""
database.py
SQLite storage for two things:
1. conversation_history — the raw turn-by-turn memory used by memory.py
   to give the agent context from earlier in the same session.
2. qa_log — a permanent record of every question asked and answer given,
   independent of session, useful for review/audit later.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "student_support.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,        -- 'user' or 'assistant'
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS qa_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# ---------- Conversation memory ----------

def add_message(session_id: str, role: str, content: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO conversation_history (session_id, role, content, created_at) "
        "VALUES (?, ?, ?, ?)",
        (session_id, role, content, datetime.now(timezone.utc).isoformat())
    )
    conn.commit()
    conn.close()


def get_conversation_history(session_id: str, limit: int = 10):
    """Return the most recent `limit` messages for a session, oldest first."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role, content, created_at FROM conversation_history "
        "WHERE session_id = ? ORDER BY id DESC LIMIT ?",
        (session_id, limit)
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return list(reversed(rows))  # oldest first, for natural reading order


def clear_session(session_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM conversation_history WHERE session_id = ?",
        (session_id,)
    )
    conn.commit()
    conn.close()


# ---------- Permanent Q&A log ----------

def log_qa(session_id: str, question: str, answer: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO qa_log (session_id, question, answer, created_at) "
        "VALUES (?, ?, ?, ?)",
        (session_id, question, answer, datetime.now(timezone.utc).isoformat())
    )
    conn.commit()
    conn.close()


def get_recent_qa(limit: int = 20):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT session_id, question, answer, created_at FROM qa_log "
        "ORDER BY id DESC LIMIT ?",
        (limit,)
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows