# app/data_scraper.py
from database import get_session, Arrival, Departure
import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup as bs
import time
import json


def scrape_sfo_arrivals():
    options = Options()
    options.add_argument("--headless")  # Run Chrome headless
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=options)

    url = "https://www.flightview.com/airport/SFO-San_Francisco-CA/arrivals"
    driver.get(url)
    
    # Wait for JavaScript to load flight data - increase if needed
    time.sleep(1)  
    
    arrivals = []
    print("--------------------Scraping SFO arrivals...--------------------")


    #Start Scraping
    rows = driver.find_elements(By.CSS_SELECTOR, "tr")

    for row in rows:
        cells = row.find_elements(By.CSS_SELECTOR, "td.AirportFlightsTable_tableCell__HdEjQ")
        if len(cells) >= 7:
            airline = cells[0].find_element(By.CSS_SELECTOR, "div.AirportFlightsTable_airlineName___pxwc").text
            flight = cells[1].text
            origin = cells[2].text
            status = cells[3].find_element(By.TAG_NAME, "a").text
            scheduled = cells[4].text
            actual = cells[5].text
            gate = cells[6].text

            arrivals.append({
                "airline": airline,
                "flight": flight,
                "origin": origin,
                "status": status,
                "scheduled_time": scheduled,
                "actual_time": actual,
                "gate": gate,
            })
    with open('data//arrivals.jsonl', 'w') as f:
        for item in arrivals:
            f.write(json.dumps(item) + ',\n')
        f.close()
        session = get_session()
    session.query(Arrival).delete()  # Optional: clear old data
    for item in arrivals:
        flight = Arrival(
            airline=item["airline"],
            flight=item["flight"],
            origin=item["origin"],
            status=item["status"],
            scheduled_time=item["scheduled_time"],
            actual_time=item["actual_time"],
            gate=item["gate"],
            scrape_timestamp=datetime.datetime.now()
        )
        session.add(flight)
    session.commit()
    session.close()
    driver.quit()

    print("--------------------SFO arrivals scraped successfully and saved to DB.--------------------")

    return arrivals


def scrape_sfo_departures():
    options = Options()
    options.add_argument("--headless")  # Run Chrome headless
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=options)

    url = "https://www.flightview.com/airport/SFO-San_Francisco-CA/departures"
    driver.get(url)
    
    # Wait for JavaScript to load flight data - increase if needed
    time.sleep(1)  
    
    departures = []
    print("--------------------Scraping SFO departures...--------------------")

    rows = driver.find_elements(By.CSS_SELECTOR, "tr")

    for row in rows:
        cells = row.find_elements(By.CSS_SELECTOR, "td.AirportFlightsTable_tableCell__HdEjQ")
        if len(cells) >= 7:
            airline = cells[0].find_element(By.CSS_SELECTOR, "div.AirportFlightsTable_airlineName___pxwc").text
            flight = cells[1].text
            origin = cells[2].text
            status = cells[3].find_element(By.TAG_NAME, "a").text
            scheduled = cells[4].text
            actual = cells[5].text
            gate = cells[6].text

            departures.append({
                "airline": airline,
                "flight": flight,
                "origin": origin,
                "status": status,
                "scheduled_time": scheduled,
                "actual_time": actual,
                "gate": gate,
            })
    with open('data//departures.jsonl', 'w') as f:
        for item in departures:
            f.write(json.dumps(item) + ',\n')
        f.close()


    session = get_session()
    session.query(Departure).delete()  # Optional: clear old data
    for item in departures:
        flight = Departure(
            airline=item["airline"],
            flight=item["flight"],
            origin=item["origin"],
            status=item["status"],
            scheduled_time=item["scheduled_time"],
            actual_time=item["actual_time"],
            gate=item["gate"],
            scrape_timestamp=datetime.datetime.now()
        )
        session.add(flight)
    session.commit()
    session.close()
    driver.quit()
    print("--------------------SFO arrivals scraped successfully and saved to DB.--------------------")
    
    return departures
