"""Testes unitários dos controlos locais de autenticação e rate limiting."""

from app.core.security import InMemoryRateLimiter, api_key_is_valid


def test_api_key_validation_requires_both_values():
    assert not api_key_is_valid("", "valid-looking-key")
    assert not api_key_is_valid("expected-key", None)
    assert not api_key_is_valid("expected-key", "")


def test_api_key_validation_accepts_exact_match_only():
    assert api_key_is_valid("a" * 32, "a" * 32)
    assert not api_key_is_valid("a" * 32, "b" * 32)


def test_api_key_validation_rejects_non_ascii_input_without_raising():
    assert not api_key_is_valid("a" * 32, "chave-com-caracteres-á")


def test_rate_limiter_enforces_limit_per_client():
    limiter = InMemoryRateLimiter(limit=2, window_seconds=10)

    assert limiter.allow("client-a", now=100.0)
    assert limiter.allow("client-a", now=101.0)
    assert not limiter.allow("client-a", now=102.0)
    assert limiter.allow("client-b", now=102.0)


def test_rate_limiter_resets_after_window_expires():
    limiter = InMemoryRateLimiter(limit=1, window_seconds=10)

    assert limiter.allow("client-a", now=100.0)
    assert not limiter.allow("client-a", now=109.0)
    assert limiter.allow("client-a", now=110.0)


def test_rate_limiter_allows_request_at_exact_window_boundary():
    limiter = InMemoryRateLimiter(limit=1, window_seconds=10)

    assert limiter.allow("client-a", now=5.0)
    assert limiter.allow("client-a", now=15.0)
