def test_add_exercise_get_shows_form(client, session_id):
    response = client.get(f"/sessions/{session_id}/add-exercise")
    assert response.status_code == 200
    assert b"Add Exercise" in response.data


def test_add_exercise_get_unknown_session_returns_404(client):
    response = client.get("/sessions/999/add-exercise")
    assert response.status_code == 404


def test_add_exercise_post_creates_and_redirects(client, session_id):
    response = client.post(
        f"/sessions/{session_id}/add-exercise",
        data={"exercise_name": "Squat"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["Location"] == f"/sessions/{session_id}"


def test_add_exercise_post_empty_name_shows_error(client, session_id):
    response = client.post(
        f"/sessions/{session_id}/add-exercise", data={"exercise_name": ""}
    )
    assert response.status_code == 200
    assert b"Exercise name is required." in response.data


def test_exercise_detail_not_found_returns_404(client, session_id):
    response = client.get(f"/sessions/{session_id}/exercises/999")
    assert response.status_code == 404
    assert b"Exercise Not Found" in response.data


def test_exercise_detail_found_shows_name(client, session_id, exercise_id):
    response = client.get(f"/sessions/{session_id}/exercises/{exercise_id}")
    assert response.status_code == 200
    assert b"Bench Press" in response.data


def test_delete_exercise_removes_it(client, session_id, exercise_id):
    response = client.post(
        f"/sessions/{session_id}/exercises/{exercise_id}/delete",
        follow_redirects=False,
    )
    assert response.status_code == 302

    follow_up = client.get(f"/sessions/{session_id}/exercises/{exercise_id}")
    assert follow_up.status_code == 404
