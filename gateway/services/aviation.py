import logging
import httpx
from fastapi import HTTPException
from gateway.utils.http import HTTPClient
from gateway.utils.cache import cache

logger = logging.getLogger("gateway.services.aviation")

class AviationDataService:
    """
    Handles business logic for retrieving aviation data.
    Follows SRP by separating API communication logic from FastAPI route parsing.
    """
    
    @staticmethod
    async def lookup_aircraft(registration: str = None, callsign: str = None) -> dict:
        """Fetch aircraft by reg or callsign."""
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

        cached = await cache.get(key)
        if cached:
            logger.info(f"Cache HIT: {key}")
            return cached

        try:
            client = HTTPClient.get_client()
            r = await client.get(url)
            r.raise_for_status()
            data = r.json()
            await cache.set(key, data)
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
                    detail=f'No aircraft found for registration "{reg}". Double-check the registration number.',
                )
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Upstream API error ({e.response.status_code}). Please try again later.",
            )
        except Exception as e:
            logger.error(f"Aircraft lookup failed: {e}")
            raise HTTPException(status_code=500, detail="Lookup failed. Please try again later.")

    @staticmethod
    async def lookup_airport(code: str) -> dict:
        """Fetch airport by ICAO or IATA."""
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

        cached = await cache.get(key)
        if cached:
            logger.info(f"Cache HIT: {key}")
            return cached

        try:
            client = HTTPClient.get_client()
            r = await client.get(url)
            r.raise_for_status()
            data = r.json()
            await cache.set(key, data)
            logger.info(f"Fetched & cached: {key}")
            return data
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail=f'No airport found for code "{code_clean}". Make sure you\'re using a valid IATA or ICAO code.',
                )
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Upstream API error ({e.response.status_code}). Please try again later.",
            )
        except Exception as e:
            logger.error(f"Airport lookup failed: {e}")
            raise HTTPException(status_code=500, detail="Lookup failed. Please try again later.")
