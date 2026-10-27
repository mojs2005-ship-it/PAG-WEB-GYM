import blueprints.api as api_module


def test_health_returns_ok_with_expected_fields(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert body["uptime_seconds"] >= 0
    assert "timestamp" in body
    assert "commit" in body


def test_health_reports_configured_commit(app, client):
    app.config["APP_COMMIT"] = "abc1234"
    response = client.get("/api/health")
    assert response.get_json()["commit"] == "abc1234"


def test_health_returns_503_when_database_fails(client, monkeypatch):
    def broken_db():
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(api_module, "get_db", broken_db)

    response = client.get("/api/health")
    assert response.status_code == 503
    body = response.get_json()
    assert body["status"] == "degraded"
    assert body["database"] == "error"
