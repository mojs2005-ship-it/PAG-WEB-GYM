"""Data-access functions for workout sessions."""

from datetime import date

from database import get_db


def get_sessions():
    """Return all workout sessions ordered newest first."""
    db = get_db()
    return db.execute(
        "SELECT id, name, date FROM sessions ORDER BY id DESC"
    ).fetchall()


def get_session_by_id(session_id):
    """Return a single session row by id, or None if it does not exist."""
    db = get_db()
    return db.execute(
        "SELECT id, name, date FROM sessions WHERE id = ?",
        (session_id,),
    ).fetchone()


def start_session(name):
    """Create a new session dated today and return its new id."""
    db = get_db()
    today = str(date.today())
    cursor = db.execute(
        "INSERT INTO sessions (date, name) VALUES (?, ?)",
        (today, name),
    )
    db.commit()
    return cursor.lastrowid


def delete_session(session_id):
    """Delete a session and every exercise/set that belongs to it."""
    db = get_db()

    exercise_ids = [
        row[0]
        for row in db.execute(
            "SELECT id FROM exercises WHERE session_id = ?", (session_id,)
        ).fetchall()
    ]

    for exercise_id in exercise_ids:
        db.execute("DELETE FROM sets WHERE exercise_id = ?", (exercise_id,))

    db.execute("DELETE FROM exercises WHERE session_id = ?", (session_id,))
    cursor = db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    db.commit()

    return cursor.rowcount > 0
