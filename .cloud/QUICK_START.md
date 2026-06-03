# 🚀 ResearchIDE - COMPLETE DEPLOYMENT GUIDE (From Scratch)

**Your Setup**: Google Account with Billing | Project: research-ide | Email: tharun2005328@gmail.com | Region: India (Mumbai)

---

## ⏱️ TOTAL TIME: ~1.5-2 hours

---

## PART 1: GCP ACCOUNT SETUP (15-30 minutes)

### Option A: AUTOMATED SETUP (Recommended - 5 minutes)

```bash
# 1. Go to project directory
cd /Users/tharungowdapr/Documents/college/projects/research-ide

# 2. Make setup script executable
chmod +x .cloud/gcp-complete-setup.sh

# 3. Run automated setup
.cloud/gcp-complete-setup.sh

# The script will:
# ✓ Authenticate you with gcloud
# ✓ Create a new GCP project (research-ide-XXXXX)
# ✓ Enable all required APIs
# ✓ Create Firestore database
# ✓ Create Cloud Storage buckets
# ✓ Create Service Account
# ✓ Create Secrets in Secret Manager
# ✓ Set up billing alerts
# ✓ Save your project info

# Save the Project ID it shows you - you'll need it!
```

### Option B: MANUAL SETUP (Step by Step)

If you prefer manual control:

```bash
chmod +x .cloud/manual-setup.sh
.cloud/manual-setup.sh
```

---

## PART 2: CONFIGURE YOUR ENVIRONMENT (10 minutes)

### Step 1: Get your Project ID

```bash
# From the setup script output, save this value:
# "Generated Project ID: research-ide-XXXXX"

# Or check it:
gcloud config get-value project
```

### Step 2: Create .env.cloud file

```bash
cd .cloud

# Copy template
cp .env.cloud.template .env.cloud

# Open in editor
nano .env.cloud
# OR
code .env.cloud
```

### Step 3: Fill in the configuration

**Required values** (minimal setup):

```
GCP_PROJECT_ID=research-ide-XXXXX        # From step above
GEMINI_API_KEY=your-actual-key          # Get from https://aistudio.google.com/apikey

# Optional (for Google login):
GOOGLE_CLIENT_ID=your-client-id         # From Google Cloud Console
GOOGLE_CLIENT_SECRET=your-client-secret # From Google Cloud Console
```

**Get your Gemini API Key:**
1. Go to https://aistudio.google.com/apikey
2. Click "Create API Key"
3. Copy it to GEMINI_API_KEY

**Get Google OAuth (optional, for social login):**
1. Go to Google Cloud Console
2. APIs & Services → Credentials
3. Create OAuth 2.0 Web Application
4. Add redirect URIs:
   - `https://research-ide-backend-XXXXX-as.a.run.app/auth/callback`
   - `http://localhost:8000/auth/callback`
5. Copy Client ID and Secret

---

## PART 3: DATABASE MIGRATION (15 minutes)

### Step 1: Install required packages

```bash
cd backend

# Activate virtual environment (if not already)
source .venv/bin/activate

# Install firebase-admin
pip install firebase-admin

# Verify installation
python -c "import firebase_admin; print('Firebase admin installed ✓')"
```

### Step 2: Run migration script

```bash
cd ../.cloud

# Replace XXXXX with your actual Project ID from setup
python migrate_to_firestore.py --project research-ide-XXXXX

# Output should show:
# ✓ Connected to SQLite
# ✓ Firestore initialized
# ✓ Migrated users
# ✓ Migrated projects
# ✓ Migrated papers
# ✓ Migration Complete!
```

### Step 3: Verify migration

```bash
# Check Firestore in Cloud Console:
# https://console.cloud.google.com/firestore/databases?project=research-ide-XXXXX

# Should show:
# - users collection with data
# - projects collection with data
# - papers collection with data
```

---

## PART 4: CODE UPDATES (20-30 minutes)

