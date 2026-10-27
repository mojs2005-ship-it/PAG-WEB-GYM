"""Data-access layer, segregated by entity.

The legacy db.py mixed every table's queries into a single file, and
app.py additionally re-implemented "find by id" logic in Python by
looping over get_sessions()/get_exercises_for_session(). Here each
entity (sessions, exercises, sets) owns its own module and its own
"get by id" query pushed down to SQL, which is both clearer and more
efficient.
"""
