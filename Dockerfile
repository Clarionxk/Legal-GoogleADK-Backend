# ─────────────────────────────────────────────────────────────────────────────
# LegalLease Live Agent — Cloud Run Dockerfile
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code + config files
COPY app/ ./app/
COPY legallease-live-firebase-adminsdk-fbsvc-4cb083dbd4.json ./firebase-sa.json

# Cloud Run sets PORT env var
ENV PORT=8080
ENV ENVIRONMENT=production
ENV DEBUG=false

EXPOSE ${PORT}

# Use standard asyncio loop (uvloop conflicts with Gemini Live API websockets)
# timeout-keep-alive=120 keeps WebSocket connections alive longer
CMD ["python", "-m", "uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8080", \
     "--loop", "asyncio", \
     "--workers", "1", \
     "--timeout-keep-alive", "120"]
