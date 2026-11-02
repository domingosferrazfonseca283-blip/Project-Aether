import httpx
import pytest

from app.core.config import Settings
from app.rag.embeddings import OllamaEmbedder, OllamaEmbeddingError


def _mock_client(monkeypatch, embeddings):
    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {"embeddings": embeddings}

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


def test_ollama_embedder_returns_vectors(monkeypatch):
    _mock_client(monkeypatch, [[0.1, 0.2], [0.3, 0.4]])
    settings = Settings(ollama_timeout_seconds=5)
    assert OllamaEmbedder(settings).embed(["query", "document"]) == [
        [0.1, 0.2], [0.3, 0.4]
    ]


@pytest.mark.parametrize(
    "embeddings",
    [
        [[0.1]],
        [[0.1, float("nan")], [0.2, 0.3]],
        [[0.1, float("inf")], [0.2, 0.3]],
        [[0.1, 0.2], [0.3]],
        [[True, 0.2], [0.3, 0.4]],
    ],
)
def test_ollama_embedder_rejects_invalid_vectors(monkeypatch, embeddings):
    _mock_client(monkeypatch, embeddings)
    with pytest.raises(OllamaEmbeddingError):
        OllamaEmbedder(Settings()).embed(["one", "two"])


def test_ollama_embedder_rejects_empty_input():
    with pytest.raises(OllamaEmbeddingError):
        OllamaEmbedder(Settings()).embed([""])
