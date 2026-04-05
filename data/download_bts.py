"""
BTS On-Time Performance Data Downloader & Preprocessor
======================================================
Downloads flight delay data from the Bureau of Transportation Statistics
and preprocesses it into a clean dataset for ML training.

Data source: https://www.transtats.bts.gov/
Dataset: "Reporting Carrier On-Time Performance (1987–present)"

Usage:
    python download_bts.py                    # Download latest 3 months
    python download_bts.py --year 2024        # Download all of 2024
    python download_bts.py --months 6         # Download latest 6 months
    python download_bts.py --skip-download    # Just preprocess existing raw data
"""

import argparse
import io
import os
import sys
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
RAW_DIR = SCRIPT_DIR / "raw"
PROCESSED_DIR = SCRIPT_DIR / "processed"

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# BTS download URL pattern
# ---------------------------------------------------------------------------
BTS_URL_TEMPLATE = (
    "https://transtats.bts.gov/PREZIP/"
    "On_Time_Reporting_Carrier_On_Time_Performance_1987_present_{year}_{month}.zip"
)

# Columns we actually need (the full CSV has 100+ columns)
KEEP_COLUMNS = [
    "Year",
    "Month",
    "DayofMonth",
    "DayOfWeek",
    "Reporting_Airline",     # 2-letter carrier code (e.g. "UA", "AA")
    "Origin",                # Origin airport IATA code
    "Dest",                  # Destination airport IATA code
    "CRSDepTime",            # Scheduled departure time (hhmm)
    "DepDelay",              # Departure delay in minutes
    "ArrDelay",              # Arrival delay in minutes
    "Cancelled",             # 1 if cancelled, 0 otherwise
    "Distance",              # Flight distance in miles
    "CarrierDelay",          # Delay due to carrier (minutes)
    "WeatherDelay",          # Delay due to weather (minutes)
    "NASDelay",              # Delay due to NAS (minutes)
    "SecurityDelay",         # Delay due to security (minutes)
    "LateAircraftDelay",     # Delay due to late arriving aircraft (minutes)
]


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------
def download_month(year: int, month: int) -> Path | None:
    """Download a single month of BTS data. Returns path to raw CSV or None."""
    csv_path = RAW_DIR / f"bts_{year}_{month:02d}.csv"

    if csv_path.exists():
        print(f"  ✓ Already downloaded: {csv_path.name}")
        return csv_path

    url = BTS_URL_TEMPLATE.format(year=year, month=month)
    print(f"  ↓ Downloading {year}-{month:02d}... ", end="", flush=True)

    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
    except requests.HTTPError as e:
        print(f"FAILED ({e})")
        return None
    except requests.ConnectionError:
        print("FAILED (connection error)")
        return None

    # Extract the CSV from the ZIP
    try:
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            csv_names = [n for n in zf.namelist() if n.endswith(".csv")]
            if not csv_names:
                print("FAILED (no CSV in ZIP)")
                return None
            with zf.open(csv_names[0]) as f:
                df = pd.read_csv(f, usecols=lambda c: c in KEEP_COLUMNS, low_memory=False)
                df.to_csv(csv_path, index=False)
                print(f"OK ({len(df):,} flights)")
                return csv_path
    except Exception as e:
        print(f"FAILED ({e})")
        return None


def download_range(year: int = None, months: int = 3) -> list[Path]:
    """Download a range of BTS data files."""
    downloaded = []

    if year:
        # Download all 12 months of a specific year
        print(f"\n📥 Downloading all of {year}...")
        for m in range(1, 13):
            path = download_month(year, m)
            if path:
                downloaded.append(path)
    else:
        # Download the latest N months
        print(f"\n📥 Downloading latest {months} months...")
        now = datetime.now()
        # BTS data has ~2-month lag, so start 3 months back
        start = now - timedelta(days=90 + (months * 30))
        for i in range(months):
            target = start + timedelta(days=i * 30)
            path = download_month(target.year, target.month)
            if path:
                downloaded.append(path)

    if not downloaded:
        print("\n⚠️  No data downloaded. See manual download instructions below.")
        print_manual_instructions()

    return downloaded


def print_manual_instructions():
    """Print instructions for manual download if automated download fails."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║              MANUAL DOWNLOAD INSTRUCTIONS                    ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  1. Go to: https://www.transtats.bts.gov/DL_SelectFields.aspx║
║     ?gnoession_ID=0&Table_ID=236                             ║
║                                                              ║
║  2. Select your desired year and months                      ║
║                                                              ║
║  3. Check these fields:                                      ║
║     - Year, Month, DayofMonth, DayOfWeek                     ║
║     - Reporting_Airline                                      ║
║     - Origin, Dest                                           ║
║     - CRSDepTime, DepDelay, ArrDelay                         ║
║     - Cancelled, Distance                                    ║
║     - CarrierDelay, WeatherDelay, NASDelay                   ║
║     - SecurityDelay, LateAircraftDelay                       ║
║                                                              ║
║  4. Click "Download" and save the ZIP file                   ║
║                                                              ║
║  5. Extract the CSV and place it in:                         ║
║     data/raw/                                                ║
║                                                              ║
║  6. Re-run: python download_bts.py --skip-download           ║
╚══════════════════════════════════════════════════════════════╝
    """)


