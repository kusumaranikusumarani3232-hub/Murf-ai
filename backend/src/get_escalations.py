import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "memory.db"

def get_escalations():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM escalations ORDER BY created_at DESC").fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        # Return empty list if table doesn't exist yet or other errors
        return []

if __name__ == "__main__":
    print(json.dumps(get_escalations()))
