"""Controlos locais de autenticação e limitação de pedidos."""
from collections import defaultdict
from hmac import compare_digest
from threading import Lock
from time import monotonic


def api_key_is_valid(expected: str, supplied: str | None) -> bool:
    """Compara chaves sem comparação textual de tempo variável."""
    if not expected or not supplied:
        return False
    try:
        return compare_digest(expected, supplied)
    except TypeError:
        # compare_digest só aceita strings ASCII; entradas inválidas não devem
        # transformar uma tentativa de autenticação num erro HTTP 500.
        return False


class InMemoryRateLimiter:
    """Janela fixa por cliente; estado apenas em memória deste processo."""

    def __init__(self, limit: int = 60, window_seconds: int = 60) -> None:
        if limit < 1 or window_seconds < 1:
            raise ValueError("Os limites devem ser positivos.")
        self.limit = limit
        self.window_seconds = window_seconds
        self._lock = Lock()
        self._windows: dict[str, tuple[float, int]] = {}

    def allow(self, client_id: str, now: float | None = None) -> bool:
        current = monotonic() if now is None else now
        with self._lock:
            started, count = self._windows.get(client_id, (current, 0))
            if current - started >= self.window_seconds:
                started, count = current, 0
            if count >= self.limit:
                self._windows[client_id] = (started, count)
                return False
            self._windows[client_id] = (started, count + 1)
            return True
