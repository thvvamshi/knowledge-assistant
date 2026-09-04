from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_get_providers():
    response = client.get("/api/providers")

    assert response.status_code == 200

    data = response.json()

    assert data["default_provider"] == "ollama"
    assert len(data["providers"]) == 2

    ollama = next(
        provider
        for provider in data["providers"]
        if provider["id"] == "ollama"
    )

    anthropic = next(
        provider
        for provider in data["providers"]
        if provider["id"] == "anthropic"
    )

    assert ollama["configured"] is True
    assert ollama["available"] is True
    assert ollama["model"] == "gemma3:4b"

    assert anthropic["configured"] is False
    assert anthropic["available"] is False
