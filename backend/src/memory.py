import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "memory.db"


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                language_preference TEXT,
                current_level TEXT,
                topics_covered TEXT,
                common_mistakes TEXT,
                last_interaction TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS escalations (
                reference_id TEXT PRIMARY KEY,
                user_id TEXT,
                description TEXT,
                checked_actions TEXT,
                urgency TEXT,
                language TEXT,
                follow_up_method TEXT,
                status TEXT DEFAULT 'open',
                created_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS call_analytics (
                session_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                channel TEXT NOT NULL,
                outcome TEXT NOT NULL,
                duration INTEGER
            )
        """)
        conn.commit()


def get_user(user_id: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()

        return dict(row) if row else None


def save_user(
    user_id: str,
    name: str,
    language_preference: str = "",
    current_level: str = "",
    topics_covered: str = "",
    common_mistakes: str = "",
):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO users (
                user_id,
                name,
                language_preference,
                current_level,
                topics_covered,
                common_mistakes,
                last_interaction
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                name = excluded.name,
                language_preference = excluded.language_preference,
                current_level = excluded.current_level,
                topics_covered = excluded.topics_covered,
                common_mistakes = excluded.common_mistakes,
                last_interaction = excluded.last_interaction
        """,
            (
                user_id,
                name,
                language_preference,
                current_level,
                topics_covered,
                common_mistakes,
                datetime.now().isoformat(),
            ),
        )
        conn.commit()


def create_escalation_in_db(
    reference_id: str,
    user_id: str,
    description: str,
    checked_actions: str,
    urgency: str,
    language: str,
    follow_up_method: str,
):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO escalations (
                reference_id,
                user_id,
                description,
                checked_actions,
                urgency,
                language,
                follow_up_method,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 'open', ?)
        """,
            (
                reference_id,
                user_id,
                description,
                checked_actions,
                urgency.lower(),
                language,
                follow_up_method,
                datetime.now().isoformat(),
            ),
        )
        conn.commit()


def save_call_analytics(
    session_id: str,
    channel: str,
    outcome: str,
    duration: int | None = None,
):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO call_analytics (
                session_id,
                timestamp,
                channel,
                outcome,
                duration
            )
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                session_id,
                datetime.now().isoformat(),
                channel,
                outcome,
                duration,
            ),
        )
        conn.commit()


def get_call_analytics():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM call_analytics ORDER BY timestamp DESC"
            ).fetchall()
            return [dict(row) for row in rows]
    except Exception:
        return []


init_db()
