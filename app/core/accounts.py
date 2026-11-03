"""Contas de utilizador e tokens de sessão (SQLite, só biblioteca padrão)."""
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
    def __init__(
        self,
        db_path,
        iterations: int = PBKDF2_ITERATIONS,
        token_ttl_seconds: float = TOKEN_TTL_SECONDS,
    ) -> None:
        self.db_path = str(db_path)
        self.iterations = iterations
        self.token_ttl_seconds = token_ttl_seconds
        self._dummy_salt = os.urandom(16)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS users ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "email TEXT NOT NULL UNIQUE, "
                "password_hash TEXT NOT NULL, "
                "salt TEXT NOT NULL, "
                "iterations INTEGER NOT NULL, "
                "created_at TEXT NOT NULL)"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS tokens ("
                "token_hash TEXT PRIMARY KEY, "
                "user_id INTEGER NOT NULL "
                "REFERENCES users(id) ON DELETE CASCADE, "
                "expires_at REAL NOT NULL)"
            )
        try:
            os.chmod(self.db_path, 0o600)
        except OSError:
            pass

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
        try:
            with closing(self._connect()) as conn, conn:
                cursor = conn.execute(
                    "INSERT INTO users "
                    "(email, password_hash, salt, iterations, created_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (email, digest.hex(), salt.hex(), self.iterations, created_at),
                )
                return int(cursor.lastrowid)
        except sqlite3.IntegrityError as exc:
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
                "SELECT id, password_hash, salt, iterations "
                "FROM users WHERE email = ?",
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
            conn.execute("DELETE FROM tokens WHERE expires_at <= ?", (time.time(),))
            conn.execute(
                "INSERT INTO tokens (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
                (_token_hash(token), user_id, expires_at),
            )
        return token, expires_at

    def user_for_token(self, token: str | None) -> int | None:
        if not token or len(token) > 200:
            return None
        token_hash = _token_hash(token)
        with closing(self._connect()) as conn, conn:
            row = conn.execute(
                "SELECT user_id, expires_at FROM tokens WHERE token_hash = ?",
                (token_hash,),
            ).fetchone()
            if row is None:
                return None
            user_id, expires_at = row
            if expires_at <= time.time():
                conn.execute("DELETE FROM tokens WHERE token_hash = ?", (token_hash,))
                return None
            return int(user_id)

    def revoke_token(self, token: str | None) -> bool:
        if not token or len(token) > 200:
            return False
        with closing(self._connect()) as conn, conn:
            cursor = conn.execute(
                "DELETE FROM tokens WHERE token_hash = ?", (_token_hash(token),)
            )
            return cursor.rowcount > 0

    def delete_user(self, user_id: int) -> bool:
        with closing(self._connect()) as conn, conn:
            cursor = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            return cursor.rowcount > 0


@lru_cache(maxsize=1)
def get_account_store() -> AccountStore:
    """Base de dados em KAMBA_DB_PATH (por omissão data/kamba.db)."""
    return AccountStore(os.environ.get("KAMBA_DB_PATH", "data/kamba.db"))
