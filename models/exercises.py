"""Data-access functions for exercises."""

from database import get_db


def get_exercises_for_session(session_id):
    """Return all exercises belonging to a session."""
    db = get_db()
    return db.execute(
        "SELECT id, name FROM exercises WHERE session_id = ? ORDER BY id",
        (session_id,),
    ).fetchall()


def get_exercise_by_id(session_id, exercise_id):
    """Return a single exercise row scoped to its session, or None."""
    db = get_db()
    return db.execute(
        "SELECT id, name FROM exercises WHERE id = ? AND session_id = ?",
        (exercise_id, session_id),
    ).fetchone()


def add_exercise(session_id, name):
    """Add an exercise to a session and return its new id."""
    db = get_db()
    cursor = db.execute(
        "INSERT INTO exercises (session_id, name) VALUES (?, ?)",
        (session_id, name),
    )
    db.commit()
    return cursor.lastrowid


def delete_exercise(exercise_id):
    """Delete an exercise and every set that belongs to it."""
    db = get_db()
    db.execute("DELETE FROM sets WHERE exercise_id = ?", (exercise_id,))
    cursor = db.execute("DELETE FROM exercises WHERE id = ?", (exercise_id,))
    db.commit()
    return cursor.rowcount > 0


def get_exercise_history():
    """Return exercise history grouped by exercise name."""
    db = get_db()
    return db.execute(
        """
        SELECT name, COUNT(DISTINCT session_id)
        FROM exercises
        GROUP BY name
        ORDER BY name
        """
    ).fetchall()
