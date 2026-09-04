from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


async def async_true():
    return True


async def async_false():
    return False


def test_health_reports_all_dependencies_ok(monkeypatch):
    monkeypatch.setattr(
        "app.main._check_database",
        async_true,
    )
    monkeypatch.setattr(
        "app.main._check_ollama",
        async_true,
    )
    monkeypatch.setattr(
        "app.main._check_vector_index",
        async_true,
    )

    response = client.get("/api/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["dependencies"]["database"] == "ok"
    assert data["dependencies"]["ollama"] == "ok"
    assert data["dependencies"]["vector_index"] == "ok"


def test_health_reports_degraded_when_ollama_is_unavailable(monkeypatch):
    monkeypatch.setattr(
        "app.main._check_database",
        async_true,
    )
    monkeypatch.setattr(
        "app.main._check_ollama",
        async_false,
    )
    monkeypatch.setattr(
        "app.main._check_vector_index",
        async_true,
    )

    response = client.get("/api/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "degraded"
    assert data["dependencies"]["database"] == "ok"
    assert data["dependencies"]["ollama"] == "unavailable"
    assert data["dependencies"]["vector_index"] == "ok"


def test_readiness_returns_ready_when_database_is_available(monkeypatch):
    monkeypatch.setattr(
        "app.main._check_database",
        async_true,
    )

    response = client.get("/api/health/ready")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ready"
    assert data["database"] == "ok"


def test_readiness_returns_not_ready_when_database_is_unavailable(monkeypatch):
    monkeypatch.setattr(
        "app.main._check_database",
        async_false,
    )

    response = client.get("/api/health/ready")

    assert response.status_code == 503

    data = response.json()

    assert data["status"] == "not_ready"
    assert data["database"] == "unavailable"


def test_health_includes_request_id():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.headers.get("x-request-id")


def test_cors_allows_frontend_origin():
    response = client.get(
        "/api/health",
        headers={
            "Origin": "http://localhost:3000",
        },
    )

    assert response.status_code == 200
    assert (
        response.headers.get("access-control-allow-origin")
        == "http://localhost:3000"
    )
