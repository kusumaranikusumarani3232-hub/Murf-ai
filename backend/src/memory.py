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
        conn.commit()


def get_user(user_id: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,)
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
        conn.execute("""
            INSERT INTO users (
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
        """, (
            user_id,
            name,
            language_preference,
            current_level,
            topics_covered,
            common_mistakes,
            datetime.now().isoformat(),
        ))
        conn.commit()


init_db()