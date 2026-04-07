# Aircraft Dashboard

Aircraft Dashboard is a full-stack aviation intelligence platform built for travelers, aviation enthusiasts, and anyone who wants to make smarter decisions about flying. Whether you need to look up a specific aircraft, understand delay patterns on a route, or learn about aviation from a conversational AI assistant, Aircraft Dashboard brings all of that into a single, unified interface.

Flight delays cost travelers millions of hours each year. Most passengers have no visibility into which routes, airlines, or departure times carry the highest risk of delay before they book. Aircraft Dashboard addresses that gap directly, combining live aviation data with machine learning models trained on nearly 7 million real flight records to surface insights that are typically only available to airline operations teams.

---

## What You Can Do

**Look Up Any Aircraft or Airport**

Enter a tail number (registration) or flight callsign and instantly retrieve aircraft details, operator information, and recent flight activity sourced live from the ADSBdb feed. Airport lookups by ICAO or IATA code provide airport-level data from the airport-data.com API. All responses are cached for 10 minutes so repeated lookups remain fast.

**Predict Whether Your Flight Will Be Delayed**

The delay predictor is powered by an XGBoost classifier trained on 6,955,229 domestic flight records from the Bureau of Transportation Statistics (BTS) Reporting Carrier On-Time Performance dataset, covering carriers, routes, and schedules across the United States. Provide the airline, origin, destination, departure hour, and date context, and the model returns the probability that the flight will experience a departure delay of 15 minutes or more, the FAA standard threshold for a reportable delay. The model achieves 79% accuracy with a ROC-AUC of 0.68.

**Find the Best Time and Airline to Fly a Route**

The route recommender goes a step further. Instead of predicting a single flight, it evaluates every airline and departure-hour combination available on a given origin-destination pair and ranks them by predicted delay probability. This gives travelers a clear, data-backed view of which options carry the least delay risk on any given day of the week and month. The underlying LightGBM model is trained on the same 6,955,229 flight records, achieving a ROC-AUC of 0.69, and covers thousands of unique domestic routes indexed at training time.

**Ask Aviation Questions in Plain Language**

The natural language aviation assistant is a Retrieval-Augmented Generation (RAG) pipeline that lets users ask free-form questions about aviation topics and receive grounded, sourced answers streamed back in real time. The assistant queries a ChromaDB vector store populated with official FAA and aviation reference documents, retrieves the most relevant context, and passes it to a locally hosted Ollama large language model. Responses are strictly grounded in the ingested knowledge base, making it a reliable tool for learning about aircraft systems, regulations, procedures, and terminology.

**Search History**

The interface retains the five most recent lookups so users can return to prior searches without re-entering queries.

---

## Architecture

```
aircraft-app-frontend/     React SPA built with Material-UI
gateway/                   FastAPI API gateway (port 8000)
  routers/                 Endpoint handlers: health, lookups, agents
  services/                Business logic: aviation data, agent proxying
  utils/                   Redis-backed cache with in-memory fallback, shared HTTP client
agents/
  delay-predictor/         XGBoost delay classifier, trained on 6.9M flights (port 8001)
  route-recommender/       LightGBM route ranker, trained on 6.9M flights (port 8004)
  nl-query/                RAG agent using ChromaDB + Ollama (port 8003)
data/                      BTS flight dataset downloader and preprocessor
```

**Request Flow**

1. The React frontend sends requests to `/api/*` endpoints, proxied to the gateway during local development.
2. The gateway handles aircraft and airport lookups directly via the ADSBdb and airport-data.com APIs, caching results in Redis with automatic in-memory fallback if Redis is unavailable.
3. For AI features, the gateway proxies requests to the appropriate internal microservice. Agent hosts are resolved by environment variable or Docker service name.

**Training Data**

Both the delay predictor and route recommender are trained on the BTS "Reporting Carrier On-Time Performance (1987-present)" dataset, sourced directly from the U.S. Department of Transportation at transtats.bts.gov. The preprocessed dataset contains 6,955,229 completed (non-cancelled) domestic flights with engineered features including departure hour, day-of-week, weekend flag, carrier, origin, destination, and distance.

**External Data Sources**

- ADSBdb API (`api.adsbdb.com/v0/`) for live aircraft and callsign data
- airport-data.com API for airport information

---

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React, React Router, Material-UI |
| Gateway | FastAPI, httpx, Redis |
| Delay Predictor | XGBoost, scikit-learn, pandas |
| Route Recommender | LightGBM, scikit-learn, pandas |
| NL Query Agent | LangChain, ChromaDB, Ollama, HuggingFace Embeddings |
| Containerization | Docker, Docker Compose |
| Persistent Storage | PostgreSQL, Redis |

---

## Getting Started

### Prerequisites

- Python 3.10 or later
- Node.js and npm
- Docker and Docker Compose (for full-stack deployment)

### Running with Docker

The recommended way to run the full application is via Docker Compose. Copy `.env.example` to `.env` and populate the required environment variables before starting.

```bash
docker-compose up --build
```

The frontend will be available at `http://localhost:3000` and the gateway at `http://localhost:8000`.

```bash
docker-compose down                  # stop all services
docker-compose logs -f gateway       # stream logs for a specific service
```

### Running Locally (Development)

**Gateway**

```bash
cd gateway
pip install -r requirements.txt
python -m uvicorn gateway.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend**

```bash
cd aircraft-app-frontend
npm install
npm start
```

The React development server proxies all `/api` requests to `http://localhost:8000` automatically via `src/setupProxy.js`.

**AI Agent Microservices**

Each agent is a self-contained FastAPI application. ML models must be trained before the service can handle prediction requests. Flight data is downloaded from the BTS and preprocessed before training.

```bash
# Download and preprocess BTS flight data (required before training)
cd data
python download_bts.py --year 2024    # download a full year
# or
python download_bts.py --months 6    # download the latest 6 months

# Delay Predictor (port 8001)
cd agents/delay-predictor
python train.py
python serve.py

# Route Recommender (port 8004)
cd agents/route-recommender
python train.py
python serve.py

# NL Query Agent (port 8003) — requires a running ChromaDB and Ollama instance
cd agents/nl-query
python ingest.py    # populate the ChromaDB vector store
python serve.py
```

### Environment Variables

| Variable | Description | Default |
|---|---|---|
| `REDIS_HOST` | Redis hostname | `localhost` |
| `REDIS_PORT` | Redis port | `6379` |
| `POSTGRES_USER` | PostgreSQL username | (required) |
| `POSTGRES_PASSWORD` | PostgreSQL password | (required) |
| `POSTGRES_DB` | PostgreSQL database name | (required) |
| `DELAY_PREDICTOR_HOST` | Delay predictor service host | `delay-predictor` |
| `NL_QUERY_HOST` | NL query service host | `nl-query` |
| `ROUTE_RECOMMENDER_HOST` | Route recommender service host | `route-recommender` |
| `CHROMA_HOST` | ChromaDB host | `localhost` |
| `OLLAMA_HOST` | Ollama host | `localhost` |

---

## Service Ports

| Service | Port |
|---|---|
| Frontend | 3000 |
| Gateway | 8000 |
| Delay Predictor | 8001 |
| NL Query Agent | 8003 |
| Route Recommender | 8004 |
| ChromaDB | 8005 (host) |
| Ollama | 11434 |

---

## Credits

Aircraft and flight data provided by the [ADSBdb API](https://www.adsbdb.com) and the [airport-data.com API](https://airport-data.com/). Training data sourced from the U.S. Bureau of Transportation Statistics [On-Time Performance dataset](https://www.transtats.bts.gov/).
