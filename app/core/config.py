"""Configuração validada da aplicação através de variáveis de ambiente."""
import os
from dataclasses import dataclass
from math import isfinite
from urllib.parse import urlsplit


@dataclass(frozen=True)
class Settings:
    ai_provider: str = "rules"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:3b"
    ollama_timeout_seconds: float = 30.0
    ollama_num_predict: int = 1024
    rag_provider: str = "lexical"
    rag_embedding_model: str = "nomic-embed-text"
    api_key: str = ""
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60

    def __post_init__(self) -> None:
        if self.ai_provider not in {"rules", "ollama"}:
            raise ValueError("AI_PROVIDER deve ser 'rules' ou 'ollama'.")
        if self.rag_provider not in {"lexical", "ollama"}:
            raise ValueError("RAG_PROVIDER deve ser 'lexical' ou 'ollama'.")
        if self.api_key and len(self.api_key) < 32:
            raise ValueError("KAMBA_API_KEY deve ter pelo menos 32 caracteres.")
        if self.rate_limit_requests < 1 or self.rate_limit_window_seconds < 1:
            raise ValueError("Os limites de pedidos devem ser inteiros positivos.")
        if isinstance(self.ollama_num_predict, bool) or not 1 <= self.ollama_num_predict <= 8192:
            raise ValueError("OLLAMA_NUM_PREDICT deve estar entre 1 e 8192.")
        if not self.ollama_model.strip():
            raise ValueError("OLLAMA_MODEL não pode estar vazio.")
        if not self.rag_embedding_model.strip():
            raise ValueError("RAG_EMBEDDING_MODEL não pode estar vazio.")
        if (
            not isfinite(self.ollama_timeout_seconds)
            or not 0 < self.ollama_timeout_seconds <= 300
        ):
            raise ValueError("OLLAMA_TIMEOUT_SECONDS deve estar entre 0 e 300 segundos.")
        try:
            parsed = urlsplit(self.ollama_base_url)
            hostname = parsed.hostname
            # Accessing .port also validates numeric syntax and the 0-65535 range.
            parsed.port
        except ValueError as exc:
            raise ValueError(
                "OLLAMA_BASE_URL deve ser um URL HTTP(S) válido, sem credenciais."
            ) from exc

        if (
            parsed.scheme not in {"http", "https"}
            or not hostname
            or any(character.isspace() for character in hostname)
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("OLLAMA_BASE_URL deve ser um URL HTTP(S) válido, sem credenciais.")


def _read_int_env(name: str, default: int) -> int:
    """Lê uma variável inteira e identifica claramente erros de conversão."""
    try:
        return int(os.getenv(name, str(default)))
    except ValueError as exc:
        raise ValueError(f"{name} deve ser um número inteiro.") from exc


def get_settings() -> Settings:
    """Lê o ambiente e falha cedo quando a configuração é inválida."""
    try:
        timeout = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "30"))
    except ValueError as exc:
        raise ValueError("OLLAMA_TIMEOUT_SECONDS deve ser um número.") from exc

    return Settings(
        ai_provider=os.getenv("AI_PROVIDER", "rules").strip().lower(),
        ollama_base_url=os.getenv(
            "OLLAMA_BASE_URL", "http://127.0.0.1:11434"
        ).rstrip("/"),
        ollama_model=os.getenv("OLLAMA_MODEL", "qwen2.5:3b").strip(),
        ollama_timeout_seconds=timeout,
        ollama_num_predict=_read_int_env("OLLAMA_NUM_PREDICT", 1024),
        rag_provider=os.getenv("RAG_PROVIDER", "lexical").strip().lower(),
        rag_embedding_model=os.getenv(
            "RAG_EMBEDDING_MODEL", "nomic-embed-text"
        ).strip(),
        api_key=os.getenv("KAMBA_API_KEY", ""),
        rate_limit_requests=_read_int_env("KAMBA_RATE_LIMIT_REQUESTS", 60),
        rate_limit_window_seconds=_read_int_env("KAMBA_RATE_LIMIT_WINDOW_SECONDS", 60),
    )
