"""JSON API.

The legacy application only spoke HTML. As part of the modernization
this blueprint exposes the same data as JSON under /api, so the same
backend could power a mobile app or a JS frontend in the future.
"""

import time
from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, request

from database import get_db
from models import exercises as exercises_model
from models import sessions as sessions_model
from models import sets as sets_model
from services import parse_positive_int, parse_weight

api_bp = Blueprint("api", __name__, url_prefix="/api")

_STARTED_AT = time.time()


@api_bp.route("/health", methods=["GET"])
def health():
    """Liveness/readiness probe used by the hosting platform and monitors.

    Returns 200 when the app AND its database respond, 503 otherwise, so
    an orchestrator can restart or stop routing traffic to a sick instance.
    """
    try:
        get_db().execute("SELECT 1").fetchone()
        database_status = "ok"
    except Exception:  # any DB failure means the instance is not healthy
        database_status = "error"

    healthy = database_status == "ok"
    body = {
        "status": "ok" if healthy else "degraded",
        "database": database_status,
        "commit": current_app.config.get("APP_COMMIT", "unknown"),
        "uptime_seconds": int(time.time() - _STARTED_AT),
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    return jsonify(body), 200 if healthy else 503


@api_bp.route("/sessions", methods=["GET"])
def list_sessions():
    sessions = []
    for session in sessions_model.get_sessions():
        exercise_count = len(exercises_model.get_exercises_for_session(session["id"]))
        sessions.append(
            {
                "id": session["id"],
                "name": session["name"],
                "date": session["date"],
                "exercise_count": exercise_count,
            }
        )
    return jsonify(sessions=sessions), 200


@api_bp.route("/sessions", methods=["POST"])
def create_session():
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "")).strip()

    if not name:
        return jsonify(error="name is required"), 400

    session_id = sessions_model.start_session(name)
    return jsonify(id=session_id, name=name), 201


@api_bp.route("/sessions/<int:session_id>", methods=["GET"])
def session_detail(session_id):
    session = sessions_model.get_session_by_id(session_id)
    if not session:
        return jsonify(error="session not found"), 404

    exercises = [
        {
            "id": exercise["id"],
            "name": exercise["name"],
            "set_count": len(sets_model.get_sets_for_exercise(exercise["id"])),
        }
        for exercise in exercises_model.get_exercises_for_session(session_id)
    ]

    return (
        jsonify(
            id=session["id"],
            name=session["name"],
            date=session["date"],
            exercises=exercises,
        ),
        200,
    )


@api_bp.route("/sessions/<int:session_id>/exercises", methods=["GET"])
def list_exercises(session_id):
    session = sessions_model.get_session_by_id(session_id)
    if not session:
        return jsonify(error="session not found"), 404

    exercises = [
        {"id": exercise["id"], "name": exercise["name"]}
        for exercise in exercises_model.get_exercises_for_session(session_id)
    ]
    return jsonify(exercises=exercises), 200


@api_bp.route("/exercises/<int:exercise_id>/sets", methods=["GET"])
def list_sets(exercise_id):
    sets = [
        {"id": row["id"], "reps": row["reps"], "weight": row["weight"]}
        for row in sets_model.get_sets_for_exercise(exercise_id)
    ]
    return jsonify(sets=sets), 200


@api_bp.route("/exercises/<int:exercise_id>/sets", methods=["POST"])
def create_set(exercise_id):
    payload = request.get_json(silent=True) or {}
    weight = parse_weight(payload.get("weight"))
    reps = parse_positive_int(payload.get("reps"))

    if weight is None or reps is None:
        return jsonify(error="valid weight and reps are required"), 400

    set_id = sets_model.add_set(exercise_id, reps, weight)
    return jsonify(id=set_id, reps=reps, weight=weight), 201


@api_bp.route("/stats", methods=["GET"])
def stats():
    all_sessions = sessions_model.get_sessions()

    total_sessions = len(all_sessions)
    total_exercises = 0
    total_sets = 0

    for session in all_sessions:
        session_exercises = exercises_model.get_exercises_for_session(session["id"])
        total_exercises += len(session_exercises)
        for exercise in session_exercises:
            total_sets += len(sets_model.get_sets_for_exercise(exercise["id"]))

    return (
        jsonify(
            total_sessions=total_sessions,
            total_exercises=total_exercises,
            total_sets=total_sets,
        ),
        200,
    )
