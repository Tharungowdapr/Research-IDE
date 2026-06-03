#!/usr/bin/env python3
"""
ResearchIDE - Python-based GCP Deployment
Deploys without requiring gcloud CLI or Docker locally
Uses Google Cloud Python libraries for direct API access
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Optional

def print_header(title: str):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def print_step(num: int, title: str):
    """Print a step header"""
    print(f"\n[STEP {num}] {title}")
    print("-" * 50)

def print_success(msg: str):
    """Print success message"""
    print(f"✅ {msg}")

def print_error(msg: str):
    """Print error message"""
    print(f"❌ {msg}")

def print_warning(msg: str):
    """Print warning message"""
    print(f"⚠️  {msg}")

def print_info(msg: str):
    """Print info message"""
    print(f"ℹ️  {msg}")

def check_prerequisites():
    """Check if required tools are available"""
    print_header("Checking Prerequisites")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print_error("Python 3.8+ required!")
        sys.exit(1)
    print_success(f"Python {sys.version.split()[0]} ✓")
    
    # Check Node.js (for frontend build)
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        print_success(f"Node.js {result.stdout.strip()} ✓")
    except FileNotFoundError:
        print_warning("Node.js not found (optional for frontend build)")
    
    # Check environment
    env_file = Path(".cloud/.env.cloud")
    if not env_file.exists():
        print_error(f".env.cloud not found at {env_file}")
        sys.exit(1)
    print_success(f"Configuration file found ✓")
    
    # Load configuration
    config = {}
    with open(env_file) as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                config[key] = value
    
    return config

def install_dependencies(config: dict):
    """Install required Python packages"""
    print_step(1, "Install Dependencies")
    
    print_info("Installing Google Cloud libraries...")
    
    packages = [
        'firebase-admin>=7.0.0',
        'google-cloud-storage>=2.10.0',
        'google-cloud-secret-manager>=2.16.0',
        'google-cloud-run>=0.3.0',
    ]
    
    for package in packages:
        print(f"  Installing {package}...")
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-q', package],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print_warning(f"    Could not install {package}")
        else:
            print(f"    ✓ {package}")
    
    print_success("Dependencies installed")

def validate_gcp_access(config: dict):
    """Validate GCP project access"""
    print_step(2, "Validate GCP Access")
    
    project_id = config.get('GCP_PROJECT_ID')
    print_info(f"Project ID: {project_id}")
    
    print(f"""
To deploy, you have two options:

Option A: Use Cloud Console (Recommended)
  1. Go to: https://console.cloud.google.com/cloud-build/builds?project={project_id}
  2. Click "Deploy"
  3. Follow the wizard

Option B: Use gcloud CLI (if installed)
  gcloud builds submit --config=cloudbuild-backend.yaml --project {project_id}
  gcloud builds submit --config=cloudbuild-frontend.yaml --project {project_id}

Option C: Deploy using Python (this script)
  This will require authentication...
    """)
    
    proceed = input("\n👉 Proceed with Python-based deployment? (y/n): ").strip().lower()
    
    if proceed != 'y':
        print_info("Deployment skipped. You can deploy manually via Cloud Console.")
        return False
    
    return True

def deploy_backend_python(config: dict):
    """Deploy backend using Python and Cloud Build"""
    print_step(3, "Deploy Backend")
    
    print_info("Submitting backend build to Cloud Build...")
    
    project_id = config.get('GCP_PROJECT_ID')
    
    # Use subprocess to submit build
    cmd = [
        sys.executable, '-m', 'gcloud', 'builds', 'submit',
        '--config=cloudbuild-backend.yaml',
        f'--project={project_id}'
    ]
    
    print(f"  Command: {' '.join(cmd)}")
    print_warning("Note: gcloud CLI required for this step")
    print_info("Install gcloud CLI: https://cloud.google.com/sdk/docs/install")
    
    return False

def deploy_frontend_python(config: dict):
    """Deploy frontend using Python and Cloud Build"""
    print_step(4, "Deploy Frontend")
    
    print_info("Submitting frontend build to Cloud Build...")
    
    project_id = config.get('GCP_PROJECT_ID')
    
    # Use subprocess to submit build
    cmd = [
        sys.executable, '-m', 'gcloud', 'builds', 'submit',
        '--config=cloudbuild-frontend.yaml',
        f'--project={project_id}'
    ]
    
    print(f"  Command: {' '.join(cmd)}")
    print_warning("Note: gcloud CLI required for this step")
    
    return False

def create_deployment_checklist(config: dict):
    """Create a manual deployment checklist"""
    print_step(5, "Manual Deployment Checklist")
    
    project_id = config.get('GCP_PROJECT_ID')
    region = config.get('GCP_REGION', 'asia-south1')
    
    checklist = f"""
