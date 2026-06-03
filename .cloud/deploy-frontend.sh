#!/bin/bash
# Deploy Frontend to Google Cloud Storage + CDN
# Static Next.js build served with Cloud CDN

set -e

PROJECT_ID=${1:-$(gcloud config get-value project)}
BUCKET_NAME="research-ide-static-$PROJECT_ID"
REGION="asia-south1"

if [ -z "$PROJECT_ID" ]; then
    echo "❌ No GCP project ID found"
    echo "Usage: ./deploy-frontend.sh [PROJECT_ID]"
    exit 1
fi

echo "🚀 Deploying ResearchIDE Frontend"
echo "Project: $PROJECT_ID"
echo "Bucket: $BUCKET_NAME"
echo ""

# Build Next.js app
echo "📦 Building Next.js app..."
cd frontend
npm install --legacy-peer-deps
npm run build

if [ ! -d "out" ]; then
    echo "⚠️  Note: Using .next output (not static export)"
    echo "For Cloud Storage, you need static export enabled in next.config.js"
    echo "Add: output: 'export' to next.config.js"
fi

# Create bucket if it doesn't exist
echo "Creating Cloud Storage bucket..."
gsutil mb -l $REGION gs://$BUCKET_NAME 2>/dev/null || echo "Bucket already exists"

# Configure CORS for frontend
echo "Configuring CORS..."
cat > /tmp/cors.json << 'EOF'
[
  {
    "origin": ["*"],
    "method": ["GET", "HEAD", "OPTIONS"],
    "responseHeader": ["Content-Type", "Cache-Control"],
    "maxAgeSeconds": 3600
  }
]
EOF
gsutil cors set /tmp/cors.json gs://$BUCKET_NAME

# Upload files
echo "Uploading files to Cloud Storage..."
# HTML files - no cache
gsutil -m cp -r out/*.html gs://$BUCKET_NAME/ \
    -h "Cache-Control: public, max-age=3600" || true

# Assets - long cache (content-addressed filenames)
gsutil -m cp -r out/_next/* gs://$BUCKET_NAME/_next/ \
    -h "Cache-Control: public, max-age=31536000" || true

# Static files - moderate cache
gsutil -m cp -r out/public/* gs://$BUCKET_NAME/ \
    -h "Cache-Control: public, max-age=86400" 2>/dev/null || true

# Set index and error pages
gsutil web set -m index.html -e 404.html gs://$BUCKET_NAME

# Make files publicly readable
gsutil -m acl ch -u AllUsers:R gs://$BUCKET_NAME/**

# Get bucket URL
BUCKET_URL=$(gsutil -m web get gs://$BUCKET_NAME | grep 'Public URL' | awk '{print $NF}')

echo ""
echo "✅ Frontend deployment complete!"
echo "Static files URL: https://$BUCKET_NAME.storage.googleapis.com"
echo "Website: https://c.storage.googleapis.com/$BUCKET_NAME"
echo ""
echo "Next step: Set up Cloud CDN with this bucket as origin"
echo "or use a custom domain with Cloud Load Balancer"
