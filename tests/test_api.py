"""Testes de contrato da API inicial do Project Aether."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_returns_project_metadata() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["project"] == "Project Aether"
    assert response.json()["version"] == "0.1.0"


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_returns_safe_starter_guidance() -> None:
    response = client.post(
        "/analyze",
        json={"content": "Como posso organizar este projeto?", "category": "programming"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["category"] == "programming"
    assert body["status"] == "starter_mode"
    assert len(body["guidance"]) >= 3


def test_analyze_rejects_empty_content() -> None:
    response = client.post("/analyze", json={"content": "", "category": "general"})

    assert response.status_code == 422


def test_analyze_rejects_unknown_category() -> None:
    response = client.post(
        "/analyze",
        json={"content": "Pedido de teste", "category": "unknown"},
    )

    assert response.status_code == 422
