from flask import Blueprint, redirect, render_template, request

from models import exercises as exercises_model
from models import sessions as sessions_model
from models import sets as sets_model

sessions_bp = Blueprint("sessions", __name__)


@sessions_bp.route("/sessions")
def sessions_list():
    workout_sessions = []

    for session in sessions_model.get_sessions():
        session_exercises = exercises_model.get_exercises_for_session(session["id"])
        workout_sessions.append(
            {
                "id": session["id"],
                "name": session["name"],
                "date": session["date"],
                "exercise_count": len(session_exercises),
            }
        )

    return render_template("sessions.html", workout_sessions=workout_sessions)


@sessions_bp.route("/sessions/<int:session_id>")
def session_detail(session_id):
    selected_session = sessions_model.get_session_by_id(session_id)

    if not selected_session:
        return "Session Not Found", 404

    exercises_with_counts = []
    for exercise in exercises_model.get_exercises_for_session(session_id):
        set_count = len(sets_model.get_sets_for_exercise(exercise["id"]))
        exercises_with_counts.append(
            {"id": exercise["id"], "name": exercise["name"], "set_count": set_count}
        )

    return render_template(
        "session_detail.html",
        workout_title=selected_session["name"],
        exercises=exercises_with_counts,
        session_id=session_id,
        session_date=selected_session["date"],
    )


@sessions_bp.route("/add-session", methods=["GET", "POST"])
def add_session():
    if request.method == "POST":
        session_name = request.form.get("session_name", "").strip()

        if not session_name:
            return render_template("add_session.html", error="Session name is required.")

        sessions_model.start_session(session_name)
        return redirect("/sessions")

    return render_template("add_session.html")


@sessions_bp.route("/sessions/<int:session_id>/delete", methods=["POST"])
def delete_session(session_id):
    sessions_model.delete_session(session_id)
    return redirect("/sessions")
