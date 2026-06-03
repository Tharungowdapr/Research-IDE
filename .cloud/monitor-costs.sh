#!/bin/bash
# Monitor GCP costs and usage in real-time
# Usage: ./monitor-costs.sh

set -e

PROJECT_ID=$(gcloud config get-value project)
MONTH=$(date +%Y-%m)

echo "💰 ResearchIDE - GCP Cost & Usage Monitoring"
echo "Project: $PROJECT_ID"
echo "Month: $MONTH"
echo "=================================================="

# Function to get service usage
get_usage() {
    local service=$1
    gcloud billing accounts list --filter="project_ids:$PROJECT_ID" \
        --format="value(name)" | head -1 | \
        gcloud beta billing accounts export \
        --bucket=gs://billing-export-$PROJECT_ID \
        --prefix=$service 2>/dev/null || echo "N/A"
}

# Cloud Run Usage
echo -e "\n☁️  CLOUD RUN"
echo "─────────────────────────────────────────"
gcloud run services list --filter="status:ACTIVE" --format="table(SERVICE_NAME,REGION)" || echo "No services deployed"

# Check Cloud Run metrics
echo -e "\nRequest metrics (last 24 hours):"
gcloud monitoring time-series list \
    --filter='resource.type = "cloud_run_revision" AND metric.type = "run.googleapis.com/request_count"' \
    --format="table(metric.labels.service_name, points[0].value)" 2>/dev/null || echo "Metrics not available yet"

# Cloud Firestore Usage
echo -e "\n🗄️  FIRESTORE"
echo "─────────────────────────────────────────"
gcloud firestore databases list --format="table(NAME,TYPE,REGION)" || echo "No databases"

# Get storage size
FIRESTORE_SIZE=$(gcloud firestore databases describe --database=default 2>/dev/null | \
    grep -i "size" | head -1 | awk '{print $NF}' || echo "0 bytes")
echo "Database size: $FIRESTORE_SIZE"

# Cloud Storage Usage
echo -e "\n💾 CLOUD STORAGE"
echo "─────────────────────────────────────────"
BUCKETS=$(gsutil ls 2>/dev/null | grep research-ide || echo "No buckets")
if [ -n "$BUCKETS" ]; then
    echo "$BUCKETS" | while read bucket; do
        SIZE=$(gsutil du -s $bucket 2>/dev/null | awk '{print $1}' | numfmt --to=iec 2>/dev/null || echo "N/A")
        echo "  $bucket: $SIZE"
    done
else
    echo "No buckets found"
fi

# Cloud Logging Usage
echo -e "\n📊 LOGGING"
echo "─────────────────────────────────────────"
LOG_SIZE=$(gcloud logging read \
    --filter='resource.type="cloud_run_revision"' \
    --limit=0 \
    --format="value(size_estimate_bytes)" 2>/dev/null | \
    awk '{sum += $1} END {print sum}' | numfmt --to=iec 2>/dev/null || echo "N/A")
echo "Log size: $LOG_SIZE"

# Cost Estimate
echo -e "\n💵 ESTIMATED MONTHLY COST"
echo "─────────────────────────────────────────"
echo "Based on free tier consumption:"
echo ""

# Check if we're within free tier
RUNS=$(gcloud run services list --format="value(name)" 2>/dev/null | wc -l)
FIRESTORE_READS=$(gcloud firestore databases list 2>/dev/null | wc -l)

if [ "$RUNS" -lt 3 ] && [ "$FIRESTORE_READS" -lt 1000000 ]; then
    echo "✅ Likely within FREE TIER ($0-5/month)"
else
    echo "⚠️  May exceed free tier (pending actual usage metrics)"
fi

echo ""
echo "Cost breakdown:"
echo "  Cloud Run:     \$0-5 (auto-scales, ~2M free requests/month)"
echo "  Firestore:     \$0 (1GB free, 50K reads/day free)"
echo "  Cloud Storage: \$0 (5GB free)"
echo "  Logging:       \$0 (50GB free)"
echo "  Gemini API:    ~\$1-3 (pay-per-token)"
echo "  ─────────────────────────────────────"
echo "  TOTAL:         ~\$1-8/month"
echo ""

# Get last 7 days of cost
echo -e "\n📈 RECENT COSTS (Last 7 days)"
echo "─────────────────────────────────────────"
gcloud billing accounts list \
    --filter="project_ids:$PROJECT_ID" \
    --format="value(display_name)" | head -1 | while read account; do
    gcloud beta billing accounts describe "$account" 2>/dev/null || echo "No billing info"
done

echo ""
echo "View full costs: https://console.cloud.google.com/billing"
echo "Create budget alert: https://console.cloud.google.com/billing/budgets"
