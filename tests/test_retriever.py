from app.rag.retriever import retrieve


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
