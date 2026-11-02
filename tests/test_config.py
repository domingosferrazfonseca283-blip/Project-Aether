import pytest

from app.core.config import Settings, get_settings


def test_default_settings_are_safe_local_defaults(monkeypatch):
    for name in (
        "AI_PROVIDER", "RAG_PROVIDER", "OLLAMA_BASE_URL", "OLLAMA_MODEL",
        "OLLAMA_TIMEOUT_SECONDS", "RAG_EMBEDDING_MODEL",
    ):
        monkeypatch.delenv(name, raising=False)

    settings = get_settings()
    assert settings.ai_provider == "rules"
    assert settings.rag_provider == "lexical"
    assert settings.ollama_base_url == "http://127.0.0.1:11434"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"ai_provider": "unknown"},
        {"rag_provider": "remote"},
        {"ollama_model": " "},
        {"rag_embedding_model": ""},
        {"ollama_timeout_seconds": 0},
        {"ollama_timeout_seconds": 301},
        {"ollama_timeout_seconds": float("nan")},
        {"ollama_timeout_seconds": float("inf")},
        {"ollama_num_predict": 0},
        {"ollama_num_predict": 8193},
        {"ollama_num_predict": True},
        {"ollama_base_url": "file:///etc/passwd"},
        {"ollama_base_url": "http://user:password@localhost:11434"},
        {"ollama_base_url": "http://localhost:11434?token=secret"},
        {"ollama_base_url": "http://localhost:99999"},
        {"ollama_base_url": "http://[::1"},
        {"ollama_base_url": "http://local host:11434"},
    ],
)
def test_settings_reject_invalid_values(kwargs):
    with pytest.raises(ValueError):
        Settings(**kwargs)


def test_get_settings_rejects_non_numeric_timeout(monkeypatch):
    monkeypatch.setenv("OLLAMA_TIMEOUT_SECONDS", "fast")
    with pytest.raises(ValueError, match="número"):
        get_settings()


def test_get_settings_normalizes_provider_and_url(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "OLLAMA")
    monkeypatch.setenv("RAG_PROVIDER", "OLLAMA")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434/")
    settings = get_settings()
    assert settings.ai_provider == "ollama"
    assert settings.rag_provider == "ollama"
    assert settings.ollama_base_url == "http://localhost:11434"


@pytest.mark.parametrize(
    ("variable", "message"),
    [
        ("KAMBA_RATE_LIMIT_REQUESTS", "KAMBA_RATE_LIMIT_REQUESTS"),
        ("KAMBA_RATE_LIMIT_WINDOW_SECONDS", "KAMBA_RATE_LIMIT_WINDOW_SECONDS"),
    ],
)
def test_get_settings_rejects_non_integer_rate_limits(monkeypatch, variable, message):
    monkeypatch.setenv(variable, "not-an-integer")
    with pytest.raises(ValueError, match=message):
        get_settings()


def test_get_settings_rejects_non_positive_rate_limits(monkeypatch):
    monkeypatch.setenv("KAMBA_RATE_LIMIT_REQUESTS", "0")
    with pytest.raises(ValueError, match="inteiros positivos"):
        get_settings()


def test_get_settings_reads_ollama_generation_limit(monkeypatch):
    monkeypatch.setenv("OLLAMA_NUM_PREDICT", "768")
    assert get_settings().ollama_num_predict == 768


def test_get_settings_rejects_non_integer_ollama_generation_limit(monkeypatch):
    monkeypatch.setenv("OLLAMA_NUM_PREDICT", "many")
    with pytest.raises(ValueError, match="OLLAMA_NUM_PREDICT"):
        get_settings()
