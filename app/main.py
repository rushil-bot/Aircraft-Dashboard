from flask import Flask, render_template
from flask import jsonify
from flask import request
import requests

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/api/aircraft_lookup', methods=['GET'])
def aircraft_lookup():
    """Lookup aircraft or route by registration or callsign."""
    reg = request.args.get('registration', '').strip().upper()
    callsign = request.args.get('callsign', '').strip().upper()
    result = {}

    if reg:
        adsbdb_url = f"https://api.adsbdb.com/v0/aircraft/{reg}"
    elif callsign:
        adsbdb_url = f"https://api.adsbdb.com/v0/callsign/{callsign}"
    else:
        return jsonify({"error": "No registration or callsign provided."}), 400

    try:
        r = requests.get(adsbdb_url)
        r.raise_for_status()
        result = r.json()
    except Exception as e:
        return jsonify({"error": "Lookup failed", "details": str(e)}), 500

    return jsonify(result)






if __name__ == "__main__":
    app.run(debug=True)
