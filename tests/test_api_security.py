from app.core.security import InMemoryRateLimiter, api_key_is_valid


def test_api_key_validation_requires_exact_configured_secret():
    assert api_key_is_valid("a" * 32, "a" * 32)
    assert not api_key_is_valid("a" * 32, "b" * 32)
    assert not api_key_is_valid("a" * 32, None)
    assert not api_key_is_valid("", "a" * 32)
    assert not api_key_is_valid("a" * 32, "chave-com-caracteres-ç")
    assert not api_key_is_valid("chave-com-caracteres-ç", "a" * 32)


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

from dataclasses import replace

from fastapi.testclient import TestClient

import app.main as main_module


def test_protected_api_requires_configured_key(monkeypatch):
    monkeypatch.setattr(
        main_module, "settings",
        replace(main_module.settings, api_key="k" * 32),
    )
    response = TestClient(main_module.app).post(
        "/review-code", json={"content": "print('safe')"}
    )
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "ApiKey"


def test_protected_api_accepts_valid_key(monkeypatch):
    monkeypatch.setattr(
        main_module, "settings",
        replace(main_module.settings, api_key="k" * 32),
    )
    monkeypatch.setattr(main_module, "rate_limiter", InMemoryRateLimiter(limit=10, window_seconds=60))
    response = TestClient(main_module.app).post(
        "/review-code",
        json={"content": "print('safe')"},
        headers={"X-API-Key": "k" * 32},
    )
    assert response.status_code == 200


def test_protected_api_returns_429_after_configured_limit(monkeypatch):
    monkeypatch.setattr(
        main_module, "settings",
        replace(main_module.settings, api_key=""),
    )
    monkeypatch.setattr(main_module, "rate_limiter", InMemoryRateLimiter(limit=1, window_seconds=60))
    client = TestClient(main_module.app)
    first = client.post("/review-code", json={"content": "print('safe')"})
    second = client.post("/review-code", json={"content": "print('safe')"})
    assert first.status_code == 200
    assert second.status_code == 429
    assert second.headers["Retry-After"] == "60"
    assert second.headers["X-Request-ID"]
    assert second.headers["Cache-Control"] == "no-store"
    assert second.headers["X-Content-Type-Options"] == "nosniff"
    assert second.headers["X-Frame-Options"] == "DENY"

def test_invalid_api_keys_are_also_rate_limited(monkeypatch):
    monkeypatch.setattr(
        main_module, "settings",
        replace(main_module.settings, api_key="k" * 32),
    )
    monkeypatch.setattr(
        main_module, "rate_limiter",
        InMemoryRateLimiter(limit=1, window_seconds=60),
    )
    client = TestClient(main_module.app)
    headers = {"X-API-Key": "x" * 32}

    assert client.post("/review-code", json={"content": "print('safe')"}, headers=headers).status_code == 401
    limited = client.post("/review-code", json={"content": "print('safe')"}, headers=headers)
    assert limited.status_code == 429


def test_rate_limiter_enforces_limit_under_concurrent_requests():
    from concurrent.futures import ThreadPoolExecutor

    limiter = InMemoryRateLimiter(limit=5, window_seconds=60)
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(
            lambda _: limiter.allow("shared-client", now=100),
            range(20),
        ))

    assert sum(results) == 5


def test_rate_limiter_periodically_removes_expired_client_windows():
    limiter = InMemoryRateLimiter(limit=2, window_seconds=10)

    assert limiter.allow("expired-client", now=100)
    assert limiter.allow("active-client", now=105)
    assert "expired-client" in limiter._windows

    assert limiter.allow("new-client", now=110)

    assert "expired-client" not in limiter._windows
    assert "active-client" in limiter._windows
    assert "new-client" in limiter._windows


def test_api_adds_security_headers_and_unique_request_ids():
    client = TestClient(main_module.app)

    first = client.get("/health")
    second = client.get("/health")

    for response in (first, second):
        assert response.status_code == 200
        assert response.headers["X-Request-ID"]
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["Referrer-Policy"] == "no-referrer"
        assert response.headers["Permissions-Policy"] == (
            "camera=(), microphone=(), geolocation=()"
        )

    assert first.headers["X-Request-ID"] != second.headers["X-Request-ID"]


def test_validation_error_keeps_security_headers_without_echoing_input():
    client = TestClient(main_module.app)
    response = client.post(
        "/analyze",
        json={"content": "private-marker", "category": "invalid-category"},
    )

    assert response.status_code == 422
    assert response.headers["X-Request-ID"]
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "private-marker" not in response.text
