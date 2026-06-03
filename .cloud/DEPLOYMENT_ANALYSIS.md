# ResearchIDE - Google Cloud Deployment Analysis & Plan

**Generated**: June 3, 2026  
**Target**: Minimal Cost Deployment on Google Cloud  
**Budget**: $0-10/month  
**Region**: India (Mumbai - asia-south1)

---

## 📋 PROJECT OVERVIEW

| Component | Tech Stack | Current State |
|-----------|-----------|--------------|
| **Backend** | Python 3.9+, FastAPI, SQLAlchemy | SQLite (local), Docker ready |
| **Frontend** | Next.js 14.2, React 18, TypeScript | Docker ready |
| **Database** | SQLite (local) | Needs migration to Cloud Firestore |
| **LLM Integration** | Multi-provider (OpenAI, Anthropic, Groq, Gemini, etc) | API-ready |
| **Storage** | PDF cache, papers | Needs Cloud Storage |

---

## 🎯 DEPLOYMENT ARCHITECTURE (FREE TIER OPTIMIZED)

```
Internet
    ↓
Cloud Load Balancer (free tier: 1 forwarding rule)
    ↓
┌─────────────────────────────────────┐
│     Cloud Run (Backend)             │
│ • Python FastAPI Container          │
│ • Serverless, Auto-scaling          │
│ • asia-south1 (Mumbai)              │
│ • 2 instances max (free tier)        │
└─────────────────────────────────────┘
    ↓
┌──────────────────────┬──────────────────────┐
│  Cloud Firestore     │  Cloud Storage       │
│  • Documents DB      │  • PDF Cache (~5GB)  │
│  • Free tier: 1GB    │  • Free tier: 5GB/mo │
│  • Read quota        │  • Egress: 1GB free  │
└──────────────────────┴──────────────────────┘
    ↓
┌──────────────────────┐
│  Cloud CDN           │
│  • Cache frontend    │
│  • GCS origin        │
└──────────────────────┘
    ↓
Cloud Storage (Static Frontend)
• Next.js static build
• Served via Cloud CDN
```

---

## ✅ IMPLEMENTATION CHECKLIST

### Phase 1: Project Preparation (Current State ✓)
- [x] Backend Docker image working
- [x] Frontend Docker image working
- [x] docker-compose.yml verified
- [ ] **TODO**: Add environment configuration files
- [ ] **TODO**: Create deployment scripts

### Phase 2: Database Migration
- [ ] Migrate SQLite schema to Cloud Firestore
- [ ] Update SQLAlchemy models (ORM → Firestore client)
- [ ] Create Firestore indexes
- [ ] Data migration scripts

### Phase 3: Cloud Infrastructure
- [ ] Create GCP project
- [ ] Enable required APIs
- [ ] Set up Cloud Run deployment
- [ ] Configure Firestore
- [ ] Set up Cloud Storage buckets
- [ ] Configure Cloud CDN

### Phase 4: Code Changes Required
- [x] Backend uses FastAPI (compatible)
- [ ] Switch from SQLite to Firestore ORM
- [ ] Configure secrets management (Secret Manager)
- [ ] Add health checks
- [ ] Optimize Docker images

### Phase 5: Deployment & Testing
- [ ] Deploy backend to Cloud Run
- [ ] Deploy frontend to Cloud Storage + CDN
- [ ] Configure custom domain
- [ ] Set up monitoring
- [ ] Run smoke tests

---

## 🔧 REQUIRED CODE CHANGES

### 1. Database: SQLite → Cloud Firestore

**Current** (`core/database.py`):
```python
DATABASE_URL = "sqlite:////app/data/research_ide.db"
engine = create_engine(DATABASE_URL)
```

**Required Changes**:
- Install: `pip install firebase-admin`
- Replace SQLAlchemy with Firestore client
- Update models to use Firestore document structure

### 2. Configuration Management

**Create**: `core/cloud_config.py`
```python
- Load secrets from Cloud Secret Manager
- Environment-based config (dev/prod)
- Connection strings for GCP services
```

### 3. Storage Backend

**Add**: Cloud Storage support for PDF cache
```python
- Replace local file storage with GCS
- Use signed URLs for file access
- Implement automatic cleanup
```

### 4. Environment Variables

Need to set in Cloud Run:
```
GCP_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/var/secrets/...
GEMINI_API_KEY=[from Secret Manager]
DATABASE_URL=firestore://
GCS_BUCKET=research-ide-papers
```

---

## 💰 DETAILED COST ESTIMATE (Monthly)

### FREE TIER ALLOCATION (Google Cloud Always Free)

| Service | Free Tier | Monthly Cost |
|---------|-----------|--------------|
| **Cloud Run** | 2M requests/month | **FREE** |
| | 360K vCPU-seconds | **FREE** |
| | 180K GiB-seconds memory | **FREE** |
| **Cloud Firestore** | 1 GB storage | **FREE** |
| | 50K reads/day | **FREE** |
| | 20K writes/day | **FREE** |
| | 20K deletes/day | **FREE** |
| **Cloud Storage** | 5 GB/month | **FREE** |
| | 1 GB egress/month | **FREE** |
| **Cloud Logging** | 50 GB/month | **FREE** |
| **Cloud Load Balancer** | 1 forwarding rule | **FREE** |
| **Cloud CDN** | 1 GiB/month cache | **FREE** |

