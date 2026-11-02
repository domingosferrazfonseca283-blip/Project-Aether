"""Testes de contrato da API inicial do Project Aether."""
import pytest

from fastapi.testclient import TestClient

from app.main import app
from app.rag.embeddings import OllamaEmbeddingError

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
    response = client.post(
        "/analyze", json={"content": "", "category": "general"}
    )

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
        OllamaEmbeddingError("serviço indisponível"),
        ValueError("vetores inválidos"),
    ],
)
def test_analyze_falls_back_to_lexical_retrieval(
    tmp_path, monkeypatch, embedding_error
):
    import app.main as main
    from app.rag.retriever import retrieve as real_retrieve

    (tmp_path / "guide.md").write_text(
        "\n".join(
            [
                "# Segurança",
                "",
                "## Menor privilégio",
                "Aplicar permissões mínimas e controlo de acesso.",
            ]
        ),
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
    assert calls == [main.embedder, None]
    sources = response.json()["sources"]
    assert sources
    assert sources[0]["path"] == "knowledge/guide.md"
    assert sources[0]["title"] == "Menor privilégio"


def test_analyze_returns_controlled_503_when_ollama_is_unavailable(monkeypatch, caplog):
    import app.main as main
    from app.ai.ollama_provider import OllamaProviderError

    class UnavailableProvider:
        name = "ollama_local"

        def analyze(self, content, category, context=""):
            raise OllamaProviderError(
                "Falha interna: token=super-secret e endpoint=http://internal.local"
            )

    monkeypatch.setattr(main, "provider", UnavailableProvider())
    response = client.post(
        "/analyze",
        json={"content": "Explica como proteger uma API.", "category": "cybersecurity"},
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Não foi possível obter resposta do modelo local."
    }
    assert "super-secret" not in response.text
    assert "internal.local" not in response.text
    assert "analysis_provider_unavailable" in caplog.text
    assert response.headers["X-Request-ID"] in caplog.text
    assert "OllamaProviderError" in caplog.text
    assert "super-secret" not in caplog.text
    assert "internal.local" not in caplog.text
    assert response.headers["X-Request-ID"]
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_analyze_passes_retrieved_context_to_ai_provider(monkeypatch):
    import app.main as main

    captured = {}

    class CapturingProvider:
        name = "ollama_local"

        def analyze(self, content, category, context=""):
            captured.update(
                content=content,
                category=category,
                context=context,
            )
            return ["Resposta baseada no contexto recuperado."]

    monkeypatch.setattr(main, "provider", CapturingProvider())
    response = client.post(
        "/analyze",
        json={
            "content": "Como aplicar o princípio do menor privilégio?",
            "category": "cybersecurity",
        },
    )

    assert response.status_code == 200
    assert response.json()["guidance"] == [
        "Resposta baseada no contexto recuperado."
    ]
    assert captured["content"] == "Como aplicar o princípio do menor privilégio?"
    assert captured["category"] == "cybersecurity"
    assert "knowledge/" in captured["context"]
    assert "Princípio do menor privilégio" in captured["context"]
    assert response.json()["sources"]


def test_analyze_marks_context_empty_when_no_sources_are_retrieved(monkeypatch):
    import app.main as main

    captured = {}

    class CapturingProvider:
        name = "ollama_local"

        def analyze(self, content, category, context=""):
            captured["context"] = context
            return ["Não foram recuperadas fontes para esta pergunta."]

    monkeypatch.setattr(main, "retrieve", lambda query, embedder=None: [])
    monkeypatch.setattr(main, "provider", CapturingProvider())

    response = client.post(
        "/analyze",
        json={
            "content": "Pergunta sem correspondência na base documental.",
            "category": "cybersecurity",
        },
    )

    assert response.status_code == 200
    assert response.json()["sources"] == []
    assert captured["context"] == ""
    assert response.json()["guidance"] == [
        "Não foram recuperadas fontes para esta pergunta."
    ]

