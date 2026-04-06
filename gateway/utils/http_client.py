"""Global Singleton mapping for HTTPX interface pools."""

from typing import Optional
import httpx


class HTTPClient:
    """
    Singleton manager for httpx.AsyncClient.
    Follows SRP and DRY by centralizing HTTP connections.
    """

    _client: Optional[httpx.AsyncClient] = None

    @classmethod
    def get_client(cls) -> httpx.AsyncClient:
        """Retrieve the active async HTTP Client."""
        if cls._client is None or cls._client.is_closed:
            cls._client = httpx.AsyncClient(timeout=120.0)
        return cls._client

    @classmethod
    async def close(cls):
        """Gracefully close the HTTP client to avoid resource leaks."""
        if cls._client and not cls._client.is_closed:
            await cls._client.aclose()
            cls._client = None
