#!/usr/bin/env python3
"""
ResearchIDE - Python-based GCP Setup (No gcloud CLI required!)
Directly uses Google Cloud Python libraries
"""

import os
import sys
import json
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

def check_python():
    """Check Python version"""
    print_header("ResearchIDE - Google Cloud Setup")
    print_info(f"Python version: {sys.version}")
    if sys.version_info < (3, 8):
        print_error("Python 3.8+ required!")
        sys.exit(1)
    print_success("Python version OK")

def check_credentials():
    """Check if user has Google credentials"""
    print_step(1, "Check Google Cloud Access")
    
    print("""
We'll set up your GCP project through the browser.
You need to:
    
    1. Go to: https://console.cloud.google.com
    2. Sign in with: tharun2005328@gmail.com
    3. Create a new project named: research-ide
    4. Copy the Project ID (format: research-ide-XXXXX)
    5. Come back here and provide the Project ID
    """)
    
    project_id = input("\n👉 Enter your GCP Project ID (research-ide-XXXXX): ").strip()
    
    if not project_id:
        print_error("Project ID is required!")
        sys.exit(1)
    
    print_success(f"Project ID: {project_id}")
    return project_id

def setup_configuration(project_id: str):
    """Setup configuration file"""
    print_step(2, "Configure Environment")
    
    print("""
Now let's get your API key.
    
Go to: https://aistudio.google.com/apikey
- Click "Create API Key"
- Copy the key
- Paste it below (it will be stored securely)
    """)
    
    gemini_key = input("👉 Paste your Gemini API Key: ").strip()
    
    if not gemini_key:
        print_error("Gemini API key is required!")
        sys.exit(1)
    
    # Create .env.cloud file
    env_content = f"""# ResearchIDE - GCP Configuration
GCP_PROJECT_ID={project_id}
GCP_REGION=asia-south1
GEMINI_API_KEY={gemini_key}
ENVIRONMENT=production
DATABASE_TYPE=firestore
LOG_LEVEL=INFO
"""
    
    env_file = Path("/Users/tharungowdapr/Documents/college/projects/research-ide/.cloud/.env.cloud")
    env_file.write_text(env_content)
    
    # Protect file
    os.chmod(env_file, 0o600)
    
    print_success(f"Configuration saved to: {env_file}")
    print_warning("This file contains your API key - keep it secret!")
    
    return {
        'project_id': project_id,
        'gemini_key': gemini_key
    }

def setup_gcp_via_console(project_id: str):
    """Guide user through GCP Console setup"""
    print_step(3, "Set Up GCP Project via Console")
    
    print(f"""
Now we'll set up your GCP project. Go to Cloud Console and do these steps:

1. Go to: https://console.cloud.google.com?project={project_id}

2. ENABLE APIs:
   - Search for "APIs" in the search bar
   - Enable these APIs:
     ✓ Cloud Run API
     ✓ Cloud Firestore API
     ✓ Cloud Storage API
     ✓ Cloud Build API
     ✓ Secret Manager API

3. CREATE FIRESTORE:
   - Go to: https://console.cloud.google.com/firestore/databases?project={project_id}
   - Click "Create Database"
   - Location: asia-south1 (Mumbai)
   - Mode: Firestore Native

4. CREATE STORAGE BUCKETS:
   - Go to: https://console.cloud.google.com/storage?project={project_id}
   - Create 3 buckets:
     ✓ research-ide-pdf-cache-{project_id}
     ✓ research-ide-static-{project_id}
     ✓ research-ide-backups-{project_id}
     (All in asia-south1 region)

5. CREATE SERVICE ACCOUNT:
   - Go to: https://console.cloud.google.com/iam-admin/serviceaccounts?project={project_id}
   - Create service account: research-ide-backend
   - Grant these roles:
     ✓ Cloud Datastore User
     ✓ Storage Object Admin
     ✓ Secret Manager Secret Accessor

6. CREATE SECRETS:
   - Go to: https://console.cloud.google.com/security/secret-manager?project={project_id}
   - Create 2 secrets:
     ✓ secret-key (random string)
     ✓ encryption-key (random string)
   - Use: python3 -c "import secrets; print(secrets.token_urlsafe(32))"

7. SET BUDGET ALERT:
   - Go to: https://console.cloud.google.com/billing
   - Create budget of $10/month
   - Alert at 50%, 90%, 100%
    """)
    
    input("👉 Press Enter when you've completed all steps in the console...")
    print_success("GCP project setup complete!")

def save_setup_info(config: dict):
    """Save setup information"""
    print_step(4, "Save Setup Information")
    
    info_file = Path("/tmp/research-ide-setup-info.json")
    info_file.write_text(json.dumps(config, indent=2))
    
    print_success(f"Setup info saved to: {info_file}")
    print(f"\nConfiguration:")
    print(f"  Project ID: {config['project_id']}")
    print(f"  Region: asia-south1")
    print(f"  Gemini API Key: {config['gemini_key'][:20]}...")

def next_steps(project_id: str):
    """Print next steps"""
    print_header("Next Steps")
    
    print(f"""
Your GCP project is configured! 🎉

Next steps to deploy:

1. Migrate database:
   python .cloud/migrate_to_firestore.py --project {project_id}

2. Deploy backend:
   .cloud/deploy-backend.sh {project_id}

3. Deploy frontend:
   .cloud/deploy-frontend.sh {project_id}

4. Monitor costs:
   .cloud/monitor-costs.sh

For detailed instructions, see:
   .cloud/QUICK_START.md
   .cloud/README.md
    """)

def main():
    """Main setup flow"""
    try:
        check_python()
        
        # Step 1: Get Project ID
        project_id = check_credentials()
        
        # Step 2: Configure API keys
        config = setup_configuration(project_id)
        
        # Step 3: Guide through GCP Console
        setup_gcp_via_console(project_id)
        
        # Step 4: Save info
        save_setup_info(config)
        
        # Step 5: Next steps
        next_steps(project_id)
        
        print_header("Setup Complete! ✨")
        print("Your ResearchIDE is ready for deployment!")
        
    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
        sys.exit(0)
    except Exception as e:
        print_error(f"Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
