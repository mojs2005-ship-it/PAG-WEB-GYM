from flask import Blueprint, render_template

from models import exercises as exercises_model
from models import sessions as sessions_model
from models import sets as sets_model

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    all_sessions = sessions_model.get_sessions()

    total_sessions = len(all_sessions)
    total_exercises = 0
    total_sets = 0

    for session in all_sessions:
        session_exercises = exercises_model.get_exercises_for_session(session["id"])
        total_exercises += len(session_exercises)

        for exercise in session_exercises:
            total_sets += len(sets_model.get_sets_for_exercise(exercise["id"]))

    return render_template(
        "index.html",
        total_sessions=total_sessions,
        total_exercises=total_exercises,
        total_sets=total_sets,
    )
