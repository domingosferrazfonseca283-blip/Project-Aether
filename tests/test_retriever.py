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


def test_retrieve_returns_no_sources_for_unrelated_query(tmp_path):
    (tmp_path / "guide.md").write_text(
        "# Guia\n\n## Backups\nCópias de segurança e recuperação.",
        encoding="utf-8",
    )

    assert retrieve("astronomia planetas telescópios", knowledge_dir=tmp_path) == []


def test_retrieve_uses_stable_order_for_equal_lexical_scores(tmp_path):
    (tmp_path / "b-guide.md").write_text(
        "# Guia B\n\n## Segurança B\nPrincípios de segurança.",
        encoding="utf-8",
    )
    (tmp_path / "a-guide.md").write_text(
        "# Guia A\n\n## Segurança A\nPrincípios de segurança.",
        encoding="utf-8",
    )

    results = retrieve("segurança princípios", knowledge_dir=tmp_path, limit=1)

    assert len(results) == 1
    assert results[0].path == "knowledge/a-guide.md"


def test_retrieve_returns_no_embedding_results_when_similarity_is_zero(tmp_path):
    (tmp_path / "guide.md").write_text(
        "# Guia\n\n## Backups\nCópias de segurança.",
        encoding="utf-8",
    )

    class ZeroEmbedder:
        def embed(self, texts):
            return [[0.0, 0.0] for _ in texts]

    assert retrieve(
        "consulta sem correspondência",
        knowledge_dir=tmp_path,
        embedder=ZeroEmbedder(),
    ) == []


def test_retrieve_prioritizes_matching_section_titles(tmp_path):
    (tmp_path / "a-general.md").write_text(
        "# Guia geral\n\n## Introdução\n"
        "Este texto aborda resposta, incidentes e gestão de incidentes "
        "com vários detalhes adicionais.",
        encoding="utf-8",
    )
    (tmp_path / "z-specific.md").write_text(
        "# Guia\n\n## Resposta a incidentes\n"
        "Segue o plano documentado.",
        encoding="utf-8",
    )

    results = retrieve(
        "resposta incidentes", knowledge_dir=tmp_path, limit=2
    )

    assert results
    assert results[0].path == "knowledge/z-specific.md"


def test_retrieve_rewards_exact_multiword_phrase(tmp_path):
    (tmp_path / "a-guide.md").write_text(
        "# Guia\n\n## Operações\n"
        "A resposta rápida ajuda a gerir incidentes.",
        encoding="utf-8",
    )
    (tmp_path / "b-guide.md").write_text(
        "# Guia\n\n## Resposta a incidentes\n"
        "Plano de resposta a incidentes.",
        encoding="utf-8",
    )

    results = retrieve(
        "resposta a incidentes", knowledge_dir=tmp_path, limit=2
    )

    assert results
    assert results[0].path == "knowledge/b-guide.md"

@pytest.mark.parametrize(
    ("query", "expected_path"),
    [
        (
            "menor privilégio permissões mínimas",
            "knowledge/security-basics.md",
        ),
        (
            "autenticação multifator autorização servidor",
            "knowledge/application-security.md",
        ),
        (
            "cadeia fornecimento dependências software",
            "knowledge/secure-development.md",
        ),
        (
            "contenção recuperação comunicação incidentes",
            "knowledge/incident-response.md",
        ),
    ],
)
def test_retrieve_ranks_additional_defensive_topics_first(query, expected_path):
    results = retrieve(query)

    assert results
    assert results[0].path == expected_path


def test_retrieve_respects_requested_result_limit(tmp_path):
    (tmp_path / "guide.md").write_text(
        "# Segurança\\n\\n"
        "## Autenticação\\nAutenticação multifator e sessões seguras.\\n\\n"
        "## Autorização\\nAutorização no servidor e menor privilégio.\\n\\n"
        "## Registos\\nRegistos de segurança e monitorização.",
        encoding="utf-8",
    )

    results = retrieve("segurança autenticação autorização registos", knowledge_dir=tmp_path, limit=2)

    assert len(results) == 2

