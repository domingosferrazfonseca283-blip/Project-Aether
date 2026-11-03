import pytest
from fastapi.testclient import TestClient

import app.main as main_module
from app.core.accounts import AccountStore
from app.core.security import InMemoryRateLimiter

PASSWORD = "minha-password-123"


@pytest.fixture
def api(tmp_path, monkeypatch):
    store = AccountStore(tmp_path / "teste.db", iterations=1000)
    main_module.app.dependency_overrides[main_module.account_store] = lambda: store
    monkeypatch.setattr(
        main_module, "auth_limiter", InMemoryRateLimiter(limit=1000, window_seconds=60)
    )
    monkeypatch.setattr(
        main_module, "chat_limiter", InMemoryRateLimiter(limit=1000, window_seconds=60)
    )
    yield TestClient(main_module.app)
    main_module.app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(api):
    response = api.post(
        "/auth/register", json={"email": "ana@exemplo.com", "password": PASSWORD}
    )
    return {"Authorization": "Bearer " + response.json()["access_token"]}
