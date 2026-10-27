def test_api_create_session(client):
    response = client.post("/api/sessions", json={"name": "Cardio Day"})
    assert response.status_code == 201
    body = response.get_json()
    assert body["name"] == "Cardio Day"
    assert "id" in body


def test_api_create_session_missing_name_returns_400(client):
    response = client.post("/api/sessions", json={})
    assert response.status_code == 400
    assert response.get_json()["error"] == "name is required"


def test_api_list_sessions(client):
    client.post("/api/sessions", json={"name": "Cardio Day"})
    response = client.get("/api/sessions")
    assert response.status_code == 200
    body = response.get_json()
    assert len(body["sessions"]) == 1
    assert body["sessions"][0]["name"] == "Cardio Day"


def test_api_session_detail_json(client, session_id, exercise_id):
    response = client.get(f"/api/sessions/{session_id}")
    assert response.status_code == 200
    body = response.get_json()
    assert body["id"] == session_id
    assert body["exercises"][0]["name"] == "Bench Press"


def test_api_session_not_found_returns_404(client):
    response = client.get("/api/sessions/999")
    assert response.status_code == 404
    assert response.get_json()["error"] == "session not found"


def test_api_create_set(client, exercise_id):
    response = client.post(
        f"/api/exercises/{exercise_id}/sets", json={"weight": 95, "reps": 12}
    )
    assert response.status_code == 201
    body = response.get_json()
    assert body["weight"] == 95
    assert body["reps"] == 12


def test_api_create_set_invalid_payload_returns_400(client, exercise_id):
    response = client.post(
        f"/api/exercises/{exercise_id}/sets", json={"weight": "bad", "reps": 12}
    )
    assert response.status_code == 400


def test_api_list_sets(client, exercise_id):
    client.post(f"/api/exercises/{exercise_id}/sets", json={"weight": 50, "reps": 10})
    response = client.get(f"/api/exercises/{exercise_id}/sets")
    assert response.status_code == 200
    assert len(response.get_json()["sets"]) == 1


def test_api_stats(client, session_id, exercise_id):
    client.post(f"/api/exercises/{exercise_id}/sets", json={"weight": 50, "reps": 10})
    response = client.get("/api/stats")
    assert response.status_code == 200
    body = response.get_json()
    assert body == {"total_sessions": 1, "total_exercises": 1, "total_sets": 1}
