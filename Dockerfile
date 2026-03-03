# ─────────────────────────────────────────────────────────────────────────────
# LegalLease Live Agent — Cloud Run Dockerfile
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Install system deps (none needed for our slim stack)
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Cloud Run sets PORT env var
ENV PORT=8080
ENV ENVIRONMENT=production
ENV DEBUG=false

# Use standard asyncio loop (uvloop conflicts with Gemini Live API websockets)
CMD ["python", "-m", "uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8080", \
     "--loop", "asyncio", \
     "--workers", "1"]
