#!/bin/bash
# ResearchIDE - Step-by-Step Manual Setup for GCP
# Run this if you prefer step-by-step over automated setup

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  ResearchIDE - Manual GCP Setup (Step by Step)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

# Helper function
pause_step() {
    echo -e "${YELLOW}$1${NC}"
    read -p "Press Enter to continue..."
}

# STEP 1
echo -e "\n${YELLOW}[STEP 1/6] Install & Authenticate with Google Cloud${NC}"
echo "You need to:"
echo "  1. Install Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
echo "  2. Run: gcloud auth login"
echo "  3. Run: gcloud auth application-default login"
echo ""

pause_step "✓ Done with authentication? Press Enter to continue..."

# STEP 2
echo -e "\n${YELLOW}[STEP 2/6] Create New GCP Project${NC}"
echo "Go to: https://console.cloud.google.com/projectcreate"
echo ""
echo "Instructions:"
echo "  1. Project Name: research-ide"
echo "  2. Billing Account: (Your existing account)"
echo "  3. Click CREATE"
echo ""
echo "Then set it as default:"

read -p "Enter your new Project ID: " PROJECT_ID
gcloud config set project $PROJECT_ID
echo -e "${GREEN}✓ Project set to: $PROJECT_ID${NC}"

# STEP 3
echo -e "\n${YELLOW}[STEP 3/6] Enable Required APIs${NC}"
echo "Enabling APIs (this takes 1-2 minutes)..."

APIs=(
    "run.googleapis.com"
    "firestore.googleapis.com"
    "storage-api.googleapis.com"
    "cloudbuild.googleapis.com"
    "artifactregistry.googleapis.com"
    "secretmanager.googleapis.com"
)

for api in "${APIs[@]}"; do
    echo "  • Enabling $api..."
    gcloud services enable $api --project=$PROJECT_ID
done

echo -e "${GREEN}✓ All APIs enabled${NC}"

# STEP 4
echo -e "\n${YELLOW}[STEP 4/6] Create Cloud Firestore${NC}"
echo "Creating Firestore database..."

gcloud firestore databases create \
    --database=default \
    --region=asia-south1 \
    --type=firestore-native \
    --project=$PROJECT_ID

echo -e "${GREEN}✓ Firestore created${NC}"

# STEP 5
echo -e "\n${YELLOW}[STEP 5/6] Create Cloud Storage Buckets${NC}"
echo "Creating storage buckets..."

BUCKET_PDF="research-ide-pdf-$PROJECT_ID"
BUCKET_STATIC="research-ide-static-$PROJECT_ID"

gsutil mb -l asia-south1 gs://$BUCKET_PDF 2>/dev/null || echo "  PDF bucket exists"
gsutil mb -l asia-south1 gs://$BUCKET_STATIC 2>/dev/null || echo "  Static bucket exists"

echo -e "${GREEN}✓ Buckets created:${NC}"
echo "  • gs://$BUCKET_PDF"
echo "  • gs://$BUCKET_STATIC"

# STEP 6
echo -e "\n${YELLOW}[STEP 6/6] Create Secrets${NC}"
echo "Creating secrets in Secret Manager..."

# Generate keys
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
ENCRYPTION_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

echo -n "$SECRET_KEY" | gcloud secrets create secret-key --data-file=- --project=$PROJECT_ID 2>/dev/null || echo "  Secret key exists"
echo -n "$ENCRYPTION_KEY" | gcloud secrets create encryption-key --data-file=- --project=$PROJECT_ID 2>/dev/null || echo "  Encryption key exists"

echo -e "${GREEN}✓ Secrets created${NC}"

# Summary
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ MANUAL SETUP COMPLETE!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

echo -e "\n${YELLOW}Your Project Info:${NC}"
echo "  Project ID: $PROJECT_ID"
echo "  Region: asia-south1"
echo "  PDF Bucket: $BUCKET_PDF"
echo "  Static Bucket: $BUCKET_STATIC"

echo -e "\n${YELLOW}Next Steps:${NC}"
echo "1. Update .cloud/.env.cloud:"
echo "   GCP_PROJECT_ID=$PROJECT_ID"
echo ""
echo "2. Run database migration:"
echo "   python .cloud/migrate_to_firestore.py --project $PROJECT_ID"
echo ""
echo "3. Deploy backend:"
echo "   .cloud/deploy-backend.sh $PROJECT_ID"
echo ""
echo "4. Deploy frontend:"
echo "   .cloud/deploy-frontend.sh $PROJECT_ID"
