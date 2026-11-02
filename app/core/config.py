"""Configuração da aplicação através de variáveis de ambiente."""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    ai_provider: str = "rules"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:3b"
    ollama_timeout_seconds: float = 30.0


def get_settings() -> Settings:
    """Lê configuração sem exigir ficheiros .env nem guardar segredos."""
    return Settings(
        ai_provider=os.getenv("AI_PROVIDER", "rules").strip().lower(),
        ollama_base_url=os.getenv(
            "OLLAMA_BASE_URL", "http://127.0.0.1:11434"
        ).rstrip("/"),
        ollama_model=os.getenv("OLLAMA_MODEL", "qwen2.5:3b").strip(),
        ollama_timeout_seconds=float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "30")),
    )
