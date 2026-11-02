"""Testes de contrato da API inicial do Project Aether."""
import pytest

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_returns_project_metadata() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["project"] == "Kamba"
    assert response.json()["version"] == "0.6.0"
    assert response.json()["previous_project_name"] == "Project Aether"


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
    assert body["provider"] == "rule_based"
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


def test_cybersecurity_category_returns_defensive_guidance() -> None:
    response = client.post(
        "/analyze",
        json={"content": "Como proteger a minha aplicação?", "category": "cybersecurity"},
    )

    assert response.status_code == 200
    guidance = " ".join(response.json()["guidance"]).lower()
    assert "autorização" in guidance


def test_analyze_returns_retrieved_sources():
    response = client.post(
        "/analyze",
        json={"content": "Como aplicar o princípio do menor privilégio?", "category": "cybersecurity"},
    )

    assert response.status_code == 200
    sources = response.json()["sources"]
    assert sources
    assert sources[0]["source_id"].startswith("security-basics.md#")
    assert sources[0]["path"].startswith("knowledge/")
    assert sources[0]["title"]
    assert sources[0]["excerpt"]
    assert sources[0]["reference"].startswith("Ver referências")


@pytest.mark.parametrize(
    "embedding_error",
    [
        __import__("app.rag.embeddings", fromlist=["OllamaEmbeddingError"]).OllamaEmbeddingError(
            "serviço indisponível"
        ),
        ValueError("vetores inválidos"),
    ],
)
def test_analyze_falls_back_to_lexical_retrieval(
    tmp_path, monkeypatch, embedding_error
):
    import app.main as main
    from app.rag.retriever import retrieve as real_retrieve

    (tmp_path / "guide.md").write_text(
        "# Segurança\\n\\n## Menor privilégio\\n"
        "Aplicar permissões mínimas e controlo de acesso.",
        encoding="utf-8",
    )

    class FailingEmbedder:
        def embed(self, texts):
            raise embedding_error

    calls = []

    def tracked_retrieve(query, embedder=None):
        calls.append(embedder)
        return real_retrieve(
            query, knowledge_dir=tmp_path, embedder=embedder
        )

    monkeypatch.setattr(main, "embedder", FailingEmbedder())
    monkeypatch.setattr(main, "retrieve", tracked_retrieve)

    response = client.post(
        "/analyze",
        json={
            "content": "Como aplicar permissões mínimas?",
            "category": "cybersecurity",
        },
    )

    assert response.status_code == 200
    assert calls[0] is not None
    assert calls[1] is None
    sources = response.json()["sources"]
    assert sources
    assert sources[0]["path"] == "knowledge/guide.md"
    assert sources[0]["title"] == "Menor privilégio"
