from flask import Flask, render_template
from flask import jsonify
from database import init_db, get_session, Arrival, Departure
from data_scraper import scrape_sfo_arrivals, scrape_sfo_departures
import threading
import time
import os

app = Flask(__name__)

def update_cache_periodically():
    while True:
        scrape_sfo_arrivals()
        scrape_sfo_departures()
        print("--------------------Database updated--------------------")
        time.sleep(60)

@app.route('/')
def home():
    return render_template('home.html')

# @app.route('/arrivals')
# def arrivals():
#     session = get_session()
#     flights = session.query(Arrival).order_by(Arrival.scheduled_time).all()
#     session.close()
#     return render_template('index.html', flights=flights, label="Arrivals")

# @app.route('/departures')
# def departures():
#     session = get_session()
#     flights = session.query(Departure).order_by(Departure.scheduled_time).all()
#     session.close()
#     return render_template('index.html', flights=flights, label="Departures")

@app.route('/api/arrivals')
def api_arrivals():
    session = get_session()
    flights = session.query(Arrival).order_by(Arrival.scheduled_time).all()
    session.close()
    # Convert SQLAlchemy objects to dictionaries
    result = [dict(
        id=f.id,
        airline=f.airline,
        flight=f.flight,
        origin=f.origin,
        status=f.status,
        scheduled_time=f.scheduled_time,
        actual_time=f.actual_time,
        gate=f.gate
    ) for f in flights]
    return jsonify(result)

@app.route('/api/departures')
def api_departures():
    session = get_session()
    flights = session.query(Departure).order_by(Departure.scheduled_time).all()
    session.close()
    result = [dict(
        id=f.id,
        airline=f.airline,
        flight=f.flight,
        origin=f.origin,
        status=f.status,
        scheduled_time=f.scheduled_time,
        actual_time=f.actual_time,
        gate=f.gate
    ) for f in flights]
    return jsonify(result)



if __name__ == "__main__":
    init_db()  # Create tables if not present
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
        threading.Thread(target=update_cache_periodically, daemon=True).start()
    app.run(debug=True)
