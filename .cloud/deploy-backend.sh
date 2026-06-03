#!/bin/bash
# Deploy Backend to Google Cloud Run
# This script builds and deploys the Python backend to Cloud Run

set -e

PROJECT_ID=${1:-$(gcloud config get-value project)}
SERVICE_NAME="research-ide-backend"
REGION="asia-south1"

if [ -z "$PROJECT_ID" ]; then
    echo "❌ No GCP project ID found"
    echo "Usage: ./deploy-backend.sh [PROJECT_ID]"
    exit 1
fi

echo "🚀 Deploying ResearchIDE Backend to Cloud Run"
echo "Project: $PROJECT_ID"
echo "Service: $SERVICE_NAME"
echo "Region: $REGION"
echo ""

# Check if Cloud Run API is enabled
echo "Checking Cloud Run API..."
gcloud services enable run.googleapis.com --project=$PROJECT_ID

# Build and push to Container Registry
echo "📦 Building Docker image..."
gcloud builds submit \
    --tag gcr.io/$PROJECT_ID/$SERVICE_NAME:latest \
    --project=$PROJECT_ID \
    --timeout=1200s \
    --substitutions _SERVICE_NAME=$SERVICE_NAME \
    -f backend/Dockerfile \
    backend/

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME:latest \
    --platform managed \
    --region $REGION \
    --project=$PROJECT_ID \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --timeout 3600 \
    --max-instances 2 \
    --concurrency 50 \
    --set-env-vars "^:^" \
    --set-secrets \
        SECRET_KEY=secret-key:latest,\
        ENCRYPTION_KEY=encryption-key:latest,\
        GEMINI_API_KEY=gemini-api-key:latest \
    --service-account=research-ide-backend@$PROJECT_ID.iam.gserviceaccount.com

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format='value(status.url)')

echo ""
echo "✅ Deployment complete!"
echo "Backend URL: $SERVICE_URL"
echo ""
echo "Test the deployment:"
echo "curl $SERVICE_URL/api/health"