# ---------------------------------------------------------------------------
# Preprocessing
# ---------------------------------------------------------------------------
def preprocess(raw_files: list[Path] = None) -> Path:
    """
    Clean and preprocess raw BTS data for ML training.

    Feature engineering:
      - dep_hour: scheduled departure hour (0-23)
      - is_weekend: 1 if Saturday or Sunday
      - delayed_15: binary target — 1 if arrival delay >= 15 min
      - delay_minutes: continuous target — arrival delay in minutes

    Returns path to the processed CSV.
    """
    if raw_files is None:
        raw_files = sorted(RAW_DIR.glob("bts_*.csv"))

    if not raw_files:
        print("❌ No raw data files found in data/raw/")
        print("   Run the download first, or place CSV files manually.")
        sys.exit(1)

    print(f"\n🔧 Preprocessing {len(raw_files)} file(s)...")

    # Load and concatenate all raw files
    dfs = []
    for f in raw_files:
        df = pd.read_csv(f, low_memory=False)
        dfs.append(df)
        print(f"  ✓ Loaded {f.name}: {len(df):,} rows")

    df = pd.concat(dfs, ignore_index=True)
    print(f"\n  Total raw rows: {len(df):,}")

    # --- Cleaning ---
    # Drop cancelled flights (can't measure delay on cancellations)
    before = len(df)
    df = df[df["Cancelled"] == 0].copy()
    print(f"  Dropped {before - len(df):,} cancelled flights")

    # Drop rows with missing delay values
    before = len(df)
    df = df.dropna(subset=["ArrDelay", "DepDelay"])
    print(f"  Dropped {before - len(df):,} rows with missing delay data")

    # --- Feature Engineering ---
    # Extract departure hour from CRSDepTime (format: hhmm, e.g. 1435 = 2:35 PM)
    df["dep_hour"] = (df["CRSDepTime"] // 100).astype(int).clip(0, 23)

    # Weekend flag (DayOfWeek: 1=Monday ... 7=Sunday)
    df["is_weekend"] = (df["DayOfWeek"] >= 6).astype(int)

    # Binary target: delayed by 15+ minutes (FAA standard definition)
    df["delayed_15"] = (df["ArrDelay"] >= 15).astype(int)

    # Continuous target: arrival delay in minutes (clip extreme outliers)
    df["delay_minutes"] = df["ArrDelay"].clip(-60, 300)

    # --- Select final features ---
    feature_cols = [
        # Features
        "Year",
        "Month",
        "DayOfWeek",
        "dep_hour",
        "is_weekend",
        "Reporting_Airline",
        "Origin",
        "Dest",
        "Distance",
        # Targets
        "delayed_15",
        "delay_minutes",
    ]

    df_final = df[feature_cols].copy()

    # Drop any remaining NaN rows
    before = len(df_final)
    df_final = df_final.dropna()
    if before - len(df_final) > 0:
        print(f"  Dropped {before - len(df_final):,} remaining NaN rows")

    # --- Save ---
    output_path = PROCESSED_DIR / "flights_processed.csv"
    df_final.to_csv(output_path, index=False)

    print(f"\n✅ Processed dataset saved to: {output_path}")
    print(f"   Rows: {len(df_final):,}")
    print(f"   Columns: {list(df_final.columns)}")

    # --- Quick stats ---
    delay_rate = df_final["delayed_15"].mean() * 100
    avg_delay = df_final["delay_minutes"].mean()
    print(f"\n📊 Dataset Statistics:")
    print(f"   Delay rate (≥15 min): {delay_rate:.1f}%")
    print(f"   Average delay: {avg_delay:.1f} minutes")
    print(f"   Top carriers: {df_final['Reporting_Airline'].value_counts().head(5).to_dict()}")
    print(f"   Top origins:  {df_final['Origin'].value_counts().head(5).to_dict()}")

    return output_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Download and preprocess BTS flight delay data"
    )
    parser.add_argument(
        "--year", type=int, default=None,
        help="Download all 12 months of a specific year (e.g. 2024)"
    )
    parser.add_argument(
        "--months", type=int, default=3,
        help="Number of recent months to download (default: 3)"
    )
    parser.add_argument(
        "--skip-download", action="store_true",
        help="Skip download and just preprocess existing raw data"
    )
    args = parser.parse_args()

    if not args.skip_download:
        downloaded = download_range(year=args.year, months=args.months)
        if not downloaded:
            return
    
    preprocess()


if __name__ == "__main__":
    main()
