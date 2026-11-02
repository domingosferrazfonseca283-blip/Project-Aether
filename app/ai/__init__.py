"""Fábrica e contratos dos fornecedores de IA."""
from app.ai.ollama_provider import OllamaProvider
from app.ai.provider import AIProvider, RuleBasedProvider
from app.core.config import get_settings


def get_provider() -> AIProvider:
    """Seleciona o fornecedor por configuração; fallback local é o padrão."""
    settings = get_settings()
    if settings.ai_provider == "ollama":
        return OllamaProvider(settings)
    return RuleBasedProvider()


__all__ = ["AIProvider", "OllamaProvider", "RuleBasedProvider", "get_provider"]