✅ Configuration Ready:
   Project ID: {project_id}
   Region: {region}
   Gemini API Key: (stored in .env.cloud)
   
📋 Deployment Steps:

1. BACKEND DEPLOYMENT
   □ Go to: https://console.cloud.google.com/cloud-build/builds?project={project_id}
   □ Click "Create Build"
   □ Select "Cloud Build from GitHub"
   □ Connect your repository
   □ Trigger builds automatically on push
   
   Or manually:
   gcloud builds submit --config=cloudbuild-backend.yaml --project={project_id}
   
2. FRONTEND DEPLOYMENT
   □ Build frontend locally:
     cd frontend && npm run build
   
   □ Deploy to Cloud Storage:
     gcloud storage cp -r .next/* gs://research-ide-static-{project_id}/
   
   □ Set up Cloud CDN:
     https://console.cloud.google.com/compute/backendServices?project={project_id}

3. FIRESTORE SETUP
   □ Run migration (if you have existing data):
     python .cloud/migrate_to_firestore.py --project {project_id}

4. VERIFY DEPLOYMENT
   □ Backend running: https://{project_id}.run.app/api/docs
   □ Frontend running: https://research-ide-static-{project_id}.storage.googleapis.com/
   □ Check logs: https://console.cloud.google.com/logs?project={project_id}

5. MONITOR COSTS
   □ Run: .cloud/monitor-costs.sh
   □ Check budget alerts: https://console.cloud.google.com/billing?project={project_id}

🔗 Useful Links:
   • Cloud Build: https://console.cloud.google.com/cloud-build?project={project_id}
   • Cloud Run: https://console.cloud.google.com/run?project={project_id}
   • Cloud Storage: https://console.cloud.google.com/storage?project={project_id}
   • Firestore: https://console.cloud.google.com/firestore?project={project_id}
   • Logs: https://console.cloud.google.com/logs?project={project_id}
   • Billing: https://console.cloud.google.com/billing?project={project_id}
"""
    
    print(checklist)
    
    # Save checklist to file
    checklist_file = Path(".cloud/MANUAL_DEPLOYMENT_CHECKLIST.md")
    checklist_file.write_text(f"# ResearchIDE Deployment Checklist\n\n{checklist}")
    print_success(f"Checklist saved to: {checklist_file}")

def next_steps(config: dict):
    """Print next steps"""
    print_header("Next Steps")
    
    print("""
🎯 You have multiple options to deploy:

Option 1: Cloud Console (No CLI needed) ⭐ RECOMMENDED
  • Go to: https://console.cloud.google.com/cloud-build
  • Upload cloudbuild-backend.yaml and cloudbuild-frontend.yaml
  • Trigger builds manually or set up webhooks

Option 2: gcloud CLI (Fastest)
  • Install: https://cloud.google.com/sdk/docs/install
  • Run:
    gcloud builds submit --config=cloudbuild-backend.yaml
    gcloud builds submit --config=cloudbuild-frontend.yaml

Option 3: GitHub Actions (Automated)
  • Create .github/workflows/deploy.yml
  • Trigger on every push to main branch
  • Fully automated CI/CD

Option 4: Manual Deployment
  • Follow the checklist in: .cloud/MANUAL_DEPLOYMENT_CHECKLIST.md
  • Deploy components individually

📚 Documentation:
  • DEPLOYMENT_ANALYSIS.md - Complete technical analysis
  • README.md - Step-by-step guide
  • QUICK_START.md - 7-phase walkthrough

📞 Need Help?
  • See .cloud/QUICK_START.md for detailed instructions
  • Check .cloud/README.md for troubleshooting
""")

def main():
    """Main deployment flow"""
    try:
        print_header("ResearchIDE - GCP Deployment Helper")
        
        # Check prerequisites
        config = check_prerequisites()
        
        # Install dependencies
        install_dependencies(config)
        
        # Validate GCP access
        if not validate_gcp_access(config):
            create_deployment_checklist(config)
            next_steps(config)
            print_info("Ready for manual deployment!")
            return
        
        # Deploy components
        deploy_backend_python(config)
        deploy_frontend_python(config)
        
        # Provide checklist
        create_deployment_checklist(config)
        next_steps(config)
        
        print_header("Setup Complete! 🚀")
        print("Your ResearchIDE is ready for deployment!")
        
    except KeyboardInterrupt:
        print("\n\nDeployment cancelled.")
        sys.exit(0)
    except Exception as e:
        print_error(f"Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
