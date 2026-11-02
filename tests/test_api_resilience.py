"""Testes de robustez do contrato HTTP da API."""
import pytest
from fastapi.testclient import TestClient

import app.main as main
from app.ai.ollama_provider import OllamaProviderError
from app.rag.embeddings import OllamaEmbeddingError


client = TestClient(main.app)


def test_analyze_rejects_whitespace_only_content():
    response = client.post("/analyze", json={"content": "   "})
    assert response.status_code == 422


def test_analyze_rejects_content_over_limit():
    response = client.post("/analyze", json={"content": "a" * 20_001})
    assert response.status_code == 422


def test_analyze_accepts_content_at_limit():
    response = client.post("/analyze", json={"content": "a" * 20_000})
    assert response.status_code == 200


def test_analyze_uses_default_category():
    response = client.post("/analyze", json={"content": "Explica testes unitários"})
    assert response.status_code == 200
    assert response.json()["category"] == "general"


def test_analyze_falls_back_to_lexical_when_embeddings_fail(monkeypatch):
    class BrokenEmbedder:
        def embed(self, texts):
            raise OllamaEmbeddingError("serviço indisponível")

    monkeypatch.setattr(main, "embedder", BrokenEmbedder())
    response = client.post(
        "/analyze",
        json={
            "content": "Como aplicar o princípio do menor privilégio e permissões?",
            "category": "cybersecurity",
        },
    )
    assert response.status_code == 200
    assert response.json()["sources"]
    assert any("menor" in source["title"].lower() for source in response.json()["sources"])


def test_analyze_returns_503_when_chat_provider_is_unavailable(monkeypatch):
    class BrokenProvider:
        name = "ollama_local"

        def analyze(self, content, category, context=""):
            raise OllamaProviderError("serviço local indisponível")

    monkeypatch.setattr(main, "provider", BrokenProvider())
    response = client.post(
        "/analyze",
        json={"content": "Explica o princípio do menor privilégio"},
    )
    assert response.status_code == 503
    assert response.json()["detail"] == "Não foi possível obter resposta do modelo local."
    assert "serviço local indisponível" not in response.text
    assert response.headers["X-Request-ID"]
    assert response.headers["Cache-Control"] == "no-store"
