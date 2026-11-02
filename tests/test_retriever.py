from app.rag.retriever import retrieve

import pytest


def test_retrieve_returns_matching_markdown_sections(tmp_path):
    (tmp_path / "guide.md").write_text(
        "# Segurança\n\n## Menor privilégio\nUsa permissões mínimas.\n\n"
        "## Backups\nTesta cópias de segurança.", encoding="utf-8"
    )
    results = retrieve("permissões mínimas", knowledge_dir=tmp_path)
    assert len(results) == 1
    assert results[0].title == "Menor privilégio"
    assert "permissões mínimas" in results[0].excerpt


def test_retrieve_empty_query_returns_no_sources(tmp_path):
    assert retrieve("   ", knowledge_dir=tmp_path) == []


def test_retrieve_missing_directory_returns_no_sources(tmp_path):
    assert retrieve("segurança", knowledge_dir=tmp_path / "missing") == []


def test_retrieve_uses_embedding_similarity(tmp_path):
    (tmp_path / "guide.md").write_text(
        "# Guia\n\n## Backups\nCópias de segurança e recuperação.\n\n"
        "## Permissões\nControlo de acesso e privilégios.", encoding="utf-8"
    )

    class FakeEmbedder:
        def embed(self, texts):
            assert len(texts) == 3
            return [[1.0, 0.0], [0.0, 1.0], [0.9, 0.1]]

    results = retrieve(
        "restaurar informação", knowledge_dir=tmp_path, embedder=FakeEmbedder()
    )
    assert results
    assert results[0].title == "Permissões"


def test_retrieve_rejects_wrong_embedding_count(tmp_path):
    (tmp_path / "guide.md").write_text(
        "# Guia\n\n## Backups\nCópias de segurança.", encoding="utf-8"
    )

    class FakeEmbedder:
        def embed(self, texts):
            return [[1.0, 0.0]]

    with pytest.raises(ValueError, match="Quantidade"):
        retrieve("recuperação", knowledge_dir=tmp_path, embedder=FakeEmbedder())


@pytest.mark.parametrize(
    "vectors",
    [
        [[1.0, 0.0], [0.0]],
        [[1.0, 0.0], [float("nan"), 1.0]],
        [[1.0, 0.0], [float("inf"), 1.0]],
        [[True, 0.0], [0.0, 1.0]],
    ],
)
def test_retrieve_rejects_invalid_embedding_vectors(tmp_path, vectors):
    (tmp_path / "guide.md").write_text(
        "# Guia\n\n## Backups\nCópias de segurança.", encoding="utf-8"
    )

    class FakeEmbedder:
        def embed(self, texts):
            return vectors

    with pytest.raises(ValueError, match="embeddings|Embeddings|Dimensões"):
        retrieve("recuperação", knowledge_dir=tmp_path, embedder=FakeEmbedder())


@pytest.mark.parametrize(
    ("query", "expected_path", "reference"),
    [
        (
            "SSDF desenvolvimento seguro software",
            "knowledge/secure-development.md",
            "https://csrc.nist.gov/pubs/sp/800/218/final",
        ),
        (
            "NIST resposta incidentes gestão risco",
            "knowledge/incident-response.md",
            "https://csrc.nist.gov/pubs/sp/800/61/r3/final",
        ),
        (
            "OWASP riscos aplicações web versão 2025",
            "knowledge/application-security.md",
            "https://owasp.org/projects/top-ten/",
        ),
    ],
)
def test_retrieve_curated_security_knowledge_and_references(
    query, expected_path, reference
):
    results = retrieve(query)

    assert results
    # The expected source must rank first, not merely appear somewhere in top-k.
    assert results[0].path == expected_path
    assert reference in results[0].excerpt