### Update 1: Install Docker & Build Images

```bash
# Make sure Docker is running
docker --version

# Go to project root
cd /Users/tharungowdapr/Documents/college/projects/research-ide

# Build both images
docker-compose build

# Verify builds
docker images | grep research-ide
```

### Update 2: Update Backend Configuration

Update `backend/core/config.py`:

```python
# OLD (SQLite):
# from sqlalchemy import create_engine
# DATABASE_URL = "sqlite://..."

# NEW (Cloud Firestore):
import firebase_admin
from firebase_admin import firestore

firebase_admin.initialize_app()
db = firestore.client()

# Also add:
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
```

### Update 3: Update Requirements

Add to `backend/requirements.txt`:

```
firebase-admin==7.0.0
```

Then:
```bash
cd backend
pip install -r requirements.txt
```

### Update 4: Update .gitignore

```bash
echo ".env.cloud" >> .gitignore
echo ".env.local" >> .gitignore
```

---

## PART 5: DEPLOY BACKEND (20-30 minutes)

### Step 1: Deploy to Cloud Run

```bash
cd .cloud

# Deploy backend
chmod +x deploy-backend.sh
./deploy-backend.sh research-ide-XXXXX

# What it does:
# ✓ Builds Docker image
# ✓ Pushes to Container Registry
# ✓ Creates Cloud Run service
# ✓ Sets up auto-scaling
# ✓ Returns service URL
```

### Step 2: Get Backend URL

```bash
# From deployment output, save this URL:
# https://research-ide-backend-XXXXX-as.a.run.app

# Or get it with:
gcloud run services describe research-ide-backend \
    --region asia-south1 \
    --format='value(status.url)'
```

### Step 3: Test Backend

```bash
# Replace with your actual URL
BACKEND_URL="https://research-ide-backend-XXXXX-as.a.run.app"

# Health check
curl $BACKEND_URL/api/health

# Should return: {"status": "ok"}

# View logs
gcloud logging read "resource.type=cloud_run_revision" --limit=50
```

---

## PART 6: DEPLOY FRONTEND (15-20 minutes)

### Step 1: Update Backend URL in Frontend

Update `frontend/.env.production`:

```
NEXT_PUBLIC_API_URL=https://research-ide-backend-XXXXX-as.a.run.app
```

### Step 2: Deploy Frontend

```bash
cd .cloud

# Deploy frontend
chmod +x deploy-frontend.sh
./deploy-frontend.sh research-ide-XXXXX

# What it does:
# ✓ Builds Next.js app
# ✓ Uploads to Cloud Storage
# ✓ Configures CDN
# ✓ Returns public URL
```

### Step 3: Get Frontend URL

```bash
# From deployment output, save this URL:
# https://storage.googleapis.com/research-ide-static-research-ide-XXXXX

# Or get it with:
gsutil web get gs://research-ide-static-research-ide-XXXXX
```

### Step 4: Test Frontend

```bash
# Open in browser:
# https://storage.googleapis.com/research-ide-static-research-ide-XXXXX/

# Should show ResearchIDE login page ✓
```

---

## PART 7: FINAL CONFIGURATION (10 minutes)

### Step 1: Update OAuth Redirect URIs

If using Google login:

1. Go to Google Cloud Console
2. APIs & Services → Credentials
3. Edit your OAuth app
4. Add your actual frontend & backend URLs to redirect URIs:

```
https://storage.googleapis.com/research-ide-static-research-ide-XXXXX/
https://research-ide-backend-XXXXX-as.a.run.app/auth/callback
```

### Step 2: Update CORS in Backend

Update `backend/main.py`:

```python
CORS_ORIGINS = [
    "https://storage.googleapis.com/research-ide-static-XXXXX",
    "https://research-ide-backend-XXXXX-as.a.run.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    ...
)
```

### Step 3: Verify Everything Works

1. Open frontend URL
2. Try to login with Google
3. Create a new project
4. Upload papers
5. Check Cloud Logging for any errors

