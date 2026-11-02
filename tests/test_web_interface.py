"""Testes da interface web estática do Project Aether."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_web_interface_is_served_with_security_headers() -> None:
    response = client.get("/ui")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Project Aether" in response.text
    assert 'id="analysis-form"' in response.text
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"


def test_web_assets_are_served() -> None:
    response = client.get("/static/app.js")

    assert response.status_code == 200
    assert "text/javascript" in response.headers["content-type"]
    assert 'textContent' in response.text
    assert "innerHTML" not in response.text
    assert "localStorage" not in response.text
