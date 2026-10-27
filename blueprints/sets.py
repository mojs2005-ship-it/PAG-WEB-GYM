from flask import Blueprint, redirect, render_template, request

from models import exercises as exercises_model
from models import sets as sets_model
from services import parse_positive_int, parse_weight

sets_bp = Blueprint("sets", __name__)


@sets_bp.route(
    "/sessions/<int:session_id>/exercises/<int:exercise_id>/add-set",
    methods=["GET", "POST"],
)
def add_set(session_id, exercise_id):
    selected_exercise = exercises_model.get_exercise_by_id(session_id, exercise_id)
    if not selected_exercise:
        return "Exercise Not Found", 404

    exercise_name = selected_exercise["name"]

    if request.method == "POST":
        weight = parse_weight(request.form.get("weight"))
        reps = parse_positive_int(request.form.get("reps"))

        if weight is None or reps is None:
            return render_template(
                "add_set.html",
                error="Please enter valid weight and reps.",
                exercise_name=exercise_name,
                session_id=session_id,
                exercise_id=exercise_id,
            )

        sets_model.add_set(exercise_id, reps, weight)
        return redirect(f"/sessions/{session_id}/exercises/{exercise_id}")

    return render_template(
        "add_set.html",
        exercise_name=exercise_name,
        session_id=session_id,
        exercise_id=exercise_id,
    )


@sets_bp.route(
    "/sessions/<int:session_id>/exercises/<int:exercise_id>/sets/<int:set_id>/delete",
    methods=["POST"],
)
def delete_set(session_id, exercise_id, set_id):
    sets_model.delete_set(set_id)
    return redirect(f"/sessions/{session_id}/exercises/{exercise_id}")
