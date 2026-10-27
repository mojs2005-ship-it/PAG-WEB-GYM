def test_add_set_get_shows_form(client, session_id, exercise_id):
    response = client.get(f"/sessions/{session_id}/exercises/{exercise_id}/add-set")
    assert response.status_code == 200
    assert b"Add Set" in response.data


def test_add_set_post_creates_and_redirects(client, session_id, exercise_id):
    response = client.post(
        f"/sessions/{session_id}/exercises/{exercise_id}/add-set",
        data={"weight": "185", "reps": "8"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["Location"] == f"/sessions/{session_id}/exercises/{exercise_id}"


def test_add_set_post_invalid_weight_shows_error(client, session_id, exercise_id):
    response = client.post(
        f"/sessions/{session_id}/exercises/{exercise_id}/add-set",
        data={"weight": "not-a-number", "reps": "8"},
    )
    assert response.status_code == 200
    assert b"Please enter valid weight and reps." in response.data


def test_add_set_post_negative_reps_shows_error(client, session_id, exercise_id):
    response = client.post(
        f"/sessions/{session_id}/exercises/{exercise_id}/add-set",
        data={"weight": "100", "reps": "-5"},
    )
    assert response.status_code == 200
    assert b"Please enter valid weight and reps." in response.data


def test_delete_set_removes_it(client, session_id, exercise_id):
    client.post(
        f"/sessions/{session_id}/exercises/{exercise_id}/add-set",
        data={"weight": "100", "reps": "10"},
    )

    detail = client.get(f"/sessions/{session_id}/exercises/{exercise_id}")
    # the "weight" column is REAL in SQLite, so it always round-trips as a float
    assert b"100.0 lbs" in detail.data

    # The freshly created set is the only row in the DB for this exercise.
    with client.application.app_context():
        from models.sets import get_sets_for_exercise

        set_id = get_sets_for_exercise(exercise_id)[0]["id"]

    response = client.post(
        f"/sessions/{session_id}/exercises/{exercise_id}/sets/{set_id}/delete",
        follow_redirects=False,
    )
    assert response.status_code == 302

    follow_up = client.get(f"/sessions/{session_id}/exercises/{exercise_id}")
    assert b"No sets logged yet." in follow_up.data
