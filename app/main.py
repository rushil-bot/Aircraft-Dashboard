import time
from flask import Flask, jsonify, render_template, request
import requests

app = Flask(__name__)

# Simple in-memory cache: {key: (timestamp, data)}
cache = {}
CACHE_TTL = 60 * 10  # cache for 10 minutes

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/api/aircraft_lookup", methods=["GET"])
def aircraft_lookup():
    reg = request.args.get("registration", "").strip().upper()
    callsign = request.args.get("callsign", "").strip().upper()

    if reg:
        key = f"registration:{reg}"
        url = f"https://api.adsbdb.com/v0/aircraft/{reg}"
    elif callsign:
        key = f"callsign:{callsign}"
        url = f"https://api.adsbdb.com/v0/callsign/{callsign}"
    else:
        return jsonify({"error": "No registration or callsign provided."}), 400

    # Check cache
    now = time.time()
    if key in cache:
        cached_time, cached_data = cache[key]
        if now - cached_time < CACHE_TTL:
            return jsonify(cached_data)

    # Not cached or expired, fetch fresh data
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        cache[key] = (now, data)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": "Lookup failed", "details": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)