"""Service for proxying requests to internal AI Agents."""

import logging
import httpx
from fastapi import HTTPException
from gateway.utils.http_client import HTTPClient

logger = logging.getLogger("gateway.services.agents")


# pylint: disable=too-few-public-methods
class AgentProxyService:
    """
    Handles proxying requests to internal AI Agent microservices.
    Follows OCP by providing a generic request sender that can be extended
    without modifying the core networking logic.
    """

    @staticmethod
    async def request_agent(agent_url: str, payload: dict) -> dict:
        """Generic proxy method to communicate with any internal agent."""
        try:
            client = HTTPClient.get_client()
            r = await client.post(agent_url, json=payload)

            # Pass through 4xx errors gracefully
            if r.status_code >= 400:
                detail = (
                    r.json()
                    if r.headers.get("content-type") == "application/json"
                    else r.text
                )
                raise HTTPException(status_code=r.status_code, detail=detail)

            return r.json()

        except httpx.RequestError as e:
            logger.error("Failed to connect to AI Agent at %s: %s", agent_url, e)
            raise HTTPException(
                status_code=503,
                detail="The requested AI Agent service is currently unavailable.",
            ) from e

    @staticmethod
    async def stream_agent(agent_url: str, payload: dict):
        """Generic proxy method to stream responses from an internal agent."""
        client = HTTPClient.get_client()
        try:
            async with client.stream("POST", agent_url, json=payload) as response:
                if response.status_code >= 400:
                    await response.aread()
                    raise HTTPException(
                        status_code=response.status_code, detail=response.text
                    )

                async for chunk in response.aiter_text():
                    yield chunk
        except httpx.RequestError as e:
            logger.error("Failed to stream from AI Agent at %s: %s", agent_url, e)
            raise HTTPException(
                status_code=503,
                detail="The requested streaming AI Agent service is currently unavailable.",
            ) from e
