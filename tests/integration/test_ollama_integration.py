"""Testes de integração opcionais contra uma instância Ollama real.

Executar apenas quando o serviço local e os modelos configurados estiverem disponíveis:
KAMBA_OLLAMA_INTEGRATION=1 pytest -q tests/integration
"""
import os
from math import isfinite

import pytest

from app.ai.ollama_provider import OllamaProvider
from app.core.config import get_settings
from app.rag.embeddings import OllamaEmbedder


pytestmark = pytest.mark.skipif(
    os.getenv("KAMBA_OLLAMA_INTEGRATION") != "1",
    reason="Define KAMBA_OLLAMA_INTEGRATION=1 para ativar testes Ollama reais.",
)


def test_real_ollama_chat_returns_non_empty_answer():
    """Confirma que /api/chat responde sem executar código submetido."""
    settings = get_settings()

    answer = OllamaProvider(settings).analyze(
        "Explica em duas frases o princípio do menor privilégio.",
        "cybersecurity",
        context="O princípio do menor privilégio limita cada utilizador às permissões necessárias.",
    )

    assert len(answer) == 1
    assert answer[0].strip()


def test_real_ollama_embeddings_are_finite_and_consistent():
    """Confirma quantidade, dimensão e validade numérica dos vetores."""
    settings = get_settings()

    vectors = OllamaEmbedder(settings).embed(
        ["segurança defensiva", "princípio do menor privilégio"]
    )

    assert len(vectors) == 2
    assert all(vectors)
    assert len(vectors[0]) == len(vectors[1])
    assert all(
        isfinite(value)
        for vector in vectors
        for value in vector
    )
