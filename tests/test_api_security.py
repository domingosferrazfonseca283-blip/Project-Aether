from app.core.security import InMemoryRateLimiter, api_key_is_valid


def test_api_key_validation_requires_exact_configured_secret():
    assert api_key_is_valid("a" * 32, "a" * 32)
    assert not api_key_is_valid("a" * 32, "b" * 32)
    assert not api_key_is_valid("a" * 32, None)
    assert not api_key_is_valid("", "a" * 32)


def test_rate_limiter_enforces_and_resets_fixed_window():
    limiter = InMemoryRateLimiter(limit=2, window_seconds=10)

    assert limiter.allow("client-a", now=100)
    assert limiter.allow("client-a", now=101)
    assert not limiter.allow("client-a", now=102)
    assert limiter.allow("client-a", now=110)


def test_rate_limiter_tracks_clients_independently():
    limiter = InMemoryRateLimiter(limit=1, window_seconds=10)

    assert limiter.allow("client-a", now=100)
    assert limiter.allow("client-b", now=100)
    assert not limiter.allow("client-a", now=101)
