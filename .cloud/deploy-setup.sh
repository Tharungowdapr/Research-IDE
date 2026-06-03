#!/bin/bash
# GCP Deployment Setup Script
# Usage: chmod +x deploy-setup.sh && ./deploy-setup.sh

set -e  # Exit on error

echo "🚀 ResearchIDE - Google Cloud Deployment Setup"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
check_prerequisites() {
    echo -e "\n${YELLOW}Checking prerequisites...${NC}"
    
    if ! command -v gcloud &> /dev/null; then
        echo -e "${RED}❌ gcloud CLI not found. Install: https://cloud.google.com/sdk/docs/install${NC}"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker not found. Install: https://docs.docker.com/install${NC}"
        exit 1
    fi
    
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 not found${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ All prerequisites found${NC}"
}

# Setup GCP Project
setup_gcp_project() {
    echo -e "\n${YELLOW}Setting up GCP Project...${NC}"
    
    read -p "Enter GCP Project ID (e.g., research-ide-prod): " PROJECT_ID
    
    # Set default project
    gcloud config set project $PROJECT_ID
    
    # Enable required APIs
    echo "Enabling required APIs..."
    gcloud services enable \
        run.googleapis.com \
        firestore.googleapis.com \
        storage-api.googleapis.com \
        cloudbuild.googleapis.com \
        artifactregistry.googleapis.com \
        secretmanager.googleapis.com \
        cloudkms.googleapis.com
    
    echo -e "${GREEN}✓ GCP Project setup complete${NC}"
    echo "Project ID: $PROJECT_ID"
}

# Create Cloud Firestore database
setup_firestore() {
    echo -e "\n${YELLOW}Setting up Cloud Firestore...${NC}"
    
    gcloud firestore databases create \
        --database=default \
        --region=asia-south1 \
        --type=firestore-native \
        2>/dev/null || echo "Database might already exist"
    
    echo -e "${GREEN}✓ Firestore database ready${NC}"
}

# Create Cloud Storage buckets
setup_storage() {
    echo -e "\n${YELLOW}Setting up Cloud Storage...${NC}"
    
    BUCKET_PDF="research-ide-pdf-cache-${PROJECT_ID}"
    BUCKET_STATIC="research-ide-static-${PROJECT_ID}"
    BUCKET_BACKUPS="research-ide-backups-${PROJECT_ID}"
    
    # Create buckets
    gsutil mb -l asia-south1 gs://$BUCKET_PDF 2>/dev/null || echo "PDF bucket exists"
    gsutil mb -l asia-south1 gs://$BUCKET_STATIC 2>/dev/null || echo "Static bucket exists"
    gsutil mb -l asia-south1 gs://$BUCKET_BACKUPS 2>/dev/null || echo "Backups bucket exists"
    
    # Set lifecycle policies
    echo "Setting lifecycle policies..."
    cat > /tmp/pdf_lifecycle.json << EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 90}
      }
    ]
  }
}
EOF
    gsutil lifecycle set /tmp/pdf_lifecycle.json gs://$BUCKET_PDF
    
    echo -e "${GREEN}✓ Cloud Storage buckets created${NC}"
    echo "PDF Cache: gs://$BUCKET_PDF"
    echo "Static Content: gs://$BUCKET_STATIC"
    echo "Backups: gs://$BUCKET_BACKUPS"
}

# Create Cloud Run service account
setup_service_account() {
    echo -e "\n${YELLOW}Setting up Service Account...${NC}"
    
    SA_NAME="research-ide-backend"
    SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
    
    # Create service account
    gcloud iam service-accounts create $SA_NAME \
        --display-name="ResearchIDE Backend Service" \
        2>/dev/null || echo "Service account exists"
    
    # Grant necessary roles
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
    
    echo -e "${GREEN}✓ Service Account created and configured${NC}"
    echo "Service Account: $SA_EMAIL"
}

# Create secrets in Secret Manager
setup_secrets() {
    echo -e "\n${YELLOW}Setting up Cloud Secret Manager...${NC}"
    
    echo "Creating secrets from .env.cloud..."
    
    # Check if .env.cloud exists
    if [ ! -f ".cloud/.env.cloud" ]; then
        echo -e "${YELLOW}Note: Copy .env.cloud.template to .env.cloud and fill in your values${NC}"
        echo "Then re-run this script"
        return
    fi
    
    # Create secrets
    gcloud secrets create secret-key --data-file=/dev/stdin < <(grep SECRET_KEY= .cloud/.env.cloud | cut -d= -f2-) 2>/dev/null || echo "Secret exists"
    gcloud secrets create encryption-key --data-file=/dev/stdin < <(grep ENCRYPTION_KEY= .cloud/.env.cloud | cut -d= -f2-) 2>/dev/null || echo "Secret exists"
    gcloud secrets create gemini-api-key --data-file=/dev/stdin < <(grep GEMINI_API_KEY= .cloud/.env.cloud | cut -d= -f2-) 2>/dev/null || echo "Secret exists"
    
    echo -e "${GREEN}✓ Secrets created in Secret Manager${NC}"
}

# Build and test Docker images
build_docker_images() {
    echo -e "\n${YELLOW}Building Docker images...${NC}"
    
    docker-compose build
    
    echo -e "${GREEN}✓ Docker images built successfully${NC}"
}

# Main execution
main() {
    check_prerequisites
    setup_gcp_project
    setup_firestore
    setup_storage
    setup_service_account
    setup_secrets
    build_docker_images
    
    echo -e "\n${GREEN}✅ Deployment setup complete!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Copy .cloud/.env.cloud.template to .cloud/.env.cloud"
    echo "2. Fill in your API keys and configuration values"
    echo "3. Run: ./deploy-backend.sh (to deploy to Cloud Run)"
    echo "4. Run: ./deploy-frontend.sh (to deploy static assets)"
    echo ""
}

main "$@"
