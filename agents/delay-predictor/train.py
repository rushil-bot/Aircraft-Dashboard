"""
Flight Delay Predictor - Training Script
========================================
This script trains an XGBoost model to predict whether a flight
will be delayed by 15 minutes or more.

It reads the preprocessed data from `data/processed/flights_processed.csv`,
handles categorical encoding, trains the model, and saves the artifacts
to the `model/` directory.

# Script and processed CSV can be uploaded to cloud environments for GPU training.
# Download the resulting .joblib files back to the local machine.
"""

import argparse
import json
import time
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# Adjust paths assuming this might be run from the root directory or inside the agent dir
# Anchor relative to this script, with a fallback.
try:
    SCRIPT_DIR = Path(__file__).resolve().parent
    ROOT_DIR = SCRIPT_DIR.parent.parent
except NameError:
    # Fallback for notebook environments
    SCRIPT_DIR = Path(".").resolve()
    ROOT_DIR = SCRIPT_DIR.parent.parent

DATA_PATH = ROOT_DIR / "data" / "processed" / "flights_processed.csv"
MODEL_DIR = SCRIPT_DIR / "model"

MODEL_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Training Pipeline
# ---------------------------------------------------------------------------
# pylint: disable=too-many-locals
def train_model(data_path: Path, output_dir: Path):
    """
    Load preprocessed flight data, perform categorical encoding,
    split data, and train the XGBoost delay predictor model.
    """
    if not data_path.exists():
        print(f"[FAIL] Data file not found: {data_path}")
        print("Execute data/download_bts.py first.")
        return

    print(f"[INFO] Loading dataset from {data_path}...")
    df = pd.read_csv(data_path)
    print(f"  Rows loaded: {len(df):,}")

    # Features and Target
    # Drop 'delay_minutes' as it leaks the target.
    # Retain 'Month' and 'DayOfWeek' features.
    df = df.drop(columns=["delay_minutes", "FlightDate"])
    y = df["delayed_15"].astype(int)

    # Select features
    features = [
        "Month",
        "DayOfWeek",
        "dep_hour",
        "is_weekend",
        "Reporting_Airline",
        "Origin",
        "Dest",
        "Distance",
    ]
    X = df[features].copy()  # pylint: disable=invalid-name

    # -----------------------------------------------------------------------
    # Categorical Encoding
    # -----------------------------------------------------------------------
    print("[INFO] Encoding categorical variables...")
    categorical_cols = ["Reporting_Airline", "Origin", "Dest"]
    encoders = {}

    for col in categorical_cols:
        le = LabelEncoder()
        # Filling NaNs with "UNKNOWN" just in case
        X[col] = X[col].fillna("UNKNOWN").astype(str)
        X[col] = le.fit_transform(X[col])
        encoders[col] = le
        print(f"  Encoded {col} ({len(le.classes_)} unique classes)")

    # Save the encoders for the serving API
    encoder_path = output_dir / "label_encoders.joblib"
    joblib.dump(encoders, encoder_path)
    print(f"  Saved label encoders to {encoder_path}")

    # -----------------------------------------------------------------------
    # Train / Test Split
    # -----------------------------------------------------------------------
    print("[INFO] Splitting data...")
    # pylint: disable=invalid-name
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"  Train shape: {X_train.shape}")
    print(f"  Test shape:  {X_test.shape}")

    # -----------------------------------------------------------------------
    # Train Model
    # -----------------------------------------------------------------------
    print("[INFO] Training XGBoost model...")
    # Lightweight parameters optimized for speed.
    clf = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
        n_jobs=-1,  # Use all CPU cores
        eval_metric="logloss",
    )

    start_time = time.time()
    clf.fit(X_train, y_train)
    duration = time.time() - start_time
    print(f"  Training completed in {duration:.1f} seconds")

    # -----------------------------------------------------------------------
    # Evaluate
    # -----------------------------------------------------------------------
    print("[INFO] Evaluating model...")
    y_pred = clf.predict(X_test)
    y_proba = clf.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_proba)

    print("\n--- Model Metrics ---")
    print(f"Accuracy: {acc:.4f}")
    print(f"ROC-AUC:  {auc:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=["On Time", "Delayed"]))

    # Save metrics
    metrics = {
        "accuracy": acc,
        "roc_auc": auc,
        "training_time_seconds": duration,
        "records_trained_on": len(X_train),
    }
    with open(output_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    # -----------------------------------------------------------------------
    # Save Artifacts
    # -----------------------------------------------------------------------
    model_path = output_dir / "xgboost_delay_model.joblib"
    joblib.dump(clf, model_path)
    print(f"\n[PASS] Model saved to {model_path}")

    # Also save the expected feature columns in order
    with open(output_dir / "feature_columns.json", "w", encoding="utf-8") as f:
        json.dump(features, f, indent=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train the Delay Predictor model")
    parser.add_argument(
        "--data", type=str, default=str(DATA_PATH), help="Path to processed CSV data"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(MODEL_DIR),
        help="Output directory for model artifacts",
    )
    args = parser.parse_args()

    train_model(Path(args.data), Path(args.output))
