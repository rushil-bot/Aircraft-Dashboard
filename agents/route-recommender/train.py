"""
Route Recommender - Training Script
=====================================
Trains a LightGBM binary classifier on BTS flight data to predict the
probability of a 15+ minute departure delay.

Produces five artifacts in the model/ directory:
    lgbm_route_model.joblib  - Trained LightGBM classifier
    label_encoders.joblib    - Categorical encoders (airline, origin, dest)
    route_index.joblib       - Per-route airline set and median distance
    feature_columns.json     - Ordered feature list for inference
    metrics.json             - Training and evaluation metrics
"""

import argparse
import json
import time
from pathlib import Path

import joblib
import lightgbm as lgb
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
try:
    SCRIPT_DIR = Path(__file__).resolve().parent
    ROOT_DIR = SCRIPT_DIR.parent.parent
except NameError:
    SCRIPT_DIR = Path(".").resolve()
    ROOT_DIR = SCRIPT_DIR.parent.parent

DATA_PATH = ROOT_DIR / "data" / "processed" / "flights_processed.csv"
MODEL_DIR = SCRIPT_DIR / "model"

MODEL_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Training Pipeline
# ---------------------------------------------------------------------------
# pylint: disable=too-many-locals
def train_model(data_path: Path, output_dir: Path) -> None:
    """
    Load preprocessed flight data, build a route index, encode categoricals,
    and train a LightGBM delay classifier. Saves all artifacts to output_dir.
    """
    if not data_path.exists():
        print(f"[FAIL] Data file not found: {data_path}")
        print("Execute data/download_bts.py first.")
        return

    print(f"[INFO] Loading dataset from {data_path}...")
    df = pd.read_csv(data_path)
    print(f"  Rows loaded: {len(df):,}")

    # Normalise string columns
    df["Origin"] = df["Origin"].str.strip().str.upper()
    df["Dest"] = df["Dest"].str.strip().str.upper()
    df["Reporting_Airline"] = df["Reporting_Airline"].str.strip().str.upper()

    # -----------------------------------------------------------------------
    # Build Route Index
    # -----------------------------------------------------------------------
    print("[INFO] Building route index...")
    route_index = {}
    for (origin, dest), group in df.groupby(["Origin", "Dest"]):
        key = f"{origin}_{dest}"
        route_index[key] = {
            "airlines": sorted(
                group["Reporting_Airline"].dropna().unique().tolist()
            ),
            "distance": int(group["Distance"].median()),
        }

    joblib.dump(route_index, output_dir / "route_index.joblib")
    print(f"  Route index built: {len(route_index):,} unique routes")

    # -----------------------------------------------------------------------
    # Feature Selection
    # -----------------------------------------------------------------------
    df = df.drop(columns=["delay_minutes", "FlightDate"], errors="ignore")
    y = df["delayed_15"].astype(int)

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
        X[col] = X[col].fillna("UNKNOWN").astype(str)
        X[col] = le.fit_transform(X[col])
        encoders[col] = le
        print(f"  Encoded {col} ({len(le.classes_)} unique classes)")

    joblib.dump(encoders, output_dir / "label_encoders.joblib")
    print("  Saved label encoders.")

    # -----------------------------------------------------------------------
    # Train / Test Split
    # -----------------------------------------------------------------------
    print("[INFO] Splitting data...")
    X_train, X_test, y_train, y_test = train_test_split(  # pylint: disable=invalid-name
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"  Train shape: {X_train.shape}")
    print(f"  Test shape:  {X_test.shape}")

    # -----------------------------------------------------------------------
    # Train LightGBM Model
    # -----------------------------------------------------------------------
    print("[INFO] Training LightGBM classifier...")
    clf = lgb.LGBMClassifier(
        n_estimators=300,
        learning_rate=0.05,
        num_leaves=63,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
        verbosity=-1,
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

    metrics = {
        "accuracy": acc,
        "roc_auc": auc,
        "training_time_seconds": duration,
        "records_trained_on": len(X_train),
    }
    with open(output_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    # -----------------------------------------------------------------------
    # Save Model & Feature Columns
    # -----------------------------------------------------------------------
    model_path = output_dir / "lgbm_route_model.joblib"
    joblib.dump(clf, model_path)
    print(f"\n[PASS] Model saved to {model_path}")

    with open(output_dir / "feature_columns.json", "w", encoding="utf-8") as f:
        json.dump(features, f, indent=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train the Route Recommender model")
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
