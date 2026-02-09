from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import httpx


class APIClientError(Exception):  # noqa: D101
    def __init__(
        self, method: str, url: str | httpx.URL, status_code: int, error: str | Exception
    ) -> None:
        self.method = method
        self.url = url
        self.status_code = status_code
        self.error = error

    def __str__(self) -> str:
        return f"[{self.method}] {self.url} - HTTP {self.status_code} - {self.error}"
