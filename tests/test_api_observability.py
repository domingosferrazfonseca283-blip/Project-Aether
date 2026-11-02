"""Testes de observabilidade sem exposição do conteúdo dos pedidos."""
import logging
from uuid import UUID

from fastapi.testclient import TestClient

import app.main as main


client = TestClient(main.app)


def test_response_includes_server_generated_request_id():
    response = client.get("/", headers={"X-Request-ID": "client-controlled"})

    assert response.status_code == 200
    request_id = response.headers["X-Request-ID"]
    UUID(request_id)
    assert request_id != "client-controlled"


def test_security_headers_are_present_on_api_responses():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert response.headers["Permissions-Policy"] == (
        "camera=(), microphone=(), geolocation=()"
    )


def test_analysis_response_disables_caching():
    response = client.post("/analyze", json={"content": "texto de teste"})

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"


def test_logs_metadata_without_request_content(caplog):
    secret_text = "texto-privado-nao-deve-ser-registado"
    caplog.set_level(logging.INFO, logger="project_aether.api")

    response = client.post("/analyze", json={"content": secret_text})

    assert response.status_code == 200
    assert "request_completed" in caplog.text
    assert "POST" in caplog.text
    assert "/analyze" in caplog.text
    assert "status_code=200" in caplog.text
    assert response.headers["X-Request-ID"] in caplog.text
    assert secret_text not in caplog.text


def test_unavailable_provider_logs_safe_error_metadata(monkeypatch, caplog):
    class BrokenProvider:
        name = "ollama_local"

        def analyze(self, content, category, context=""):
            raise main.OllamaProviderError("falha de serviço")

    monkeypatch.setattr(main, "provider", BrokenProvider())
    caplog.set_level(logging.INFO, logger="project_aether.api")

    response = client.post("/analyze", json={"content": "conteúdo confidencial"})

    assert response.status_code == 503
    assert "request_completed" in caplog.text
    assert "status_code=503" in caplog.text
    assert "conteúdo confidencial" not in caplog.text
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"

def test_validation_errors_do_not_echo_submitted_content():
    private_text = "conteudo-privado-que-nao-deve-ser-repetido"
    response = client.post("/analyze", json={"content": private_text, "category": "invalid"})

    assert response.status_code == 422
    assert private_text not in response.text
    assert response.json()["detail"]
    assert response.headers.get("X-Request-ID")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    error = response.json()["detail"][0]
    assert error["loc"] == ["body", "category"]
    assert "input" not in error

