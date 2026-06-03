# ResearchIDE - GCP Deployment Action Plan

**Project**: ResearchIDE - AI-Powered Research Assistant  
**Target**: Google Cloud Platform (India region - Mumbai)  
**Budget**: $0-10/month  
**Timeline**: 1-2 hours for complete deployment

---

## 🎯 EXECUTIVE SUMMARY

### What We've Created
Your project is ready for deployment to Google Cloud with:
- **Architecture**: Cloud Run (backend) + Cloud Storage (frontend) + Firestore (database)
- **Cost**: Stays within **free tier** = $0-2/month (plus ~$1-3 for Gemini API)
- **Performance**: Auto-scaling, 99% uptime, global CDN support
- **Security**: AES-256 encryption, Firestore security rules, Service accounts

### Files Created
Located in `.cloud/` directory:
```
.cloud/
├── DEPLOYMENT_ANALYSIS.md      (📊 Full technical analysis)
├── README.md                    (📖 Complete deployment guide)
├── .env.cloud.template          (🔐 Configuration template)
├── app.yaml                     (⚙️ Cloud Run config)
├── Dockerfile.optimized         (🐳 Optimized Docker image)
├── deploy-setup.sh              (🚀 Automated setup script)
├── deploy-backend.sh            (🔧 Backend deployment)
├── deploy-frontend.sh           (🌐 Frontend deployment)
├── migrate_to_firestore.py      (🔄 Database migration)
├── firestore-rules.txt          (🔐 Security rules)
└── monitor-costs.sh             (💰 Cost monitoring)
```

---

## 📋 STEP-BY-STEP DEPLOYMENT CHECKLIST

### Phase 1: Preparation (15 minutes)

- [ ] **1.1** Create GCP Project
  - Go to https://console.cloud.google.com
  - Click "Create Project"
  - Name: `research-ide-prod`
  - Note the Project ID

- [ ] **1.2** Install & Authenticate GCP CLI
  ```bash
  brew install --cask google-cloud-sdk
  gcloud auth login
  gcloud config set project YOUR-PROJECT-ID
  ```

- [ ] **1.3** Copy deployment files
  ```bash
  # Already created in .cloud/ directory
  ls .cloud/
  chmod +x .cloud/*.sh
  ```

### Phase 2: GCP Infrastructure Setup (30 minutes)

- [ ] **2.1** Enable required APIs
  ```bash
  gcloud services enable run.googleapis.com firestore.googleapis.com \
      storage-api.googleapis.com cloudbuild.googleapis.com
  ```

- [ ] **2.2** Create Cloud Firestore
  ```bash
  gcloud firestore databases create --region=asia-south1 \
      --database=default --type=firestore-native
  ```

- [ ] **2.3** Create Cloud Storage buckets
  ```bash
  cd .cloud
  bash deploy-setup.sh  # Interactive setup
  ```

- [ ] **2.4** Create Service Account & secrets
  ```bash
  # Done by deploy-setup.sh script
  gcloud secrets create secret-key --data-file=/dev/stdin
  gcloud secrets create encryption-key --data-file=/dev/stdin
  gcloud secrets create gemini-api-key --data-file=/dev/stdin
  ```

### Phase 3: Configuration (15 minutes)

- [ ] **3.1** Configure environment
  ```bash
  cd .cloud
  cp .env.cloud.template .env.cloud
  # Edit .env.cloud with:
  # - GCP_PROJECT_ID
  # - GEMINI_API_KEY
  # - GOOGLE_CLIENT_ID/SECRET (for OAuth)
  # - Other API keys
  ```

- [ ] **3.2** Generate new secret keys
  ```bash
  python3 -c "import secrets; print(secrets.token_urlsafe(32))"
  # Copy output to SECRET_KEY and ENCRYPTION_KEY in .env.cloud
  ```

### Phase 4: Code Migration (30 minutes)

