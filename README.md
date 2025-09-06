# Aircraft Lookup Dashboard

Welcome to the **Aviation Lookup Dashboard** — your personal gateway to exploring the fascinating world of aircraft and Airport data! This app lets you quickly search for any plane or Airport by registration number or callsign, and see detailed info, recent routes, and stunning photos — all powered by the awesome [ADSBdb API](https://www.adsbdb.com) and [Airport-Data API](https://airport-data.com/).

---

## 🚀 Features

- **Lightning-fast Aircraft/Airport Lookup:** Just enter a tail number (e.g., `N12345`), flight callsign (e.g., `UAL151`) or Airport ICAO/IATA (e.g.,`KSFO`) to get instant data on the aircraft’s details and recent flight activity.
- **Search Mode Selector:** Toggle easily between searching by *Registration* or *Callsign*.
- **History of Recent Searches:** Keep track of your last 5 lookups and jump back to them with a single click — perfect for the avid plane spotter.
- **Image Gallery:** View multiple photos of the aircraft, showcasing different angles and liveries (when available).
- **Smart Backend Caching:** Cached API responses for 10 minutes to keep things snappy and conserve data — no more waiting for repeated lookups!
- **Clean, Responsive UI:** Beautiful interface built with React and Material-UI components, optimized for desktops and mobiles.

---

## 🎯 Why This Project?

As an aviation enthusiast and aspiring developer, I wanted to combine my love for planes with modern web tech — building an app that’s both fun and functional. Plus, it’s a great showcase of:

- **React Hooks & State Management** for interactive UIs.
- **Material-UI (MUI)** for sleek, accessible design.
- **Simple yet effective backend caching** in Flask.
- **Real-world REST API integration** pulling live data from ADS-B feeds.
- **Thoughtful UX with search history and image galleries.**

---

## 🛠️ Getting Started

### Prerequisites

- Python 3.x
- Node.js & npm
- Your favorite IDE or text editor

### Backend Setup

1. Clone the repo and navigate to the backend folder.

2. Install dependencies:

```

pip install -r requirements.txt

```

3. Run the Flask server:

```

python main.py

```

### Frontend Setup

1. Navigate to the frontend folder (```\aircraft-app-frontend\```).

2. Install dependencies:

```

npm install

```

3. Start the React app:

```

npm start

```

4. Visit http://localhost:3000 to explore!

---

## 🔮 Future Plans

- **Flight Status Tracking:** Up-to-the-minute updates on specific flights, delays, and gate info.
- **Map Visualization:** Fancy flight paths displayed interactively on an embeddable map.
- **Weather:** See weather in different airports and decode METAR

---

## 🙏 Credits & Thanks

- This project taps into the incredible **[ADSBdb API](https://www.adsbdb.com)**  and **[Airport-Data API](https://airport-data.com/)** — free and open aircraft data for the aviation lover in all of us.
- Built with ❤️ using **React**, **Material-UI**, and **Flask**.
- Inspired by endless plane-spotting sessions and late-night coding marathons.

---

Ready to dive in? Happy flying & coding! ✈️🚀
