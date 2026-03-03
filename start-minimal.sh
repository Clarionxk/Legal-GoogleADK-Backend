#!/bin/bash
# =============================================================================
# LegalLease Live Agent — Minimal Dev Startup
# =============================================================================

set -e

echo "🏛️  Starting LegalLease Live Agent..."
echo ""

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ No venv found. Run: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check for .env
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Copying .env.example → .env"
    cp .env.example .env
    echo "📝 Please edit .env and set your GOOGLE_API_KEY"
    exit 1
fi

# Check for GOOGLE_API_KEY
if ! grep -q "GOOGLE_API_KEY=" .env || grep -q "GOOGLE_API_KEY=your-google-api-key" .env; then
    echo "❌ GOOGLE_API_KEY is not set in .env"
    echo "   Get one from: https://aistudio.google.com/apikey"
    exit 1
fi

echo "✅ Environment configured"
echo "🚀 Starting FastAPI server on http://localhost:8000"
echo "📡 WebSocket endpoint: ws://localhost:8000/ws/live-agent/{session_id}"
echo "📖 API docs: http://localhost:8000/docs"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --loop asyncio
