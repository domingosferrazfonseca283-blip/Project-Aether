"""Contas de utilizador e tokens de sessão (SQLite local ou PostgreSQL)."""
import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import time
from contextlib import closing
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

PBKDF2_ITERATIONS = 600_000
TOKEN_TTL_SECONDS = 7 * 24 * 3600
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

_INSERT_USER = (
    "INSERT INTO assistant_users (email, password_hash, salt, iterations, created_at) "
    "VALUES (?, ?, ?, ?, ?)"
)


class AccountError(Exception):
    """Erro base das contas; as mensagens são seguras para mostrar ao cliente."""


class InvalidEmailError(AccountError):
    pass


class InvalidPasswordError(AccountError):
    pass


class DuplicateEmailError(AccountError):
    pass


class InvalidCredentialsError(AccountError):
    pass


def normalize_email(email: str) -> str:
    value = email.strip().lower()
    if len(value) > 254 or not _EMAIL_RE.match(value):
        raise InvalidEmailError("E-mail inválido.")
    return value


def _hash_password(password: str, salt: bytes, iterations: int) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class AccountStore:
    """Versão SQLite: desenvolvimento local e testes."""

    def __init__(
        self,
        db_path,
        iterations: int = PBKDF2_ITERATIONS,
        token_ttl_seconds: float = TOKEN_TTL_SECONDS,
    ) -> None:
        self.db_path = str(db_path)
        self._configure(iterations, token_ttl_seconds)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        try:
            os.chmod(self.db_path, 0o600)
        except OSError:
            pass

    def _configure(self, iterations: int, token_ttl_seconds: float) -> None:
        self.iterations = iterations
        self.token_ttl_seconds = token_ttl_seconds
        self._dummy_salt = os.urandom(16)

    # ---- ganchos que mudam entre SQLite e PostgreSQL ----

    def _connect(self):
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _q(self, sql: str) -> str:
        return sql

    def _integrity_errors(self) -> tuple:
        return (sqlite3.IntegrityError,)

    def _schema(self) -> list[str]:
        return [
            "CREATE TABLE IF NOT EXISTS assistant_users ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "email TEXT NOT NULL UNIQUE, "
            "password_hash TEXT NOT NULL, "
            "salt TEXT NOT NULL, "
            "iterations INTEGER NOT NULL, "
            "created_at TEXT NOT NULL)",
            "CREATE TABLE IF NOT EXISTS assistant_tokens ("
            "token_hash TEXT PRIMARY KEY, "
            "user_id INTEGER NOT NULL REFERENCES assistant_users(id) ON DELETE CASCADE, "
            "expires_at REAL NOT NULL)",
        ]

    def _insert_user(self, conn, params: tuple) -> int:
        cursor = conn.execute(self._q(_INSERT_USER), params)
        return int(cursor.lastrowid)

    # ---- lógica comum ----

    def _init_db(self) -> None:
        with closing(self._connect()) as conn, conn:
            for statement in self._schema():
                conn.execute(statement)

    def _burn(self, password: str) -> None:
        """Gasta o mesmo tempo de uma verificação real (evita revelar contas)."""
        _hash_password(password[:MAX_PASSWORD_LENGTH], self._dummy_salt, self.iterations)

    def create_user(self, email: str, password: str) -> int:
        email = normalize_email(email)
        if not MIN_PASSWORD_LENGTH <= len(password) <= MAX_PASSWORD_LENGTH:
            raise InvalidPasswordError(
                f"A password deve ter entre {MIN_PASSWORD_LENGTH} e "
                f"{MAX_PASSWORD_LENGTH} caracteres."
            )
        salt = os.urandom(16)
        digest = _hash_password(password, salt, self.iterations)
        created_at = datetime.now(timezone.utc).isoformat()
        params = (email, digest.hex(), salt.hex(), self.iterations, created_at)
        try:
            with closing(self._connect()) as conn, conn:
                return self._insert_user(conn, params)
        except self._integrity_errors() as exc:
            raise DuplicateEmailError("Já existe uma conta com este e-mail.") from exc

    def authenticate(self, email: str, password: str) -> int:
        failure = InvalidCredentialsError("E-mail ou password incorretos.")
        if len(password) > MAX_PASSWORD_LENGTH:
            raise failure
        try:
            email = normalize_email(email)
        except InvalidEmailError:
            self._burn(password)
            raise failure from None
        with closing(self._connect()) as conn:
            row = conn.execute(
                self._q(
                    "SELECT id, password_hash, salt, iterations "
                    "FROM assistant_users WHERE email = ?"
                ),
                (email,),
            ).fetchone()
        if row is None:
            self._burn(password)
            raise failure
        user_id, stored, salt_hex, iterations = row
        candidate = _hash_password(password, bytes.fromhex(salt_hex), iterations)
        if not hmac.compare_digest(candidate.hex(), stored):
            raise failure
        return int(user_id)

    def issue_token(self, user_id: int) -> tuple[str, float]:
        token = secrets.token_urlsafe(32)
        expires_at = time.time() + self.token_ttl_seconds
        with closing(self._connect()) as conn, conn:
            conn.execute(
                self._q("DELETE FROM assistant_tokens WHERE expires_at <= ?"), (time.time(),)
            )
            conn.execute(
                self._q(
                    "INSERT INTO assistant_tokens (token_hash, user_id, expires_at) "
                    "VALUES (?, ?, ?)"
                ),
                (_token_hash(token), user_id, expires_at),
            )
        return token, expires_at

    def user_for_token(self, token: str | None) -> int | None:
        if not token or len(token) > 200:
            return None
        token_hash = _token_hash(token)
        with closing(self._connect()) as conn, conn:
            row = conn.execute(
                self._q("SELECT user_id, expires_at FROM assistant_tokens WHERE token_hash = ?"),
                (token_hash,),
            ).fetchone()
            if row is None:
                return None
            user_id, expires_at = row
            if expires_at <= time.time():
                conn.execute(
                    self._q("DELETE FROM assistant_tokens WHERE token_hash = ?"), (token_hash,)
                )
                return None
            return int(user_id)

    def revoke_token(self, token: str | None) -> bool:
        if not token or len(token) > 200:
            return False
        with closing(self._connect()) as conn, conn:
            cursor = conn.execute(
                self._q("DELETE FROM assistant_tokens WHERE token_hash = ?"),
                (_token_hash(token),),
            )
            return cursor.rowcount > 0

    def delete_user(self, user_id: int) -> bool:
        with closing(self._connect()) as conn, conn:
            cursor = conn.execute(
                self._q("DELETE FROM assistant_users WHERE id = ?"), (user_id,)
            )
            return cursor.rowcount > 0


