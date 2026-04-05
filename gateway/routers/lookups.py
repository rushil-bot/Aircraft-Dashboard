"""Endpoints for retrieving raw aviation data lookups."""

from typing import Optional
from fastapi import APIRouter, Query
from gateway.services.aviation import AviationDataService

router = APIRouter(tags=["Aviation Data"], prefix="/api")


@router.get("/aircraft_lookup")
async def aircraft_lookup(
    registration: Optional[str] = Query(
        None, description="Aircraft registration (e.g. N12345)"
    ),
    callsign: Optional[str] = Query(None, description="Flight callsign (e.g. UAL123)"),
):
    """
    Look up aircraft information by registration or callsign.
    Data sourced from ADSBdb.
    """
    return await AviationDataService.lookup_aircraft(registration, callsign)


@router.get("/airport_lookup")
async def airport_lookup(
    code: Optional[str] = Query(
        None, description="ICAO (4-char) or IATA (3-char) airport code"
    ),
):
    """
    Look up airport information by ICAO or IATA code.
    Data sourced from airport-data.com.
    """
    return await AviationDataService.lookup_airport(code)
