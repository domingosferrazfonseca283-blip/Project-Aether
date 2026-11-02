"""Testes determinísticos do adaptador HTTP de embeddings Ollama."""
import httpx
import pytest

from app.core.config import Settings
from app.rag.embeddings import OllamaEmbedder, OllamaEmbeddingError


def _install_transport(monkeypatch, handler):
    original_client = httpx.Client

    def client_factory(timeout):
        return original_client(
            transport=httpx.MockTransport(handler),
            timeout=timeout,
        )

    monkeypatch.setattr(httpx, "Client", client_factory)


def _json_response(request):
    return httpx.Response(200, json={"embeddings": [[0.1, 0.2], [0.3, 0.4]]})


def test_ollama_embedder_returns_vectors_and_sends_expected_request(monkeypatch):
    requests = []

    def handler(request):
        requests.append(request)
        return _json_response(request)

    _install_transport(monkeypatch, handler)
    settings = Settings(ollama_timeout_seconds=5)
    result = OllamaEmbedder(settings).embed(["query", "document"])

    assert result == [[0.1, 0.2], [0.3, 0.4]]
    assert len(requests) == 1
    assert requests[0].method == "POST"
    assert requests[0].url == "http://127.0.0.1:11434/api/embed"
    assert requests[0].read()["model"] == "nomic-embed-text"
    assert requests[0].read()["input"] == ["query", "document"]


@pytest.mark.parametrize(
    "embeddings",
    [
        [[0.1]],
        [[0.1, float("nan")], [0.2, 0.3]],
        [[0.1, float("inf")], [0.2, 0.3]],
        [[0.1, 0.2], [0.3]],
        [[True, 0.2], [0.3, 0.4]],
        [[], [0.3, 0.4]],
        {"unexpected": "shape"},
    ],
)
def test_ollama_embedder_rejects_invalid_vectors(monkeypatch, embeddings):
    def handler(request):
        return httpx.Response(200, json={"embeddings": embeddings})

    _install_transport(monkeypatch, handler)
    with pytest.raises(OllamaEmbeddingError):
        OllamaEmbedder(Settings()).embed(["one", "two"])


def test_ollama_embedder_rejects_wrong_vector_count(monkeypatch):
    _install_transport(
        monkeypatch,
        lambda request: httpx.Response(200, json={"embeddings": [[0.1, 0.2]]}),
    )
    with pytest.raises(OllamaEmbeddingError):
        OllamaEmbedder(Settings()).embed(["one", "two"])


def test_ollama_embedder_wraps_http_status_errors(monkeypatch):
    _install_transport(
        monkeypatch,
        lambda request: httpx.Response(503, json={"error": "unavailable"}),
    )
    with pytest.raises(OllamaEmbeddingError) as error:
        OllamaEmbedder(Settings()).embed(["query"])
    assert isinstance(error.value.__cause__, httpx.HTTPStatusError)


def test_ollama_embedder_wraps_timeout_errors(monkeypatch):
    def handler(request):
        raise httpx.ReadTimeout("simulated timeout", request=request)

    _install_transport(monkeypatch, handler)
    with pytest.raises(OllamaEmbeddingError) as error:
        OllamaEmbedder(Settings(ollama_timeout_seconds=1)).embed(["query"])
    assert isinstance(error.value.__cause__, httpx.ReadTimeout)


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(200, content=b"{"),
        httpx.Response(200, json={"unexpected": []}),
        httpx.Response(200, json={"embeddings": None}),
    ],
)
def test_ollama_embedder_wraps_malformed_responses(monkeypatch, response):
    _install_transport(monkeypatch, lambda request: response)
    with pytest.raises(OllamaEmbeddingError):
        OllamaEmbedder(Settings()).embed(["query"])


@pytest.mark.parametrize("texts", [[], [""], ["  "], ["valid", ""]])
def test_ollama_embedder_rejects_empty_input(texts):
    with pytest.raises(OllamaEmbeddingError):
        OllamaEmbedder(Settings()).embed(texts)