---

## PART 8: MONITOR COSTS (Ongoing)

### Check Free Tier Usage

```bash
cd .cloud

# Real-time cost monitoring
chmod +x monitor-costs.sh
./monitor-costs.sh

# Output should show:
# ✓ Cloud Run: 0% of free tier
# ✓ Firestore: 0% of free tier
# ✓ Cloud Storage: 0% of free tier
# TOTAL: $0-2/month
```

### Set Up Cost Alerts (Optional)

```bash
# Create alert if spending exceeds $10/month
gcloud billing budgets create \
    --billing-account=$(gcloud billing accounts list --format="value(name)" | head -1) \
    --display-name="ResearchIDE Alert" \
    --budget-amount=10 \
    --threshold-rule=percent=50,percent=90,percent=100
```

---

## ✅ VERIFICATION CHECKLIST

After deployment, verify everything:

- [ ] Backend health check returns 200 OK
  ```bash
  curl https://research-ide-backend-XXXXX-as.a.run.app/api/health
  ```

- [ ] Frontend loads without errors
  - Open in browser
  - Check browser console (F12)

- [ ] Firestore has data
  - Check Cloud Console
  - Should see users, projects, papers collections

- [ ] Cloud Storage has files
  ```bash
  gsutil ls gs://research-ide-pdf-cache-XXXXX/
  ```

- [ ] Secrets are created
  ```bash
  gcloud secrets list
  ```

- [ ] Cloud Run service is ACTIVE
  ```bash
  gcloud run services list
  ```

- [ ] Logs appear in Cloud Logging
  ```bash
  gcloud logging read --limit=20
  ```

- [ ] Costs are tracked
  - View: https://console.cloud.google.com/billing

---

## 🆘 TROUBLESHOOTING

### Problem: gcloud: command not found
**Solution:**
```bash
brew install --cask google-cloud-sdk
source /usr/local/Caskroom/google-cloud-sdk/latest/google-cloud-sdk/completion.bash.inc
```

### Problem: Permission denied on Cloud Run deploy
**Solution:**
```bash
gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
    --member="serviceAccount:research-ide-backend@$(gcloud config get-value project).iam.gserviceaccount.com" \
    --role="roles/run.invoker"
```

### Problem: Firestore connection timeout
**Solution:**
```bash
gcloud firestore databases list
# Should show status: ACTIVE
```

### Problem: Frontend getting CORS errors
**Solution:**
1. Update CORS_ORIGINS in backend/main.py
2. Redeploy backend
3. Wait 2 minutes for changes to propagate

### Problem: High costs or unexpected charges
**Solution:**
```bash
cd .cloud && ./monitor-costs.sh
# Check which service is causing costs
# Should be mostly $0
```

---

## 📞 RESOURCES

- [GCP Console](https://console.cloud.google.com)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Firestore Documentation](https://cloud.google.com/firestore/docs)
- [gcloud Documentation](https://cloud.google.com/cli/docs)
- [GCP Free Tier](https://cloud.google.com/free)

---

## 🎉 SUCCESS!

After completing all steps, you should have:

✅ ResearchIDE running on Google Cloud  
✅ Database migrated to Firestore  
✅ Backend on Cloud Run  
✅ Frontend on Cloud Storage + CDN  
✅ OAuth login enabled  
✅ Cost monitoring set up  
✅ All within FREE TIER (~$0-5/month)  

**Total Cost Breakdown:**
- Cloud Run: $0 (2M free requests/month)
- Firestore: $0 (1GB free, 50K reads/day)
- Cloud Storage: $0 (5GB free)
- Cloud Logging: $0 (50GB free)
- Gemini API: ~$1-3 (token-based)
- **TOTAL: $1-3/month** 💰✨

---

**Need help?** Check the troubleshooting section or review the detailed docs in `.cloud/README.md`

**Ready to start?** Begin with Step 1 → Automated Setup ⬆️
