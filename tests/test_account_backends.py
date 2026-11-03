from app.core import accounts
from app.core.accounts import AccountStore, PostgresAccountStore


def test_postgres_store_converts_placeholders():
    query = "SELECT id FROM users WHERE email = ? AND iterations = ?"
    converted = PostgresAccountStore._q(None, query)
    assert converted == "SELECT id FROM users WHERE email = %s AND iterations = %s"


def test_factory_uses_sqlite_without_database_url(tmp_path, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("KAMBA_DB_PATH", str(tmp_path / "x.db"))
    accounts.get_account_store.cache_clear()
    try:
        assert type(accounts.get_account_store()) is AccountStore
    finally:
        accounts.get_account_store.cache_clear()


def test_factory_uses_postgres_when_database_url_is_set(monkeypatch):
    created = {}

    class FakePostgres:
        def __init__(self, url):
            created["url"] = url

    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@host/db")
    monkeypatch.setattr(accounts, "PostgresAccountStore", FakePostgres)
    accounts.get_account_store.cache_clear()
    try:
        accounts.get_account_store()
        assert created["url"] == "postgresql://u:p@host/db"
    finally:
        accounts.get_account_store.cache_clear()
