"""
Route Recommender - Serving Endpoint
======================================
FastAPI microservice that returns ranked flight route recommendations
based on predicted delay probability for all viable airline/hour
combinations on a given origin-destination pair.
"""

# pylint: disable=duplicate-code

import json
from contextlib import asynccontextmanager
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Paths & Globals
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
MODEL_DIR = SCRIPT_DIR / "model"

# Departure hours considered for candidate generation (06:00–22:00)
CANDIDATE_HOURS = list(range(6, 23))

# pylint: disable=invalid-name
model_instance = None
encoders = {}
feature_columns = []
route_index = {}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class RecommendRequest(BaseModel):
    """Schema for a route recommendation request."""

    origin: str
    dest: str
    month: int = Field(..., ge=1, le=12)
    day_of_week: int = Field(..., ge=1, le=7)  # 1=Monday, 7=Sunday
    top_n: int = Field(default=5, ge=1, le=10)


class RouteOption(BaseModel):
    """A single ranked route recommendation."""

    rank: int
    airline: str
    dep_hour: int
    delay_probability: float
    label: str


class RecommendResponse(BaseModel):
    """Schema for the full recommendation response."""

    origin: str
    dest: str
    recommendations: list[RouteOption]
    model_note: str = (
        "Rankings are based on predicted probability of a 15+ minute departure delay. "
        "Lower probability indicates reduced delay risk."
    )


# ---------------------------------------------------------------------------
# App Lifecycle
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Load ML artifacts and route index once on application startup."""
    # pylint: disable=global-statement
    global model_instance, encoders, feature_columns, route_index

    try:
        print("[INFO] Loading ML artifacts...")
        model_instance = joblib.load(MODEL_DIR / "lgbm_route_model.joblib")
        encoders = joblib.load(MODEL_DIR / "label_encoders.joblib")
        route_index = joblib.load(MODEL_DIR / "route_index.joblib")

        with open(MODEL_DIR / "feature_columns.json", "r", encoding="utf-8") as f:
            feature_columns = json.load(f)

        print("[PASS] All artifacts loaded successfully.")
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"[FAIL] Error loading artifacts: {e}")
        print("Ensure train.py has been executed before starting the server.")
    yield


# ---------------------------------------------------------------------------
# App Setup
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Route Recommender API",
    description="Microservice for recommending optimal flight routes via LightGBM",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _encode_value(col: str, raw_val: str) -> int:
    """
    Encode a categorical string value using the stored LabelEncoder.
    Falls back to UNKNOWN for values not seen during training.
    """
    le = encoders[col]
    val = raw_val.upper()
    if val not in le.classes_:
        val = "UNKNOWN" if "UNKNOWN" in le.classes_ else le.classes_[0]
    return int(le.transform([val])[0])


def _risk_label(prob: float, hour: int) -> str:
    """Produce a human-readable risk label string for a given probability."""
    time_str = f"{hour:02d}:00"
    if prob < 0.30:
        risk = "Low Risk"
    elif prob < 0.60:
        risk = "Medium Risk"
    else:
        risk = "High Risk"
    return f"{time_str} — {risk}"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/health")
def health_check():
    """Health check endpoint for Docker orchestration."""
    return {"status": "healthy", "model_loaded": model_instance is not None}


@app.post("/recommend", response_model=RecommendResponse)
def recommend_routes(req: RecommendRequest):  # pylint: disable=too-many-locals
    """
    Return the top N airline/departure-hour combinations with the lowest
    predicted delay probability for the requested origin-destination pair.

    Raises a 404 if the route was not observed in training data.
    """
    if model_instance is None:
        raise HTTPException(status_code=503, detail="Model is not loaded.")

    origin = req.origin.strip().upper()
    dest = req.dest.strip().upper()
    route_key = f"{origin}_{dest}"

    if route_key not in route_index:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Route {origin} to {dest} was not found in training data. "
                "Verify the airport codes and try again."
            ),
        )

    route_data = route_index[route_key]
    known_airlines = route_data["airlines"]
    distance = route_data["distance"]
    is_weekend = 1 if req.day_of_week >= 6 else 0

    # Build candidate DataFrame (all airline x hour combinations)
    rows = []
    for airline in known_airlines:
        for hour in CANDIDATE_HOURS:
            rows.append(
                {
                    "Month": req.month,
                    "DayOfWeek": req.day_of_week,
                    "dep_hour": hour,
                    "is_weekend": is_weekend,
                    "Reporting_Airline": _encode_value("Reporting_Airline", airline),
                    "Origin": _encode_value("Origin", origin),
                    "Dest": _encode_value("Dest", dest),
                    "Distance": distance,
                    "_airline_raw": airline,
                    "_hour": hour,
                }
            )

    candidates = pd.DataFrame(rows)
    feature_df = candidates[feature_columns]

    # Vectorised batch prediction — single model call for all candidates
    probabilities = model_instance.predict_proba(feature_df)[:, 1]
    candidates = candidates.copy()
    candidates["delay_probability"] = probabilities

    top = candidates.nsmallest(req.top_n, "delay_probability").reset_index(drop=True)

    recommendations = [
        RouteOption(
            rank=idx + 1,
            airline=row["_airline_raw"],
            dep_hour=int(row["_hour"]),
            delay_probability=round(float(row["delay_probability"]), 3),
            label=_risk_label(float(row["delay_probability"]), int(row["_hour"])),
        )
        for idx, (_, row) in enumerate(top.iterrows())
    ]

    return RecommendResponse(
        origin=origin,
        dest=dest,
        recommendations=recommendations,
    )


if __name__ == "__main__":
    import uvicorn  # pylint: disable=import-outside-toplevel

    uvicorn.run("serve:app", host="0.0.0.0", port=8004, reload=True)
