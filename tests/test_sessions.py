def test_add_session_get_shows_form(client):
    response = client.get("/add-session")
    assert response.status_code == 200
    assert b"Add Workout Session" in response.data


def test_add_session_post_creates_session_and_redirects(client):
    response = client.post(
        "/add-session", data={"session_name": "Leg Day"}, follow_redirects=False
    )
    assert response.status_code == 302
    assert response.headers["Location"] == "/sessions"


def test_add_session_post_empty_name_shows_error(client):
    response = client.post("/add-session", data={"session_name": "   "})
    assert response.status_code == 200
    assert b"Session name is required." in response.data


def test_sessions_list_shows_created_session(client):
    client.post("/add-session", data={"session_name": "Pull Day"})
    response = client.get("/sessions")
    assert response.status_code == 200
    assert b"Pull Day" in response.data


def test_sessions_list_empty_state(client):
    response = client.get("/sessions")
    assert response.status_code == 200
    assert b"No workout sessions yet." in response.data


def test_session_detail_not_found_returns_404(client):
    response = client.get("/sessions/999")
    assert response.status_code == 404
    assert b"Session Not Found" in response.data


def test_session_detail_found_shows_title(client, session_id):
    response = client.get(f"/sessions/{session_id}")
    assert response.status_code == 200
    assert b"Push Day" in response.data


def test_delete_session_removes_it(client, session_id):
    response = client.post(f"/sessions/{session_id}/delete", follow_redirects=False)
    assert response.status_code == 302

    follow_up = client.get(f"/sessions/{session_id}")
    assert follow_up.status_code == 404