**TOTAL ALWAYS-FREE: $0.00**

### ADDITIONAL SERVICES (IF NEEDED)

If you exceed free tier or add services:

| Service | Scenario | Monthly Cost |
|---------|----------|--------------|
| **Gemini API** | 10K tokens/day | ~$1-5 |
| **Firestore (overage)** | +10GB documents | ~$0.06/GB = $0.60 |
| **Cloud Storage (overage)** | +5GB papers | ~$0.023/GB = $0.12 |
| **Secret Manager** | 6 secrets, active | ~$0.60 |
| **Cloud Trace** | 100GB spans/month | ~$2.00 |
| | | |
| **WORST CASE (Light Usage)** | API calls + minimal storage | **~$5-10** |
| **TYPICAL SCENARIO** | Mostly free tier | **$0-2** |

---

## 🚀 DEPLOYMENT STEPS

### Step 1: GCP Project Setup
```bash
# Create project
gcloud projects create research-ide-prod --name="Research IDE"

# Enable required APIs
gcloud services enable \
  run.googleapis.com \
  firestore.googleapis.com \
  storage-api.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com

# Set region to India (Mumbai)
gcloud config set run/region asia-south1
```

### Step 2: Prepare Codebase
```bash
# Create deployment config
mkdir -p .cloud/gcp

# Create app.yaml for Cloud Run
# Create Firestore migration scripts
# Create secrets configuration
```

### Step 3: Database Setup
```bash
# Initialize Cloud Firestore
gcloud firestore databases create --region=asia-south1

# Run migration scripts (SQLite → Firestore)
python backend/scripts/migrate_to_firestore.py
```

### Step 4: Deploy Backend
```bash
# Deploy to Cloud Run
gcloud run deploy research-ide-backend \
  --source . \
  --runtime python311 \
  --memory 512Mi \
  --cpu 1 \
  --region asia-south1 \
  --allow-unauthenticated
```

### Step 5: Deploy Frontend
```bash
# Build Next.js static
npm run build
gcloud storage buckets create research-ide-static --region asia-south1
gcloud storage cp -r out/* gs://research-ide-static/
```

---

## ⚙️ PERFORMANCE METRICS

### Expected Performance
- **Backend Response Time**: 200-500ms (FastAPI is fast)
- **Frontend Load Time**: <2s (with CDN caching)
- **Concurrent Users**: 5-10 (free tier sufficient)
- **Daily Requests**: <100

### Scaling Limits (Free Tier)
- Max 2 Cloud Run instances
- 50K Firestore reads/day
- 20K writes/day
- 5GB outbound transfer/month

**When to Upgrade**: When exceeding these, costs are ~$2-5 for small increases

---

## 🔐 SECURITY CONSIDERATIONS

### Already Implemented ✓
- AES-256 encryption for API keys
- Bcrypt password hashing
- HTTPS/TLS (automatic with Cloud Run)
- CORS middleware

### Needs Implementation
- [ ] Cloud Secret Manager for API keys
- [ ] Service account authentication (not user passwords)
- [ ] Firestore security rules
- [ ] Cloud Storage bucket policies
- [ ] Cloud Armor (optional, for DDoS)

---

## 📊 RECOMMENDED MONITORING

### Built-in (FREE)
- Cloud Logging (50GB free/month)
- Cloud Run metrics (CPU, Memory, Requests)
- Firestore metrics (reads, writes, storage)

### Optional (PAID)
- Cloud Trace (~$2/month)
- Cloud Profiler (free for Cloud Run)

### Setup
```bash
# View logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50

# Set up alerts (free)
gcloud alpha monitoring policies create --notification-channel=EMAIL
```

---

## 🎬 QUICK START SUMMARY

### For Hobby/Development ($0-2/month):
1. ✅ Use Cloud Run (free tier covers)
2. ✅ Use Cloud Firestore (free tier covers)
3. ✅ Use Cloud Storage for PDFs (free tier covers)
4. ✅ Use Google Gemini API (pay per token: ~$0.001-0.01)
5. ✅ Static frontend on Cloud Storage + CDN

### Next Steps After Answering Questions:
1. Create GCP project setup script
2. Migrate SQLite → Firestore
3. Create Cloud Run deployment config
4. Set up CI/CD pipeline
5. Add monitoring dashboard

---

## ❓ FOLLOW-UP QUESTIONS

Before proceeding, I need a few more details:

1. **Existing GCP Account**: Do you have a Google Cloud account?
2. **Domain**: Do you have a custom domain, or use Cloud Run's default?
3. **Email for Authentication**: Should we use Gmail/Google OAuth?
4. **Backup Strategy**: Do you need automatic backups?
5. **CI/CD**: Should I set up GitHub Actions for auto-deployment?

---

## 📈 COST COMPARISON

| Platform | Backend | Frontend | Database | Storage | **Monthly** |
|----------|---------|----------|----------|---------|-----------|
| **GCP (Our Plan)** | $0* | $0* | $0* | $0* | **$0-10** |
| AWS Free Tier | $5-10 | $5 | $2-5 | $1-3 | **$13-23** |
| Heroku | $50-100 | $50-100 | $20-50 | $10-20 | **$130-270** |
| DigitalOcean | $12-25 | Included | $12-25 | Included | **$24-50** |

*excludes API costs for LLM integration

---

**Generated**: June 3, 2026  
**Status**: Ready for deployment planning phase ✨
