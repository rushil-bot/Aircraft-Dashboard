# ---- Gateway Dockerfile ----
# FastAPI API Gateway for the Aircraft Dashboard
FROM python:3.12-slim

# Prevent Python from writing .pyc and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code into the /app/gateway module 
COPY . /app/gateway/

EXPOSE 8000

# Health check for Docker / Kubernetes
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

# Run with uvicorn targeting the gateway module
CMD ["uvicorn", "gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]
