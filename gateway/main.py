"""
Aircraft Dashboard — FastAPI API Gateway

Replaces the legacy Flask backend. Serves as the central API gateway
that routes requests to external aviation APIs and to internal AI agent microservices.
Refactored using SOLID principles.

Features:
  - Async HTTP calls via httpx
  - Redis-backed caching (falls back to in-memory if Redis unavailable)
  - CORS middleware for React frontend
  - Modular routing via APIRouter
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from gateway.utils.http_client import HTTPClient
from gateway.utils.cache import cache

from gateway.routers import health, lookups, agents

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)
logger = logging.getLogger("gateway.main")


# ---------------------------------------------------------------------------
# Application lifecycle
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Lifespan manager to setup and teardown global connections."""
    # Setup global clients
    await cache.connect()
    HTTPClient.get_client()

    logger.info("[PASS] Gateway started successfully")
    yield

    # Teardown global clients
    await cache.close()
    await HTTPClient.close()

    logger.info("[INFO] Gateway shutting down")


# ---------------------------------------------------------------------------
# FastAPI app initialization
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Aircraft Dashboard API Gateway",
    description="Central gateway for aviation data lookups and AI agent services.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Sub-Routers
app.include_router(health.router)
app.include_router(lookups.router)
app.include_router(agents.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("gateway.main:app", host="0.0.0.0", port=8000, reload=True)
