def test_home_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Gym Log Web" in response.data


def test_home_page_shows_zero_stats_when_empty(client):
    response = client.get("/")
    assert b">0<" in response.data


def test_home_page_reflects_created_data(client, exercise_id, session_id):
    client.post(
        f"/sessions/{session_id}/exercises/{exercise_id}/add-set",
        data={"weight": "135", "reps": "5"},
    )

    response = client.get("/")
    assert response.status_code == 200
    # one session, one exercise, one set were created via the fixtures
    assert b">1<" in response.data
