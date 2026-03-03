#!/bin/bash
# =============================================================================
# LegalLease Live Agent — Deploy to Google Cloud Run
# =============================================================================
# Prerequisites:
#   1. Install gcloud CLI: https://cloud.google.com/sdk/docs/install
#   2. Authenticate: gcloud auth login
#   3. Set your project: gcloud config set project YOUR_PROJECT_ID
#   4. Enable APIs: gcloud services enable run.googleapis.com cloudbuild.googleapis.com
# =============================================================================

set -e

# ─── Configuration ───────────────────────────────────────────────────────────
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="legallease-live-agent"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🏛️  Deploying LegalLease Live Agent to Cloud Run"
echo "   Project:  ${PROJECT_ID}"
echo "   Region:   ${REGION}"
echo "   Service:  ${SERVICE_NAME}"
echo ""

# ─── Check for required env vars ─────────────────────────────────────────────
if [ -z "$GOOGLE_API_KEY" ]; then
    if [ -f .env ]; then
        export $(grep GOOGLE_API_KEY .env | xargs)
    fi
fi

if [ -z "$GOOGLE_API_KEY" ]; then
    echo "❌ GOOGLE_API_KEY is not set. Set it in .env or export it."
    exit 1
fi

echo "✅ GOOGLE_API_KEY found"

# ─── Build & Deploy ──────────────────────────────────────────────────────────
echo ""
echo "🔨 Building and deploying to Cloud Run..."
echo ""

gcloud run deploy "${SERVICE_NAME}" \
    --source . \
    --region "${REGION}" \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars "GOOGLE_API_KEY=${GOOGLE_API_KEY}" \
    --set-env-vars "ENVIRONMENT=production" \
    --set-env-vars "DEBUG=false" \
    --set-env-vars "CORS_ORIGINS=*" \
    --set-env-vars "GEMINI_MODEL=gemini-2.5-flash-native-audio-preview-12-2025" \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300 \
    --session-affinity \
    --min-instances 0 \
    --max-instances 3 \
    --port 8080

echo ""
echo "✅ Deployed successfully!"
echo ""

# Get the service URL
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" --region="${REGION}" --format='value(status.url)')
echo "🌐 Service URL: ${SERVICE_URL}"
echo "📡 WebSocket:   ${SERVICE_URL/https/wss}/ws/live-agent/{session_id}"
echo "📖 API Docs:    ${SERVICE_URL}/docs"
echo ""
echo "👉 Update your frontend to use this URL as the backend:"
echo "   NEXT_PUBLIC_BACKEND_URL=${SERVICE_URL/https/wss}"
