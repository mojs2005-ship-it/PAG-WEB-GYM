"""Data-access functions for logged sets (reps + weight)."""

from database import get_db


def get_sets_for_exercise(exercise_id):
    """Return all sets logged for a specific exercise."""
    db = get_db()
    return db.execute(
        "SELECT id, reps, weight FROM sets WHERE exercise_id = ? ORDER BY id",
        (exercise_id,),
    ).fetchall()


def add_set(exercise_id, reps, weight):
    """Add a completed set to an exercise and return its new id."""
    db = get_db()
    cursor = db.execute(
        "INSERT INTO sets (exercise_id, reps, weight) VALUES (?, ?, ?)",
        (exercise_id, reps, weight),
    )
    db.commit()
    return cursor.lastrowid


def delete_set(set_id):
    """Delete a single set by id."""
    db = get_db()
    cursor = db.execute("DELETE FROM sets WHERE id = ?", (set_id,))
    db.commit()
    return cursor.rowcount > 0
