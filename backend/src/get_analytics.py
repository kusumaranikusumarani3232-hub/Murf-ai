import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "memory.db"


def get_analytics():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            # Aggregate metrics
            row = conn.execute("""
                SELECT
                    COUNT(*) as total_calls,
                    SUM(CASE WHEN outcome = 'successful' THEN 1 ELSE 0 END) as successful_calls,
                    SUM(CASE WHEN outcome = 'failed' THEN 1 ELSE 0 END) as failed_calls
                FROM call_analytics
            """).fetchone()

            total_calls = row[0] if row and row[0] is not None else 0
            successful_calls = row[1] if row and row[1] is not None else 0
            failed_calls = row[2] if row and row[2] is not None else 0

            # Fetch the list of calls
            conn.row_factory = sqlite3.Row
            call_rows = conn.execute("""
                SELECT session_id, timestamp, channel, outcome, duration
                FROM call_analytics
                ORDER BY timestamp DESC
            """).fetchall()
            calls = [dict(r) for r in call_rows]

            return {
                "summary": {
                    "total_calls": total_calls,
                    "successful_calls": successful_calls,
                    "failed_calls": failed_calls,
                },
                "calls": calls,
            }
    except Exception:
        return {
            "summary": {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
            },
            "calls": [],
        }


if __name__ == "__main__":
    print(json.dumps(get_analytics()))
