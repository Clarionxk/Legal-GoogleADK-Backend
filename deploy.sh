#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# LegalLease — Deploy Backend to Google Cloud Run
# ─────────────────────────────────────────────────────────────────────────────
set -e

# ─── Configuration ─────────────────────────────────────────────────────────
PROJECT_ID="${GCP_PROJECT_ID:-legallease-live}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="legallease-backend"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         LegalLease — Cloud Run Deployment                  ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  Project:  ${PROJECT_ID}"
echo "║  Region:   ${REGION}"
echo "║  Service:  ${SERVICE_NAME}"
echo "║  Image:    ${IMAGE_NAME}"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ─── Step 1: Verify gcloud is authenticated ────────────────────────────────
echo "🔐 Step 1: Checking gcloud authentication..."
gcloud auth print-identity-token > /dev/null 2>&1 || {
    echo "❌ Not authenticated. Run: gcloud auth login"
    exit 1
}
echo "   ✅ Authenticated"

# ─── Step 2: Set project ───────────────────────────────────────────────────
echo "📋 Step 2: Setting project to ${PROJECT_ID}..."
gcloud config set project "${PROJECT_ID}" 2>/dev/null
echo "   ✅ Project set"

# ─── Step 3: Enable required APIs ──────────────────────────────────────────
echo "🔧 Step 3: Enabling required APIs..."
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    containerregistry.googleapis.com \
    artifactregistry.googleapis.com \
    2>/dev/null
echo "   ✅ APIs enabled"

# ─── Step 4: Build container image ─────────────────────────────────────────
echo "🏗️  Step 4: Building container image with Cloud Build..."
gcloud builds submit --tag "${IMAGE_NAME}" .
echo "   ✅ Image built and pushed"

# ─── Step 5: Deploy to Cloud Run ───────────────────────────────────────────
echo "🚀 Step 5: Deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
    --image "${IMAGE_NAME}" \
    --platform managed \
    --region "${REGION}" \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300 \
    --concurrency 80 \
    --min-instances 0 \
    --max-instances 3 \
    --set-env-vars "ENVIRONMENT=production,DEBUG=false" \
    --session-affinity
echo "   ✅ Deployed!"

# ─── Step 6: Get the service URL ───────────────────────────────────────────
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
    --region "${REGION}" \
    --format "value(status.url)")

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ✅ DEPLOYMENT COMPLETE                                    ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  Backend URL: ${SERVICE_URL}"
echo "║  Health:      ${SERVICE_URL}/health"
echo "║  API Docs:    ${SERVICE_URL}/docs"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  Next: Update your frontend .env with:                     ║"
echo "║  NEXT_PUBLIC_BACKEND_URL=${SERVICE_URL}                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
