"""Database connection lifecycle.

Legacy behaviour: app.py opened ONE global sqlite3 connection at import
time (`conn = sqlite3.connect(...)`) and every request reused it,
which is unsafe under a real multi-worker server and impossible to
swap out cleanly for tests.

New behaviour: a fresh connection is opened per request-context via
Flask's `g` object and closed automatically on teardown, following
Flask's recommended application-factory pattern. Row objects are used
instead of raw tuples so callers can access columns either by index
(`row[0]`) or by name (`row["name"]`), keeping the old templates
(which index into tuples) working unmodified while enabling clearer
code going forward.
"""

import sqlite3

from flask import current_app, g

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE TABLE IF NOT EXISTS sets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exercise_id INTEGER NOT NULL,
    reps INTEGER NOT NULL,
    weight REAL NOT NULL,
    FOREIGN KEY (exercise_id) REFERENCES exercises(id)
);
"""


def get_db():
    """Return the sqlite3 connection for the current request, opening
    one if it does not exist yet."""
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"],
            check_same_thread=False,
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")

    return g.db


def close_db(exception=None):
    """Close the connection for the current request, if one was opened."""
    db = g.pop("db", None)

    if db is not None:
        db.close()


def init_db():
    """Create all required tables if they do not already exist."""
    db = get_db()
    db.executescript(SCHEMA_SQL)
    db.commit()


def init_app(app):
    """Wire the database lifecycle into the Flask app."""
    app.teardown_appcontext(close_db)

    with app.app_context():
        init_db()
