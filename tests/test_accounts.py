import pytest

from app.core.accounts import (
    AccountStore,
    DuplicateEmailError,
    InvalidCredentialsError,
    InvalidEmailError,
    InvalidPasswordError,
)

PASSWORD = "minha-password-123"


@pytest.fixture
def store(tmp_path):
    return AccountStore(tmp_path / "contas.db", iterations=1000)


def _db_bytes(store):
    with open(store.db_path, "rb") as handle:
        return handle.read()


def test_create_and_authenticate(store):
    user_id = store.create_user("Ana@Exemplo.com", PASSWORD)
    assert store.authenticate("ana@exemplo.com", PASSWORD) == user_id
    assert store.authenticate("  ANA@exemplo.COM ", PASSWORD) == user_id


def test_duplicate_email_is_rejected_case_insensitively(store):
    store.create_user("ana@exemplo.com", PASSWORD)
    with pytest.raises(DuplicateEmailError):
        store.create_user("ANA@exemplo.com", PASSWORD)


def test_wrong_password_and_unknown_email_fail_the_same_way(store):
    store.create_user("ana@exemplo.com", PASSWORD)
    with pytest.raises(InvalidCredentialsError) as wrong:
        store.authenticate("ana@exemplo.com", "outra-password-1")
    with pytest.raises(InvalidCredentialsError) as unknown:
        store.authenticate("ninguem@exemplo.com", PASSWORD)
    with pytest.raises(InvalidCredentialsError):
        store.authenticate("isto-nao-e-email", PASSWORD)
    with pytest.raises(InvalidCredentialsError):
        store.authenticate("ana@exemplo.com", "x" * 5000)
    assert str(wrong.value) == str(unknown.value)


def test_invalid_email_and_password_are_rejected(store):
    for bad in ("", "sem-arroba", "a@b", "a b@c.com", "x" * 260 + "@c.com"):
        with pytest.raises(InvalidEmailError):
            store.create_user(bad, PASSWORD)
    with pytest.raises(InvalidPasswordError):
        store.create_user("ana@exemplo.com", "curta")
    with pytest.raises(InvalidPasswordError):
        store.create_user("ana@exemplo.com", "x" * 129)


def test_password_is_not_stored_in_plain_text(store):
    store.create_user("ana@exemplo.com", PASSWORD)
    assert PASSWORD.encode() not in _db_bytes(store)


def test_same_password_gets_different_hashes(store):
    store.create_user("ana@exemplo.com", PASSWORD)
    store.create_user("rui@exemplo.com", PASSWORD)
    import sqlite3
    with sqlite3.connect(store.db_path) as conn:
        rows = conn.execute("SELECT password_hash, salt FROM users").fetchall()
    assert rows[0][0] != rows[1][0]
    assert rows[0][1] != rows[1][1]


def test_token_lifecycle(store):
    user_id = store.create_user("ana@exemplo.com", PASSWORD)
    token, expires_at = store.issue_token(user_id)
    assert store.user_for_token(token) == user_id
    assert token.encode() not in _db_bytes(store)
    assert store.revoke_token(token) is True
    assert store.user_for_token(token) is None
    assert store.revoke_token(token) is False


def test_unknown_or_empty_tokens_are_rejected(store):
    assert store.user_for_token(None) is None
    assert store.user_for_token("") is None
    assert store.user_for_token("inventado") is None
    assert store.user_for_token("x" * 500) is None


def test_expired_token_is_rejected(tmp_path):
    expired = AccountStore(tmp_path / "e.db", iterations=1000, token_ttl_seconds=-1)
    user_id = expired.create_user("ana@exemplo.com", PASSWORD)
    token, _ = expired.issue_token(user_id)
    assert expired.user_for_token(token) is None


def test_each_login_gets_a_distinct_token(store):
    user_id = store.create_user("ana@exemplo.com", PASSWORD)
    first, _ = store.issue_token(user_id)
    second, _ = store.issue_token(user_id)
    assert first != second
    assert store.user_for_token(first) == user_id
    assert store.user_for_token(second) == user_id


def test_delete_user_removes_account_and_tokens(store):
    user_id = store.create_user("ana@exemplo.com", PASSWORD)
    token, _ = store.issue_token(user_id)
    assert store.delete_user(user_id) is True
    assert store.user_for_token(token) is None
    with pytest.raises(InvalidCredentialsError):
        store.authenticate("ana@exemplo.com", PASSWORD)
    assert store.delete_user(user_id) is False