- [ ] **4.1** Migrate SQLite → Firestore
  ```bash
  cd backend
  python migrate_to_firestore.py --project YOUR-PROJECT-ID
  ```

- [ ] **4.2** Update database imports
  - Replace SQLAlchemy SQLite code with Firestore client
  - Update `backend/core/database.py`
  - Install: `pip install firebase-admin`

- [ ] **4.3** Update config files
  - Update `backend/core/config.py` to load from Secret Manager
  - Update CORS to allow Cloud Run URLs

### Phase 5: Deployment (30 minutes)

- [ ] **5.1** Deploy backend
  ```bash
  cd .cloud
  ./deploy-backend.sh
  ```

- [ ] **5.2** Deploy frontend
  ```bash
  ./deploy-frontend.sh
  ```

- [ ] **5.3** Configure Cloud CDN (optional)
  ```bash
  # For better performance
  gcloud compute backend-buckets create research-ide-cdn \
      --gcs-uri-base=gs://research-ide-static-YOUR-PROJECT-ID \
      --enable-cdn
  ```

### Phase 6: Testing & Monitoring (20 minutes)

- [ ] **6.1** Test backend health
  ```bash
  BACKEND_URL=$(gcloud run services describe research-ide-backend \
      --region asia-south1 --format='value(status.url)')
  curl $BACKEND_URL/api/health
  ```

- [ ] **6.2** Test frontend
  ```bash
  gsutil web get gs://research-ide-static-YOUR-PROJECT-ID
  ```

- [ ] **6.3** Set up monitoring
  ```bash
  cd .cloud
  ./monitor-costs.sh
  ```

- [ ] **6.4** Create budget alert
  ```bash
  gcloud billing budgets create --display-name="ResearchIDE" \
      --billing-account=YOUR-BILLING-ID --budget-amount=10
  ```

---

## 💰 ESTIMATED MONTHLY COST

### Cost Breakdown

| Service | Free Tier | Usage | Monthly Cost |
|---------|-----------|-------|--------------|
| **Cloud Run** | 2M requests | <100 req/day | **$0** ✅ |
| **Firestore** | 1GB storage | 200 docs | **$0** ✅ |
| **Cloud Storage** | 5GB/month | 1GB papers | **$0** ✅ |
| **Cloud Logging** | 50GB/month | 10GB logs | **$0** ✅ |
| **Cloud CDN** | 1GB/month | Caching | **$0** ✅ |
| **Gemini API** | — | 10K tokens/day | **$2-3** |
| **Secret Manager** | — | 6 secrets | **~$0.04** |
| | | | |
| **TOTAL** | | | **$2-4/month** |

### When costs increase:
- If you exceed 50K Firestore reads/day: +$0.06 per 100K reads
- If you exceed 5GB Cloud Storage: +$0.023 per GB
- If you exceed 2M Cloud Run requests: +$0.40 per million requests

---

## 🚀 DEPLOYMENT COMMANDS QUICK REFERENCE

```bash
# 1. Initial setup
gcloud config set project YOUR-PROJECT-ID
cd .cloud
chmod +x *.sh
./deploy-setup.sh

# 2. Configure secrets
cp .env.cloud.template .env.cloud
nano .env.cloud  # Edit with your values

# 3. Migrate database
cd ../backend
python migrate_to_firestore.py --project YOUR-PROJECT-ID

# 4. Deploy
cd ../.cloud
./deploy-backend.sh
./deploy-frontend.sh

# 5. Monitor
./monitor-costs.sh
gcloud logging read "resource.type=cloud_run_revision" --limit=50
```

---

## ✅ SUCCESS CRITERIA

After deployment, verify:

- [ ] Backend returns 200 OK on `/api/health`
- [ ] Frontend loads without CORS errors
- [ ] Firestore has migrated data
- [ ] Cloud Storage buckets are accessible
- [ ] Secrets Manager has all required secrets
- [ ] Cloud Run service is "ACTIVE"
- [ ] Logs appear in Cloud Logging
- [ ] Cost monitoring shows $0-5/month

