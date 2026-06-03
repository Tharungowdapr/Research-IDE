# ☁️ ResearchIDE - Google Cloud Deployment Guide

Complete step-by-step guide to deploy ResearchIDE to Google Cloud with **$0-10/month** cost.

**Generated**: June 2026  
**Target**: Cost-optimized deployment on GCP (India region - Mumbai)  
**Estimated Time**: 1-2 hours

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (5 minutes)](#quick-start)
3. [Detailed Setup](#detailed-setup)
4. [Code Changes Required](#code-changes-required)
5. [Deployment](#deployment)
6. [Testing & Validation](#testing--validation)
7. [Monitoring & Cost Management](#monitoring--cost-management)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools
- [x] Google Cloud SDK (`gcloud` CLI)
- [x] Docker
- [x] Python 3.11+
- [x] Node.js 18+
- [x] Git
- [ ] GCP Account (free tier eligible)

### GCP Account Setup

If you don't have a GCP account:
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable billing (you get $300 free trial)
4. All services mentioned here are within the free tier

### Local Setup
```bash
# Install Google Cloud SDK
# macOS:
brew install --cask google-cloud-sdk

# OR download from: https://cloud.google.com/sdk/docs/install

# Authenticate with GCP
gcloud auth login
gcloud config set project YOUR-PROJECT-ID
```

---

## Quick Start

### Option 1: Automated Setup (RECOMMENDED)

```bash
# From project root
cd .cloud

# 1. Make scripts executable
chmod +x deploy-setup.sh deploy-backend.sh deploy-frontend.sh

# 2. Run setup
./deploy-setup.sh
# Prompts for: GCP Project ID, API keys, configuration

# 3. Configure environment
cp .env.cloud.template .env.cloud
# Edit .env.cloud with your API keys

# 4. Deploy backend
./deploy-backend.sh

# 5. Deploy frontend
./deploy-frontend.sh
```

### Option 2: Manual Setup (Step-by-step)

See [Detailed Setup](#detailed-setup) section below.

---

## Detailed Setup

### Step 1: Create GCP Project

```bash
# Create new project
gcloud projects create research-ide-prod \
    --name="ResearchIDE Production"

# Set as default
gcloud config set project research-ide-prod

# Enable required APIs
gcloud services enable \
    run.googleapis.com \
    firestore.googleapis.com \
    storage-api.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    secretmanager.googleapis.com \
    cloudkms.googleapis.com
```

### Step 2: Set Up Cloud Firestore

```bash
# Create Firestore database (India region)
gcloud firestore databases create \
    --database=default \
    --region=asia-south1 \
    --type=firestore-native

# Create a test collection to verify
gcloud firestore collections list
```

### Step 3: Create Cloud Storage Buckets

```bash
PROJECT_ID=$(gcloud config get-value project)

# PDF cache bucket
gsutil mb -l asia-south1 gs://research-ide-pdf-cache-$PROJECT_ID

# Static frontend bucket
gsutil mb -l asia-south1 gs://research-ide-static-$PROJECT_ID

# Backups bucket
gsutil mb -l asia-south1 gs://research-ide-backups-$PROJECT_ID

# List buckets
gsutil ls
```

### Step 4: Create Service Account

```bash
PROJECT_ID=$(gcloud config get-value project)

# Create service account
gcloud iam service-accounts create research-ide-backend \
    --display-name="ResearchIDE Backend Service"

# Grant roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:research-ide-backend@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/datastore.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:research-ide-backend@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:research-ide-backend@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### Step 5: Store Secrets in Secret Manager

```bash
# Generate new secret keys
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
ENCRYPTION_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Create secrets
echo -n "$SECRET_KEY" | gcloud secrets create secret-key --data-file=-
echo -n "$ENCRYPTION_KEY" | gcloud secrets create encryption-key --data-file=-
echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets create gemini-api-key --data-file=-

# List secrets
gcloud secrets list
```

---

## Code Changes Required

### 1. Switch from SQLite to Cloud Firestore

**Current** (`backend/core/database.py`):
```python
from sqlalchemy import create_engine
DATABASE_URL = "sqlite:////app/data/research_ide.db"
engine = create_engine(DATABASE_URL)
```

**After** (using `firebase-admin`):
```python
import firebase_admin
from firebase_admin import firestore

# Initialize in startup
firebase_admin.initialize_app()
db = firestore.client()

# Use Firestore instead of SQLAlchemy
# Update all database queries to use Firestore API
```

### 2. Update Requirements

Add to `backend/requirements.txt`:
```
firebase-admin==7.0.0
```

### 3. Update Configuration

Update `backend/core/config.py`:
```python
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # GCP Configuration
    GCP_PROJECT_ID: str = os.getenv("GCP_PROJECT_ID")
    
    # Database
    DATABASE_TYPE: str = "firestore"  # or "postgresql"
    
    # Secrets from Secret Manager
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY")
    
    # LLM
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")
    
    # Cloud Storage
    GCS_BUCKET_PDF: str = os.getenv("GCS_BUCKET_PDF")
    
    class Config:
        env_file = ".env"
```

### 4. Add Cloud Run Environment

Create `.cloud/.env.cloud` from template:
```bash
cd .cloud
cp .env.cloud.template .env.cloud
# Edit with your values
```

---

## Deployment

### Backend Deployment

```bash
cd .cloud

# Option 1: Using deploy script
./deploy-backend.sh

# Option 2: Manual deployment
gcloud run deploy research-ide-backend \
    --source ../backend \
    --platform managed \
    --region asia-south1 \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --timeout 3600 \
    --max-instances 2 \
    --set-secrets SECRET_KEY=secret-key:latest,\
        ENCRYPTION_KEY=encryption-key:latest,\
        GEMINI_API_KEY=gemini-api-key:latest
```

### Frontend Deployment

```bash
cd frontend

# Build static export
npm install --legacy-peer-deps
npm run build

# Deploy to Cloud Storage
cd ..
cd .cloud
./deploy-frontend.sh
```

### Get Deployed URLs

```bash
# Backend URL
gcloud run services describe research-ide-backend \
    --region asia-south1 \
    --format='value(status.url)'

# Frontend URL (from Cloud Storage)
gsutil web get gs://research-ide-static-$(gcloud config get-value project)
```

---

## Testing & Validation

### 1. Test Backend Health

```bash
BACKEND_URL=$(gcloud run services describe research-ide-backend \
    --region asia-south1 \
    --format='value(status.url)')

curl $BACKEND_URL/api/health
# Should return: {"status": "ok"}
```

### 2. Test Firestore Connection

```bash
curl -X POST $BACKEND_URL/api/test-firestore
# Should return successful connection test
```

### 3. Test Frontend Loading

```bash
FRONTEND_BUCKET=$(gcloud config get-value project)
curl https://storage.googleapis.com/research-ide-static-$FRONTEND_BUCKET/index.html
# Should return HTML
```

### 4. View Logs

```bash
# Backend logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=research-ide-backend" \
    --limit=50 \
    --format=json

# Filter for errors
gcloud logging read "resource.type=cloud_run_revision AND severity=ERROR" \
    --limit=20
```

---

## Monitoring & Cost Management

### 1. Monitor Costs

```bash
cd .cloud
chmod +x monitor-costs.sh
./monitor-costs.sh
```

### 2. Create Budget Alert

```bash
gcloud billing budgets create \
    --billing-account=$(gcloud billing accounts list --format="value(name)" | head -1) \
    --display-name="ResearchIDE Monthly Budget" \
    --budget-amount=10 \
    --threshold-rule=percent=50 \
    --threshold-rule=percent=90 \
    --threshold-rule=percent=100
```

### 3. Enable Monitoring

```bash
# Cloud Monitoring dashboard
gcloud monitoring dashboards create --config-from-file=- << 'EOF'
{
  "displayName": "ResearchIDE Dashboard",
  "mosaicLayout": {
    "columns": 12,
    "tiles": [
      {
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Cloud Run Requests",
          "xyChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"run.googleapis.com/request_count\" resource.type=\"cloud_run_revision\""
                }
              }
            }]
          }
        }
      }
    ]
  }
}
EOF
```

---

## Cost Breakdown (Monthly)

| Service | Tier | Cost |
|---------|------|------|
| **Cloud Run** | 2M requests free | **$0** |
| **Firestore** | 1GB free, 50K reads/day | **$0** |
| **Cloud Storage** | 5GB free | **$0** |
| **Cloud Logging** | 50GB free | **$0** |
| **Cloud CDN** | 1GiB/month free | **$0** |
| **Gemini API** | Token-based | **$1-5** |
| **Secret Manager** | $0.006/secret/month | **~$0.02** |
| | | |
| **TOTAL** | | **$1-5/month** |

---

## Troubleshooting

### Issue: "Permission denied" when deploying

**Solution**: Ensure service account has correct roles
```bash
gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
    --member="serviceAccount:research-ide-backend@$(gcloud config get-value project).iam.gserviceaccount.com" \
    --role="roles/run.invoker"
```

### Issue: Firestore connection timeout

**Solution**: Check firestore database is created
```bash
gcloud firestore databases list
# Should show status: ACTIVE
```

### Issue: Cloud Run service not scaling

**Solution**: Check Cloud Run quota
```bash
gcloud compute project-info describe --project=$(gcloud config get-value project) \
    --format="value(quotas[name~'run.*'].limit)"
```

### Issue: High costs

**Solution**: Check free tier usage
```bash
cd .cloud
./monitor-costs.sh
```

---

## Next Steps After Deployment

1. ✅ Set up custom domain with Cloud Load Balancer
2. ✅ Enable Cloud Armor for DDoS protection
3. ✅ Configure Cloud CDN for better performance
4. ✅ Set up automated backups
5. ✅ Enable Cloud Trace for performance monitoring
6. ✅ Create Cloud Scheduler jobs for recurring tasks

---

## Support & Resources

- [GCP Free Tier Documentation](https://cloud.google.com/free)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Firestore Documentation](https://cloud.google.com/firestore/docs)
- [GCP Console](https://console.cloud.google.com)

---

**Questions?** Check the [DEPLOYMENT_ANALYSIS.md](./DEPLOYMENT_ANALYSIS.md) for architecture details.
