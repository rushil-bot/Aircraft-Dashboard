"""
Flight Delay Predictor - Serving Endpoint
=========================================
FastAPI application that serves the XGBoost flight delay prediction model.
"""

import json
from contextlib import asynccontextmanager
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, conint

# ---------------------------------------------------------------------------
# Paths & Globals
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
MODEL_DIR = SCRIPT_DIR / "model"

model = None
encoders = {}
feature_columns = []

# ---------------------------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------------------------
class PredictRequest(BaseModel):
    month: int
    day_of_week: int        # 1=Monday, 7=Sunday
    dep_hour: int           # 0-23
    reporting_airline: str  # e.g., 'UA', 'DL'
    origin: str             # e.g., 'SFO'
    dest: str               # e.g., 'JFK'
    distance: int

class PredictResponse(BaseModel):
    is_delayed: bool
    delay_probability: float
    feature_importance_note: str = "Values >= 50% probability predict a 15+ minute delay."

# ---------------------------------------------------------------------------
# App Lifecycle — Load Model on Startup
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, encoders, feature_columns
    
    try:
        print("Loading ML artifacts...")
        model = joblib.load(MODEL_DIR / "xgboost_delay_model.joblib")
        encoders = joblib.load(MODEL_DIR / "label_encoders.joblib")
        
        with open(MODEL_DIR / "feature_columns.json", "r") as f:
            feature_columns = json.load(f)
            
        print("✅ Models loaded successfully!")
    except FileNotFoundError as e:
        print(f"❌ Error loading model: {e}")
        print("Please ensure you have run train.py first.")
        # Proceed anyway so container stays up, but predictions will fail
    yield

# ---------------------------------------------------------------------------
# App Setup
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Flight Delay Predictor API",
    description="Microservice for predicting aircraft delays",
    version="1.0.0",
    lifespan=lifespan
)

# In production, gateway handles CORS, but good for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/health")
def health_check():
    """Simple health check for Docker/Kubernetes."""
    return {"status": "healthy", "model_loaded": model is not None}

@app.post("/predict", response_model=PredictResponse)
def predict_delay(req: PredictRequest):
    """
    Predict if a flight will be delayed >= 15 minutes.
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model is not loaded.")

    try:
        # 1. Feature Engineering (mimic training logic)
        is_weekend = 1 if req.day_of_week >= 6 else 0
        
        # 2. Categorical Encoding (safely handle unseen values)
        encoded_inputs = {}
        for col, raw_val in [
            ('Reporting_Airline', req.reporting_airline),
            ('Origin', req.origin),
            ('Dest', req.dest)
        ]:
            le = encoders[col]
            # If we've never seen this airport/airline before, default to "UNKNOWN"
            # (assuming we used "UNKNOWN" in training, otherwise just use the first item as fallback)
            val = raw_val.upper()
            if val not in le.classes_:
                if "UNKNOWN" in le.classes_:
                    val = "UNKNOWN"
                else:
                    # Fallback to the most common or specific class to prevent crash
                    # In a robust system, we would have an 'Other' category
                    val = le.classes_[0] 
            
            encoded_inputs[col] = le.transform([val])[0]
        
        # 3. Assemble DataFrame in the exact order the model expects
        input_dict = {
            "Month": [req.month],
            "DayOfWeek": [req.day_of_week],
            "dep_hour": [req.dep_hour],
            "is_weekend": [is_weekend],
            "Reporting_Airline": [encoded_inputs['Reporting_Airline']],
            "Origin": [encoded_inputs['Origin']],
            "Dest": [encoded_inputs['Dest']],
            "Distance": [req.distance]
        }
        
        # Make sure dataframe columns match `feature_columns` perfectly
        df = pd.DataFrame(input_dict)[feature_columns]

        # 4. Predict
        proba = model.predict_proba(df)[0][1] # Probability of class 1 (Delayed)
        
        return PredictResponse(
            is_delayed=bool(proba >= 0.50),
            delay_probability=round(float(proba), 3)
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("serve:app", host="0.0.0.0", port=8001, reload=True)
