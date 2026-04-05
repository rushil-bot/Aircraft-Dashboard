FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and models
COPY . .

# Expose the API port
EXPOSE 8001

# Run the FastAPI server
CMD ["uvicorn", "serve:app", "--host", "0.0.0.0", "--port", "8001"]
