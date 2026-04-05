"""
Aircraft Dashboard — FastAPI API Gateway

Replaces the legacy Flask backend. Serves as the central API gateway
that routes requests to external aviation APIs and (soon) to internal
AI agent microservices.

Features:
  - Async HTTP calls via httpx
  - Redis-backed caching (falls back to in-memory if Redis unavailable)
  - CORS middleware for React frontend
  - Health check endpoint
  - Pydantic request/response models
"""

import time
import logging
from contextlib import asynccontextmanager
from typing import Optional

import httpx
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)
logger = logging.getLogger("gateway")

# ---------------------------------------------------------------------------
# Cache (in-memory fallback; Redis integration in docker-compose)
# ---------------------------------------------------------------------------
CACHE_TTL = 60 * 10  # 10 minutes

_memory_cache: dict[str, tuple[float, dict]] = {}
_redis_client = None


async def _try_connect_redis():
    """Attempt to connect to Redis. Returns client or None."""
    try:
        import os
        import redis.asyncio as aioredis
        import json  # noqa: F811 — only used inside this function

        redis_host = os.environ.get("REDIS_HOST", "localhost")
        redis_port = int(os.environ.get("REDIS_PORT", "6379"))
        client = aioredis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        await client.ping()
        logger.info("✅ Connected to Redis")
        return client
    except Exception:
        logger.warning("⚠️  Redis unavailable — falling back to in-memory cache")
        return None


async def cache_get(key: str) -> Optional[dict]:
    """Retrieve a value from cache (Redis or in-memory)."""
    import json

    if _redis_client:
        raw = await _redis_client.get(key)
        if raw:
            return json.loads(raw)
        return None

    # In-memory fallback
    if key in _memory_cache:
        ts, data = _memory_cache[key]
        if time.time() - ts < CACHE_TTL:
            return data
        del _memory_cache[key]
    return None


async def cache_set(key: str, data: dict):
    """Store a value in cache (Redis or in-memory)."""
    import json

    if _redis_client:
        await _redis_client.setex(key, CACHE_TTL, json.dumps(data))
    else:
        _memory_cache[key] = (time.time(), data)


# ---------------------------------------------------------------------------
# Application lifecycle
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _redis_client
    _redis_client = await _try_connect_redis()
    logger.info("🚀 Gateway started")
    yield
    if _redis_client:
        await _redis_client.close()
    logger.info("👋 Gateway shutting down")


# ---------------------------------------------------------------------------
# FastAPI app
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


# ---------------------------------------------------------------------------
# Pydantic response models
# ---------------------------------------------------------------------------
class HealthResponse(BaseModel):
    status: str
    version: str
    cache: str


class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None


# ---------------------------------------------------------------------------
# Shared HTTP client
# ---------------------------------------------------------------------------
_http_client: Optional[httpx.AsyncClient] = None


def _get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(timeout=15.0)
    return _http_client


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Health check endpoint for container orchestration (Docker / K8s)."""
    return HealthResponse(
        status="healthy",
        version="2.0.0",
        cache="redis" if _redis_client else "memory",
    )


@app.get("/api/aircraft_lookup", tags=["Aviation Data"])
async def aircraft_lookup(
    registration: Optional[str] = Query(None, description="Aircraft registration (e.g. N12345)"),
    callsign: Optional[str] = Query(None, description="Flight callsign (e.g. UAL123)"),
):
    """
    Look up aircraft information by registration or callsign.
    Data sourced from ADSBdb.
    """
    reg = (registration or "").strip().upper()
    cs = (callsign or "").strip().upper()

    if reg:
        key = f"registration:{reg}"
        url = f"https://api.adsbdb.com/v0/aircraft/{reg}"
    elif cs:
        key = f"callsign:{cs}"
        url = f"https://api.adsbdb.com/v0/callsign/{cs}"
    else:
        raise HTTPException(status_code=400, detail="No registration or callsign provided.")

    # Check cache
    cached = await cache_get(key)
    if cached:
        logger.info(f"Cache HIT: {key}")
        return cached

    # Fetch from upstream
    try:
        client = _get_http_client()
        r = await client.get(url)
        r.raise_for_status()
        data = r.json()
        await cache_set(key, data)
        logger.info(f"Fetched & cached: {key}")
        return data
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404 and cs:
            raise HTTPException(
                status_code=404,
                detail=f'No aircraft found for callsign "{cs}". Did you mean to search by Registration instead?',
            )
        elif e.response.status_code == 404 and reg:
            raise HTTPException(
                status_code=404,
                detail=f'No aircraft found for registration "{reg}". Double-check the registration number (e.g. N787UA).',
            )
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Upstream API error ({e.response.status_code}). Please try again later.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lookup failed. Please try again later.")


@app.get("/api/airport_lookup", tags=["Aviation Data"])
async def airport_lookup(
    code: Optional[str] = Query(None, description="ICAO (4-char) or IATA (3-char) airport code"),
):
    """
    Look up airport information by ICAO or IATA code.
    Data sourced from airport-data.com.
    """
    code_clean = (code or "").strip().upper()
    if not code_clean:
        raise HTTPException(status_code=400, detail="No airport code provided.")

    if len(code_clean) == 4:
        key = f"icao:{code_clean}"
        url = f"https://airport-data.com/api/ap_info.json?icao={code_clean}"
    elif len(code_clean) == 3:
        key = f"iata:{code_clean}"
        url = f"https://airport-data.com/api/ap_info.json?iata={code_clean}"
    else:
        raise HTTPException(status_code=400, detail="Code must be 3 (IATA) or 4 (ICAO) characters.")

    # Check cache
    cached = await cache_get(key)
    if cached:
        logger.info(f"Cache HIT: {key}")
        return cached

    # Fetch from upstream
    try:
        client = _get_http_client()
        r = await client.get(url)
        r.raise_for_status()
        data = r.json()
        await cache_set(key, data)
        logger.info(f"Fetched & cached: {key}")
        return data
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail=f'No airport found for code "{code_clean}". Make sure you\'re using a valid IATA (e.g. "SFO") or ICAO (e.g. "KSFO") code.',
            )
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Upstream API error ({e.response.status_code}). Please try again later.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lookup failed. Please try again later.")


# ---------------------------------------------------------------------------
# AI Agent Proxy Routes
# ---------------------------------------------------------------------------

@app.post("/api/agents/delay-predictor/predict", tags=["AI Agents"])
async def proxy_delay_predictor(req_body: dict):
    """
    Proxy request to the internal delay-predictor microservice.
    """
    import os
    
    # Internal service URL (docker-compose hostname)
    # Default to localhost if running outside docker
    agent_host = os.environ.get("DELAY_PREDICTOR_HOST", "delay-predictor")
    url = f"http://{agent_host}:8001/predict"

    try:
        client = _get_http_client()
        r = await client.post(url, json=req_body)
        
        # If the internal service throws a 422 or 400, pass it back transparently
        if r.status_code >= 400:
            raise HTTPException(status_code=r.status_code, detail=r.json())
            
        return r.json()
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to delay-predictor: {e}")
        raise HTTPException(
            status_code=503, 
            detail="Delay predictor service is currently unavailable. Ensure the container is running."
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
