import httpx
from typing import Optional

class HTTPClient:
    """
    Singleton manager for httpx.AsyncClient.
    Follows SRP and DRY by centralizing HTTP connections.
    """
    _client: Optional[httpx.AsyncClient] = None

    @classmethod
    def get_client(cls) -> httpx.AsyncClient:
        if cls._client is None or cls._client.is_closed:
            cls._client = httpx.AsyncClient(timeout=15.0)
        return cls._client

    @classmethod
    async def close(cls):
        if cls._client and not cls._client.is_closed:
            await cls._client.aclose()
            cls._client = None
