import httpx
import pytest

from app.core.config import Settings
from app.rag.embeddings import OllamaEmbedder, OllamaEmbeddingError


def test_ollama_embedder_returns_vectors(monkeypatch):
    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {"embeddings": [[0.1, 0.2], [0.3, 0.4]]}

    class Client:
        def __init__(self, timeout):
            assert timeout == 5

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def post(self, url, json):
            assert url.endswith("/api/embed")
            assert json == {"model": "nomic-embed-text", "input": ["query", "document"]}
            return Response()

    monkeypatch.setattr(httpx, "Client", Client)
    settings = Settings(ollama_timeout_seconds=5)
    assert OllamaEmbedder(settings).embed(["query", "document"]) == [
        [0.1, 0.2], [0.3, 0.4]
    ]


def test_ollama_embedder_rejects_invalid_response(monkeypatch):
    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {"embeddings": [[0.1]]}

    class Client:
        def __init__(self, timeout):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def post(self, url, json):
            return Response()

    monkeypatch.setattr(httpx, "Client", Client)
    with pytest.raises(OllamaEmbeddingError):
        OllamaEmbedder(Settings()).embed(["one", "two"])


def test_ollama_embedder_rejects_empty_input():
    with pytest.raises(OllamaEmbeddingError):
        OllamaEmbedder(Settings()).embed([""])
