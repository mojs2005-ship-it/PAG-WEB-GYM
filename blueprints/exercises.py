from flask import Blueprint, redirect, render_template, request

from models import exercises as exercises_model
from models import sessions as sessions_model
from models import sets as sets_model

exercises_bp = Blueprint("exercises", __name__)


@exercises_bp.route("/sessions/<int:session_id>/add-exercise", methods=["GET", "POST"])
def add_exercise(session_id):
    selected_session = sessions_model.get_session_by_id(session_id)
    if not selected_session:
        return "Session Not Found", 404

    workout_title = selected_session["name"]

    if request.method == "POST":
        exercise_name = request.form.get("exercise_name", "").strip()

        if not exercise_name:
            return render_template(
                "add_exercise.html",
                error="Exercise name is required.",
                workout_title=workout_title,
                session_id=session_id,
            )

        exercises_model.add_exercise(session_id, exercise_name)
        return redirect(f"/sessions/{session_id}")

    return render_template("add_exercise.html", workout_title=workout_title, session_id=session_id)


@exercises_bp.route("/sessions/<int:session_id>/exercises/<int:exercise_id>")
def exercise_detail(session_id, exercise_id):
    selected_exercise = exercises_model.get_exercise_by_id(session_id, exercise_id)

    if not selected_exercise:
        return "Exercise Not Found", 404

    sets = sets_model.get_sets_for_exercise(exercise_id)

    return render_template(
        "exercise_detail.html",
        exercise_name=selected_exercise["name"],
        session_id=session_id,
        exercise_id=exercise_id,
        sets=sets,
    )


@exercises_bp.route(
    "/sessions/<int:session_id>/exercises/<int:exercise_id>/delete", methods=["POST"]
)
def delete_exercise(session_id, exercise_id):
    exercises_model.delete_exercise(exercise_id)
    return redirect(f"/sessions/{session_id}")
