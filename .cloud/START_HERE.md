# 📋 ResearchIDE Deployment - QUICK CHECKLIST

**Email**: tharun2005328@gmail.com  
**Project**: research-ide  
**Region**: asia-south1 (India - Mumbai)  
**Budget**: $0-10/month  
**Time**: ~1.5-2 hours

---

## 🚀 PHASE 1: GCP SETUP (15-30 min)

```bash
cd /Users/tharungowdapr/Documents/college/projects/research-ide

# Make scripts executable
chmod +x .cloud/*.sh

# Run automated setup (saves ~15 minutes!)
.cloud/gcp-complete-setup.sh
```

**What this does:**
- ✅ Authenticates with your Google account
- ✅ Creates new GCP project (research-ide-XXXXX)
- ✅ Enables all required APIs
- ✅ Creates Cloud Firestore
- ✅ Creates Cloud Storage buckets
- ✅ Creates Service Account
- ✅ Creates Secrets in Secret Manager
- ✅ Sets budget alerts

**⚠️ SAVE YOUR PROJECT ID** from the output!

---

## 🔐 PHASE 2: CONFIGURATION (10 min)

```bash
cd .cloud

# Copy template
cp .env.cloud.template .env.cloud

# Edit file and add:
nano .env.cloud
```

**Minimum required:**
```
GCP_PROJECT_ID=research-ide-XXXXX        # From Phase 1
GEMINI_API_KEY=your-actual-gemini-key    # From https://aistudio.google.com/apikey
GOOGLE_CLIENT_ID=your-client-id          # Optional: for Google login
GOOGLE_CLIENT_SECRET=your-client-secret  # Optional: for Google login
```

---

## 🔄 PHASE 3: MIGRATE DATABASE (15 min)

```bash
cd .cloud

# Run migration
python migrate_to_firestore.py --project research-ide-XXXXX
# ✅ Creates Firestore collections
# ✅ Migrates all data from SQLite
# ✅ Sets up indexes

# Verify in Cloud Console:
# https://console.cloud.google.com/firestore/databases?project=research-ide-XXXXX
```

---

## 🔨 PHASE 4: CODE UPDATES (20-30 min)

```bash
cd backend

# Install firebase client
pip install firebase-admin

# Update requirements.txt - add:
# firebase-admin==7.0.0

# Update core/config.py:
# Replace SQLAlchemy with firebase_admin import
# See .cloud/QUICK_START.md for details
```

---

## ☁️ PHASE 5: DEPLOY BACKEND (20-30 min)

```bash
cd .cloud

# Deploy to Cloud Run
./deploy-backend.sh research-ide-XXXXX

# ✅ Builds Docker image
# ✅ Deploys to Cloud Run
# ✅ Returns backend URL

# Save backend URL: https://research-ide-backend-XXXXX-as.a.run.app
```

**Verify:**
```bash
curl https://research-ide-backend-XXXXX-as.a.run.app/api/health
# Should return: {"status": "ok"}
```

---

## 🌐 PHASE 6: DEPLOY FRONTEND (15-20 min)

```bash
cd .cloud

# Deploy to Cloud Storage
./deploy-frontend.sh research-ide-XXXXX

# ✅ Builds Next.js app
# ✅ Uploads to Cloud Storage
# ✅ Sets up CDN
# ✅ Returns frontend URL

# Save frontend URL: https://storage.googleapis.com/research-ide-static-research-ide-XXXXX/
```

**Verify:**
```bash
# Open in browser:
# https://storage.googleapis.com/research-ide-static-research-ide-XXXXX/
# ✅ Should show login page
```

---

## ✅ FINAL VERIFICATION (10 min)

- [ ] Backend health check passes
  ```bash
  curl https://research-ide-backend-XXXXX-as.a.run.app/api/health
  ```

- [ ] Frontend loads
  - Open in browser
  - No CORS errors in console (F12)

- [ ] Firestore has data
  ```bash
  gcloud firestore databases list
  # Shows ACTIVE database with collections
  ```

- [ ] Cloud Storage is accessible
  ```bash
  gsutil ls gs://research-ide-pdf-cache-research-ide-XXXXX/
  ```

- [ ] Costs are within budget
  ```bash
  cd .cloud && ./monitor-costs.sh
  # Should show ~$0-2/month
  ```

---

## 💰 ESTIMATED MONTHLY COST

| Service | Limit | Your Usage | Cost |
|---------|-------|-----------|------|
| **Cloud Run** | 2M requests | <100/day | **$0** ✅ |
| **Firestore** | 1GB + 50K reads/day | 200 docs | **$0** ✅ |
| **Cloud Storage** | 5GB/month | 1GB | **$0** ✅ |
| **Cloud Logging** | 50GB/month | 10GB | **$0** ✅ |
| **Gemini API** | Pay per token | 10K tokens/day | **$1-3** |
| | | | |
| **TOTAL** | | | **$1-3/month** 🎉 |

---

## 📁 FILE LOCATIONS

All deployment files in: `.cloud/`

```
.cloud/
├── QUICK_START.md                    ← You are here
├── ACTION_PLAN.md                    ← Detailed checklist
├── README.md                         ← Full guide
├── DEPLOYMENT_ANALYSIS.md            ← Technical details
│
├── gcp-complete-setup.sh            ← ⭐ START HERE (automated)
├── manual-setup.sh                   ← Alternative (manual)
│
├── .env.cloud.template              ← Configuration template
├── .env.cloud.setup-guide           ← Setup instructions
│
├── migrate_to_firestore.py           ← Database migration
├── deploy-backend.sh                 ← Deploy backend
├── deploy-frontend.sh                ← Deploy frontend
├── monitor-costs.sh                  ← Monitor costs
│
├── Dockerfile.optimized              ← Optimized Docker
├── app.yaml                          ← Cloud Run config
└── firestore-rules.txt               ← Security rules
```

---

## 🎬 START NOW!

```bash
cd /Users/tharungowdapr/Documents/college/projects/research-ide/.cloud
chmod +x gcp-complete-setup.sh
./gcp-complete-setup.sh
```

**This single command will:**
1. Authenticate you
2. Create GCP project
3. Enable APIs
4. Create Firestore
5. Create buckets
6. Create secrets
7. Set up alerts

**Then follow Phase 2-6 in order above** ⬆️

---

## ❓ COMMON ISSUES

| Issue | Solution |
|-------|----------|
| `gcloud: command not found` | Install: `brew install --cask google-cloud-sdk` |
| `Permission denied` | Run: `gcloud auth login` |
| `Project not found` | Check: `gcloud config get-value project` |
| CORS errors | Update `CORS_ORIGINS` in `backend/main.py` |
| High costs | Run: `.cloud/monitor-costs.sh` |

---

## 📞 HELP

- **Detailed guide**: `.cloud/README.md`
- **Full analysis**: `.cloud/DEPLOYMENT_ANALYSIS.md`
- **Troubleshooting**: `.cloud/QUICK_START.md` → Troubleshooting section
- **GCP Docs**: https://cloud.google.com/docs
- **GCP Console**: https://console.cloud.google.com

---

## ✨ YOU'RE READY!

All files are prepared. Just run the setup script and follow the phases.

**Total time: 1.5-2 hours for full deployment**

**Your app will be live with: $0-3/month cost** 🚀

Let me know when you're ready to start! 💪
