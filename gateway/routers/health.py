"""System health check endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel
from gateway.utils.cache import cache

router = APIRouter(tags=["System"])


class HealthResponse(BaseModel):
    """Schema for health check response."""

    status: str
    version: str
    cache: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for container orchestration (Docker / K8s)."""
    return HealthResponse(
        status="healthy",
        version="2.0.0",
        cache=cache.mode,
    )
