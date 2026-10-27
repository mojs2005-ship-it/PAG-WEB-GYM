import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402


@pytest.fixture
def app():
    """Build a fresh Flask app backed by its own temp SQLite file per test."""
    db_fd, db_path = tempfile.mkstemp()

    flask_app = create_app(test_config={"DATABASE": db_path, "TESTING": True})

    yield flask_app

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def session_id(client):
    """Create a session via the app and return its id, for tests that
    need an existing session to work against."""
    client.post("/add-session", data={"session_name": "Push Day"})
    with client.application.app_context():
        from models.sessions import get_sessions

        return get_sessions()[0]["id"]


@pytest.fixture
def exercise_id(client, session_id):
    """Create an exercise inside `session_id` and return its id."""
    client.post(
        f"/sessions/{session_id}/add-exercise", data={"exercise_name": "Bench Press"}
    )
    with client.application.app_context():
        from models.exercises import get_exercises_for_session

        return get_exercises_for_session(session_id)[0]["id"]