---

## 📞 SUPPORT & TROUBLESHOOTING

### Common Issues

**1. Permission denied on Cloud Run**
```bash
gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
    --member="serviceAccount:research-ide-backend@$(gcloud config get-value project).iam.gserviceaccount.com" \
    --role="roles/run.invoker"
```

**2. Firestore database not found**
```bash
gcloud firestore databases list
# Should show status: ACTIVE
```

**3. Secrets not accessible**
```bash
gcloud secrets list
gcloud secrets versions access latest --secret="secret-key"
```

**4. High costs**
```bash
cd .cloud && ./monitor-costs.sh
# Check which service is causing costs
```

### Resources
- [GCP Free Tier](https://cloud.google.com/free)
- [Cloud Run Docs](https://cloud.google.com/run/docs)
- [Firestore Docs](https://cloud.google.com/firestore/docs)
- [GCP Console](https://console.cloud.google.com)

---

## 🎓 WHAT TO DO NEXT

**Immediate (after deployment)**
1. Test the application thoroughly
2. Set up custom domain (optional)
3. Configure SSL/TLS (automatic with Cloud Run)
4. Monitor first 24 hours of usage

**Short term (1-2 weeks)**
1. Optimize Firestore indexes based on usage patterns
2. Fine-tune Cloud Run memory/CPU allocation
3. Implement Firestore backups
4. Set up monitoring dashboards

**Long term (1+ month)**
1. Consider Cloud CDN for better performance
2. Evaluate auto-scaling limits
3. Implement disaster recovery plan
4. Document runbooks for operations

---

## 📊 ARCHITECTURE DIAGRAM

```
┌─────────────────────────────────────────────────┐
│          Google Cloud Platform (asia-south1)   │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────────────────────────────────────┐  │
│  │    Cloud Load Balancer / Cloud CDN       │  │
│  └──────────────────┬───────────────────────┘  │
│                     │                          │
│         ┌───────────┴──────────┐              │
│         ▼                      ▼              │
│  ┌─────────────┐       ┌──────────────────┐  │
│  │ Cloud Run   │       │ Cloud Storage    │  │
│  │ (Backend)   │       │ (Frontend)       │  │
│  │ 512Mi RAM   │       │ Static Next.js   │  │
│  │ Python 3.11 │       │ CDN cached       │  │
│  └──────┬──────┘       └──────────────────┘  │
│         │                                     │
│         │     ┌─────────────────────┐        │
│         ├────▶│ Cloud Firestore     │        │
│         │     │ Documents: Users,   │        │
│         │     │ Projects, Papers    │        │
│         │     │ 1GB free tier       │        │
│         │     └─────────────────────┘        │
│         │                                     │
│         └────▶ ┌─────────────────────┐       │
│              │ Secret Manager      │        │
│              │ • API Keys          │        │
│              │ • Secrets           │        │
│              └─────────────────────┘        │
│                                              │
│         ┌────────────────────────┐          │
│         │ Cloud Logging & Trace  │          │
│         │ Monitoring & Alerts    │          │
│         └────────────────────────┘          │
│                                              │
└─────────────────────────────────────────────┘
```

---

## 📝 NOTES

- **Region**: asia-south1 (Mumbai) - selected for India based on your input
- **Database**: Cloud Firestore (serverless, scales to zero when idle)
- **Frontend**: Static Next.js build served from Cloud Storage + CDN
- **Auto-scaling**: Cloud Run automatically scales from 0 to 2 instances
- **High availability**: Built-in redundancy with Cloud Run in multiple zones
- **Cost**: ~99% of the time you'll pay $0 (only overage charges)

---

**Status**: ✅ Ready for deployment  
**Last Updated**: June 3, 2026  
**Next Action**: Follow checklist in Phase 1
