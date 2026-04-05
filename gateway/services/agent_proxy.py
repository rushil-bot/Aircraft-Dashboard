import logging
import httpx
from fastapi import HTTPException
from gateway.utils.http import HTTPClient

logger = logging.getLogger("gateway.services.agents")

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
                detail = r.json() if r.headers.get("content-type") == "application/json" else r.text
                raise HTTPException(status_code=r.status_code, detail=detail)
                
            return r.json()
            
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to AI Agent at {agent_url}: {e}")
            raise HTTPException(
                status_code=503, 
                detail="The requested AI Agent service is currently unavailable. Ensure the container is running."
            )