class PostgresAccountStore(AccountStore):
    """Versão PostgreSQL (produção); requer o pacote psycopg."""

    def __init__(
        self,
        database_url: str,
        iterations: int = PBKDF2_ITERATIONS,
        token_ttl_seconds: float = TOKEN_TTL_SECONDS,
    ) -> None:
        self.database_url = database_url
        self._configure(iterations, token_ttl_seconds)
        self._init_db()

    def _connect(self):
        import psycopg

        return psycopg.connect(self.database_url, connect_timeout=10)

    def _q(self, sql: str) -> str:
        return sql.replace("?", "%s")

    def _integrity_errors(self) -> tuple:
        import psycopg

        return (psycopg.errors.IntegrityError,)

    def _schema(self) -> list[str]:
        return [
            "CREATE TABLE IF NOT EXISTS assistant_users ("
            "id SERIAL PRIMARY KEY, "
            "email TEXT NOT NULL UNIQUE, "
            "password_hash TEXT NOT NULL, "
            "salt TEXT NOT NULL, "
            "iterations INTEGER NOT NULL, "
            "created_at TEXT NOT NULL)",
            "CREATE TABLE IF NOT EXISTS assistant_tokens ("
            "token_hash TEXT PRIMARY KEY, "
            "user_id INTEGER NOT NULL REFERENCES assistant_users(id) ON DELETE CASCADE, "
            "expires_at DOUBLE PRECISION NOT NULL)",
        ]

    def _insert_user(self, conn, params: tuple) -> int:
        row = conn.execute(
            self._q(_INSERT_USER + " RETURNING id"), params
        ).fetchone()
        return int(row[0])


@lru_cache(maxsize=1)
def get_account_store() -> AccountStore:
    """PostgreSQL se existir DATABASE_URL; senão SQLite em KAMBA_DB_PATH."""
    database_url = os.environ.get("DATABASE_URL", "").strip()
    if database_url:
        return PostgresAccountStore(database_url)
    return AccountStore(os.environ.get("KAMBA_DB_PATH", "data/kamba.db"))
