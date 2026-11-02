"""Testes de integração opcionais contra uma instância Ollama real.

Executar apenas quando o serviço local e os modelos configurados estiverem disponíveis:
KAMBA_OLLAMA_INTEGRATION=1 pytest -q tests/integration
"""
import os

import pytest

from app.ai.ollama_provider import OllamaProvider
from app.core.config import get_settings
from app.rag.embeddings import OllamaEmbedder


pytestmark = pytest.mark.skipif(
    os.getenv("KAMBA_OLLAMA_INTEGRATION") != "1",
    reason="Define KAMBA_OLLAMA_INTEGRATION=1 para ativar testes Ollama reais.",
)


def test_real_ollama_chat_and_embeddings_are_available():
    """Confirma respostas não vazias e vetores finitos sem executar código."""
    settings = get_settings()

    answer = OllamaProvider(settings).analyze(
        "Explica em duas frases o princípio do menor privilégio.",
        "cybersecurity",
        context="O princípio do menor privilégio limita cada utilizador às permissões necessárias.",
    )
    vectors = OllamaEmbedder(settings).embed(
        ["segurança defensiva", "princípio do menor privilégio"]
    )

    assert len(answer) == 1
    assert answer[0].strip()
    assert len(vectors) == 2
    assert vectors[0]
    assert len(vectors[0]) == len(vectors[1])
    assert all(
        isinstance(value, float) and value == value and abs(value) != float("inf")
        for vector in vectors
        for value in vector
    )
