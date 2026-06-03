#!/bin/bash
# ResearchIDE - Complete GCP Setup from Scratch
# This script sets up everything you need for FREE tier deployment
# Usage: chmod +x gcp-complete-setup.sh && ./gcp-complete-setup.sh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
GOOGLE_EMAIL="tharun2005328@gmail.com"
PROJECT_NAME="research-ide"
REGION="asia-south1"

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║   ResearchIDE - Google Cloud Complete Setup from Scratch      ║"
echo "║   Email: $GOOGLE_EMAIL"
echo "║   Project: $PROJECT_NAME"
echo "║   Region: $REGION (India)"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Step 1: Check & Install gcloud
echo -e "\n${YELLOW}[STEP 1/10] Checking Google Cloud SDK...${NC}"
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}gcloud not found. Installing...${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install --cask google-cloud-sdk
    else
        echo "Please install from: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
fi
echo -e "${GREEN}✓ gcloud CLI found${NC}"

# Step 2: Authenticate
echo -e "\n${YELLOW}[STEP 2/10] Authenticating with Google Cloud...${NC}"
echo "A browser window will open. Sign in with: $GOOGLE_EMAIL"
gcloud auth login
gcloud auth application-default login

echo -e "${GREEN}✓ Authentication complete${NC}"

# Step 3: Create Project
echo -e "\n${YELLOW}[STEP 3/10] Creating GCP Project: $PROJECT_NAME${NC}"
PROJECT_ID="${PROJECT_NAME}-$(date +%s | tail -c 5)"
echo "Generated Project ID: $PROJECT_ID"

gcloud projects create $PROJECT_ID \
    --name="$PROJECT_NAME" \
    --set-as-default

echo -e "${GREEN}✓ Project created: $PROJECT_ID${NC}"
echo "⚠️  Save this Project ID: $PROJECT_ID"

# Step 4: Enable Billing
echo -e "\n${YELLOW}[STEP 4/10] Linking Billing Account...${NC}"
echo "You already have a billing account. Finding it..."

BILLING_ACCOUNT=$(gcloud billing accounts list --format="value(name)" | head -1)

if [ -z "$BILLING_ACCOUNT" ]; then
    echo -e "${RED}No billing account found. Please link one at:${NC}"
    echo "https://console.cloud.google.com/billing/linkedaccounts?project=$PROJECT_ID"
    exit 1
fi

gcloud billing projects link $PROJECT_ID \
    --billing-account=$BILLING_ACCOUNT

echo -e "${GREEN}✓ Billing linked: $BILLING_ACCOUNT${NC}"

# Step 5: Enable Required APIs
echo -e "\n${YELLOW}[STEP 5/10] Enabling Required APIs (this takes ~2 minutes)...${NC}"

APIS=(
    "run.googleapis.com"
    "firestore.googleapis.com"
    "storage-api.googleapis.com"
    "cloudbuild.googleapis.com"
    "artifactregistry.googleapis.com"
    "secretmanager.googleapis.com"
    "cloudkms.googleapis.com"
    "compute.googleapis.com"
)

for api in "${APIS[@]}"; do
    echo "  Enabling $api..."
    gcloud services enable $api --project=$PROJECT_ID
done

echo -e "${GREEN}✓ All APIs enabled${NC}"

# Step 6: Create Firestore Database
echo -e "\n${YELLOW}[STEP 6/10] Creating Cloud Firestore Database...${NC}"

gcloud firestore databases create \
    --database=default \
    --region=$REGION \
    --type=firestore-native \
    --project=$PROJECT_ID

echo -e "${GREEN}✓ Firestore database created${NC}"

# Step 7: Create Cloud Storage Buckets
echo -e "\n${YELLOW}[STEP 7/10] Creating Cloud Storage Buckets...${NC}"

BUCKET_PDF="research-ide-pdf-cache-$PROJECT_ID"
BUCKET_STATIC="research-ide-static-$PROJECT_ID"
BUCKET_BACKUPS="research-ide-backups-$PROJECT_ID"

for bucket in $BUCKET_PDF $BUCKET_STATIC $BUCKET_BACKUPS; do
    echo "  Creating bucket: gs://$bucket"
    gsutil mb -l $REGION gs://$bucket 2>/dev/null || echo "    (bucket already exists)"
done

echo -e "${GREEN}✓ Cloud Storage buckets created${NC}"

# Step 8: Create Service Account
echo -e "\n${YELLOW}[STEP 8/10] Creating Service Account...${NC}"

SA_NAME="research-ide-backend"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud iam service-accounts create $SA_NAME \
    --display-name="ResearchIDE Backend Service" \
    --project=$PROJECT_ID \
    2>/dev/null || echo "  Service account already exists"

# Grant necessary roles
echo "  Granting IAM roles..."

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/datastore.user" \
    --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/storage.objectAdmin" \
    --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/secretmanager.secretAccessor" \
    --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/run.invoker" \
    --quiet

echo -e "${GREEN}✓ Service Account created: $SA_EMAIL${NC}"

# Step 9: Create Secrets in Secret Manager
echo -e "\n${YELLOW}[STEP 9/10] Creating Secrets in Secret Manager...${NC}"

# Generate new secrets
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
ENCRYPTION_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

echo "Creating secrets..."
echo -n "$SECRET_KEY" | gcloud secrets create secret-key \
    --replication-policy="automatic" \
    --data-file=- \
    --project=$PROJECT_ID \
    2>/dev/null || echo "  Secret already exists"

echo -n "$ENCRYPTION_KEY" | gcloud secrets create encryption-key \
    --replication-policy="automatic" \
    --data-file=- \
    --project=$PROJECT_ID \
    2>/dev/null || echo "  Secret already exists"

echo -e "${GREEN}✓ Secrets created${NC}"

# Step 10: Setup Budget Alert
echo -e "\n${YELLOW}[STEP 10/10] Setting up Budget Alert for Free Tier...${NC}"

# Create budget to alert if spending exceeds $10/month
gcloud billing budgets create \
    --billing-account=$BILLING_ACCOUNT \
    --display-name="ResearchIDE Free Tier Alert" \
    --budget-amount=10 \
    --threshold-rule=percent=50 \
    --threshold-rule=percent=90 \
    --threshold-rule=percent=100 \
    2>/dev/null || echo "  Budget alert may already exist"

echo -e "${GREEN}✓ Budget alert created (will alert at 50%, 90%, 100% of \$10)${NC}"

# Summary
echo -e "\n${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}✅ GCP PROJECT SETUP COMPLETE!${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"

echo -e "\n${YELLOW}📋 IMPORTANT INFORMATION - SAVE THIS:${NC}"
echo -e "${GREEN}Project ID:${NC}        $PROJECT_ID"
echo -e "${GREEN}Email:${NC}             $GOOGLE_EMAIL"
echo -e "${GREEN}Region:${NC}            $REGION"
echo -e "${GREEN}Service Account:${NC}   $SA_EMAIL"
echo -e "${GREEN}PDF Bucket:${NC}        gs://$BUCKET_PDF"
echo -e "${GREEN}Static Bucket:${NC}     gs://$BUCKET_STATIC"
echo -e "${GREEN}Backups Bucket:${NC}    gs://$BUCKET_BACKUPS"

echo -e "\n${YELLOW}🔐 SECRETS CREATED:${NC}"
echo -e "${GREEN}SECRET_KEY:${NC}       Created ✓"
echo -e "${GREEN}ENCRYPTION_KEY:${NC}   Created ✓"

echo -e "\n${YELLOW}📁 UPDATE YOUR CONFIGURATION:${NC}"
echo "1. Update .cloud/.env.cloud with:"
echo "   GCP_PROJECT_ID=$PROJECT_ID"
echo "   GEMINI_API_KEY=your-actual-gemini-api-key"
echo ""
echo "2. Verify Firestore:"
echo "   gcloud firestore databases list --project=$PROJECT_ID"
echo ""
echo "3. Verify buckets:"
echo "   gsutil ls -p $PROJECT_ID"
echo ""

echo -e "\n${YELLOW}🚀 NEXT STEPS:${NC}"
echo "1. Update .cloud/.env.cloud with your GCP_PROJECT_ID and GEMINI_API_KEY"
echo "2. Run: python migrate_to_firestore.py --project $PROJECT_ID"
echo "3. Run: ./deploy-backend.sh $PROJECT_ID"
echo "4. Run: ./deploy-frontend.sh $PROJECT_ID"
echo ""

echo -e "\n${YELLOW}💰 COST TRACKING:${NC}"
echo "View costs: https://console.cloud.google.com/billing"
echo "Project: https://console.cloud.google.com/home/dashboard?project=$PROJECT_ID"
echo ""

# Save project info to file
cat > /tmp/research-ide-project-info.txt << EOF
ResearchIDE GCP Project Information
==================================
Created: $(date)
Project ID: $PROJECT_ID
Email: $GOOGLE_EMAIL
Region: $REGION
Service Account: $SA_EMAIL

Buckets:
- PDF Cache: gs://$BUCKET_PDF
- Static: gs://$BUCKET_STATIC
- Backups: gs://$BUCKET_BACKUPS

Secrets (created automatically):
- secret-key: ✓
- encryption-key: ✓
- gemini-api-key: (need to create manually)

Next: Update .cloud/.env.cloud and run deployment scripts
EOF

echo -e "\n${GREEN}Project info saved to: /tmp/research-ide-project-info.txt${NC}"
echo -e "${GREEN}cat /tmp/research-ide-project-info.txt${NC}"
