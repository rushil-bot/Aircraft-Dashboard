FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for any compiled Python packages if necessary
RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose the API port
EXPOSE 8003

# Run the FastAPI server
CMD ["uvicorn", "serve:app", "--host", "0.0.0.0", "--port", "8003"]
