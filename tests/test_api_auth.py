import app.main as main_module
from app.core.security import InMemoryRateLimiter

PASSWORD = "minha-password-123"
CHAT = {"messages": [{"role": "user", "content": "Olá"}]}


def _register(api, email="ana@exemplo.com", password=PASSWORD):
    return api.post("/auth/register", json={"email": email, "password": password})


def _bearer(response):
    return {"Authorization": "Bearer " + response.json()["access_token"]}


def test_register_returns_token_that_works_on_chat(api):
    response = _register(api)
    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"] and body["expires_at"]
    assert api.post("/chat", json=CHAT, headers=_bearer(response)).status_code == 200


def test_chat_requires_a_valid_token(api):
    missing = api.post("/chat", json=CHAT)
    assert missing.status_code == 401
    assert missing.headers["WWW-Authenticate"] == "Bearer"
    wrong = api.post("/chat", json=CHAT, headers={"Authorization": "Bearer inventado"})
    assert wrong.status_code == 401
    other_scheme = api.post("/chat", json=CHAT, headers={"Authorization": "Basic abc"})
    assert other_scheme.status_code == 401


def test_register_rejects_duplicate_weak_password_and_bad_email(api):
    assert _register(api).status_code == 201
    assert _register(api, email="ANA@exemplo.com").status_code == 409
    assert _register(api, email="rui@exemplo.com", password="curta").status_code == 422
    assert _register(api, email="isto-nao-e-email").status_code == 422


def test_login_success_and_failure_are_indistinguishable(api):
    _register(api)
    ok = api.post("/auth/login", json={"email": "ana@exemplo.com", "password": PASSWORD})
    assert ok.status_code == 200
    wrong = api.post("/auth/login", json={"email": "ana@exemplo.com", "password": "errada-1234"})
    unknown = api.post("/auth/login", json={"email": "ninguem@exemplo.com", "password": PASSWORD})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()


def test_logout_revokes_the_token(api):
    headers = _bearer(_register(api))
    assert api.post("/auth/logout", headers=headers).status_code == 200
    assert api.post("/chat", json=CHAT, headers=headers).status_code == 401
    assert api.post("/auth/logout", headers=headers).status_code == 401


def test_delete_account_removes_access_and_login(api):
    headers = _bearer(_register(api))
    assert api.delete("/auth/account", headers=headers).status_code == 200
    assert api.post("/chat", json=CHAT, headers=headers).status_code == 401
    login = api.post("/auth/login", json={"email": "ana@exemplo.com", "password": PASSWORD})
    assert login.status_code == 401


def test_auth_endpoints_use_no_store_and_do_not_echo_password(api):
    response = api.post("/auth/login", json={"email": "", "password": "SEGREDO-XYZ"})
    assert response.status_code == 422
    assert "SEGREDO-XYZ" not in response.text
    ok = _register(api)
    assert ok.headers["Cache-Control"] == "no-store"


def test_auth_endpoints_are_rate_limited_per_ip(monkeypatch, api):
    monkeypatch.setattr(
        main_module, "auth_limiter", InMemoryRateLimiter(limit=2, window_seconds=60)
    )
    body = {"email": "ana@exemplo.com", "password": "errada-1234"}
    statuses = [api.post("/auth/login", json=body).status_code for _ in range(3)]
    assert statuses == [401, 401, 429]


def test_chat_is_rate_limited_per_user(monkeypatch, api):
    monkeypatch.setattr(
        main_module, "chat_limiter", InMemoryRateLimiter(limit=2, window_seconds=60)
    )
    first = _bearer(_register(api, email="ana@exemplo.com"))
    second = _bearer(_register(api, email="rui@exemplo.com"))
    statuses = [api.post("/chat", json=CHAT, headers=first).status_code for _ in range(3)]
    assert statuses == [200, 200, 429]
    assert api.post("/chat", json=CHAT, headers=second).status_code == 200
