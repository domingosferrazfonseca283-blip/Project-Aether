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
