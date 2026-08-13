import sqlite3

import pytest

from agent import Assistant

# Import the memory functions
from memory import DB_PATH, get_call_analytics, init_db, save_call_analytics


@pytest.fixture(autouse=True)
def setup_db():
    # Setup test database and clean the call_analytics table
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM call_analytics")
        conn.commit()


def test_successful_call():
    # Arrange
    session_id = "test_sess_success"
    channel = "browser"
    outcome = "successful"
    duration = 45

    # Act
    save_call_analytics(session_id, channel, outcome, duration)

    # Assert
    analytics = get_call_analytics()
    # Find the record
    record = next((r for r in analytics if r["session_id"] == session_id), None)
    assert record is not None
    assert record["outcome"] == "successful"
    assert record["channel"] == "browser"
    assert record["duration"] == 45


def test_failed_call():
    # Arrange
    session_id = "test_sess_failed"
    channel = "sip"
    outcome = "failed"
    duration = 10

    # Act
    save_call_analytics(session_id, channel, outcome, duration)

    # Assert
    analytics = get_call_analytics()
    record = next((r for r in analytics if r["session_id"] == session_id), None)
    assert record is not None
    assert record["outcome"] == "failed"
    assert record["channel"] == "sip"
    assert record["duration"] == 10


def test_no_duplicate():
    # Arrange
    session_id = "test_sess_duplicate"
    channel = "browser"
    outcome = "successful"
    duration = 30

    # Act: save twice with the same session_id
    save_call_analytics(session_id, channel, outcome, duration)
    save_call_analytics(session_id, channel, outcome, duration)

    # Assert: only one record is in the database
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT count(*) FROM call_analytics WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        assert row[0] == 1


def test_privacy():
    # Arrange & Act
    session_id = "test_sess_privacy"
    save_call_analytics(session_id, "browser", "successful", 20)

    # Assert
    # Verify that the table doesn't have transcript or sensitive columns
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM call_analytics LIMIT 1").fetchone()
        record = dict(row) if row else {}

        # Only allow key fields
        allowed_keys = {
            "session_id",
            "timestamp",
            "channel",
            "outcome",
            "duration",
        }
        record_keys = set(record.keys())
        assert record_keys.issubset(allowed_keys)

        # Verify that no transcription text or user details are present
        for val in record.values():
            val_str = str(val).lower()
            assert "transcript" not in val_str
            assert "password" not in val_str
            assert "otp" not in val_str
            assert "pin" not in val_str


@pytest.mark.asyncio
async def test_assistant_tool_marking() -> None:
    assistant = Assistant()
    assert not assistant.exercise_completed

    # Invoke the tool directly
    await assistant.mark_exercise_completed(context=None)

    assert assistant.exercise_completed
