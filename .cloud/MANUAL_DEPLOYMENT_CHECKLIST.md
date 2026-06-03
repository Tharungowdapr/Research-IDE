# ResearchIDE Deployment Checklist


✅ Configuration Ready:
   Project ID: gen-lang-client-0492292104
   Region: asia-south1
   Gemini API Key: (stored in .env.cloud)
   
📋 Deployment Steps:

1. BACKEND DEPLOYMENT
   □ Go to: https://console.cloud.google.com/cloud-build/builds?project=gen-lang-client-0492292104
   □ Click "Create Build"
   □ Select "Cloud Build from GitHub"
   □ Connect your repository
   □ Trigger builds automatically on push
   
   Or manually:
   gcloud builds submit --config=cloudbuild-backend.yaml --project=gen-lang-client-0492292104
   
2. FRONTEND DEPLOYMENT
   □ Build frontend locally:
     cd frontend && npm run build
   
   □ Deploy to Cloud Storage:
     gcloud storage cp -r .next/* gs://research-ide-static-gen-lang-client-0492292104/
   
   □ Set up Cloud CDN:
     https://console.cloud.google.com/compute/backendServices?project=gen-lang-client-0492292104

3. FIRESTORE SETUP
   □ Run migration (if you have existing data):
     python .cloud/migrate_to_firestore.py --project gen-lang-client-0492292104

4. VERIFY DEPLOYMENT
   □ Backend running: https://gen-lang-client-0492292104.run.app/api/docs
   □ Frontend running: https://research-ide-static-gen-lang-client-0492292104.storage.googleapis.com/
   □ Check logs: https://console.cloud.google.com/logs?project=gen-lang-client-0492292104

5. MONITOR COSTS
   □ Run: .cloud/monitor-costs.sh
   □ Check budget alerts: https://console.cloud.google.com/billing?project=gen-lang-client-0492292104

🔗 Useful Links:
   • Cloud Build: https://console.cloud.google.com/cloud-build?project=gen-lang-client-0492292104
   • Cloud Run: https://console.cloud.google.com/run?project=gen-lang-client-0492292104
   • Cloud Storage: https://console.cloud.google.com/storage?project=gen-lang-client-0492292104
   • Firestore: https://console.cloud.google.com/firestore?project=gen-lang-client-0492292104
   • Logs: https://console.cloud.google.com/logs?project=gen-lang-client-0492292104
   • Billing: https://console.cloud.google.com/billing?project=gen-lang-client-0492292104
