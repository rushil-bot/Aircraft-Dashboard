"""AI Agent proxy endpoints."""

import os
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from gateway.services.agent_proxy import AgentProxyService

router = APIRouter(tags=["AI Agents"], prefix="/api/agents")


@router.post("/delay-predictor/predict")
async def proxy_delay_predictor(req_body: dict):
    """
    Proxy request to the internal delay-predictor microservice.
    """
    # Default to localhost if running outside docker
    agent_host = os.environ.get("DELAY_PREDICTOR_HOST", "delay-predictor")
    url = f"http://{agent_host}:8001/predict"
    return await AgentProxyService.request_agent(url, req_body)


@router.post("/nl-query/ask")
async def proxy_nl_query(req_body: dict):
    """
    Proxy natural language query to the internal nl-query microservice.
    Streams the response back to the client.
    """
    agent_host = os.environ.get("NL_QUERY_HOST", "nl-query")
    url = f"http://{agent_host}:8003/ask"

    return StreamingResponse(
        AgentProxyService.stream_agent(url, req_body), media_type="text/event-stream"
    )


@router.post("/route-recommender/recommend")
async def proxy_route_recommender(req_body: dict):
    """
    Proxy request to the internal route-recommender microservice.
    Returns ranked route options as a JSON response.
    """
    agent_host = os.environ.get("ROUTE_RECOMMENDER_HOST", "route-recommender")
    url = f"http://{agent_host}:8004/recommend"
    return await AgentProxyService.request_agent(url, req_body)
