#!/usr/bin/env python3
"""
SQLite to Cloud Firestore Migration Script
Migrates existing SQLite database to Google Cloud Firestore

Usage:
    python migrate_to_firestore.py --source /path/to/research_ide.db --project your-gcp-project
"""

import os
import sys
import sqlite3
import argparse
from datetime import datetime
from typing import Any, Dict, List

try:
    import firebase_admin
    from firebase_admin import credentials
    from firebase_admin import firestore
except ImportError:
    print("Installing required packages...")
    os.system("pip install firebase-admin")
    import firebase_admin
    from firebase_admin import credentials
    from firebase_admin import firestore


class FirestoreMigrator:
    def __init__(self, project_id: str, source_db: str):
        self.project_id = project_id
        self.source_db = source_db
        self.db_connection = None
        self.db = None
        self.stats = {
            'users': 0,
            'projects': 0,
            'papers': 0,
            'errors': 0
        }

    def init_firestore(self):
        """Initialize Firestore connection"""
        print(f"Initializing Firestore for project: {self.project_id}")
        
        # Use Application Default Credentials (ADC)
        # Make sure you've run: gcloud auth application-default login
        try:
            firebase_admin.initialize_app(
                options={'projectId': self.project_id}
            )
        except ValueError:
            # App already initialized
            pass
        
        self.db = firestore.client()
        print("✓ Firestore initialized")

    def connect_sqlite(self):
        """Connect to SQLite database"""
        if not os.path.exists(self.source_db):
            raise FileNotFoundError(f"Database not found: {self.source_db}")
        
        self.db_connection = sqlite3.connect(self.source_db)
        self.db_connection.row_factory = sqlite3.Row
        print(f"✓ Connected to SQLite: {self.source_db}")

    def get_sqlite_tables(self) -> List[str]:
        """Get list of tables in SQLite database"""
        cursor = self.db_connection.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        )
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Found tables: {tables}")
        return tables

    def migrate_users(self):
        """Migrate users from SQLite to Firestore"""
        print("\n📝 Migrating Users...")
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT * FROM users")
        
        users = cursor.fetchall()
        batch = self.db.batch()
        
        for user in users:
            user_data = dict(user)
            user_id = user_data.pop('id')
            
            # Add metadata
            user_data['migrated_at'] = datetime.now()
            user_data['source'] = 'sqlite'
            
            doc_ref = self.db.collection('users').document(str(user_id))
            batch.set(doc_ref, user_data)
        
        batch.commit()
        self.stats['users'] = len(users)
        print(f"✓ Migrated {len(users)} users")

    def migrate_projects(self):
        """Migrate projects from SQLite to Firestore"""
        print("\n📝 Migrating Projects...")
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT * FROM projects")
        
        projects = cursor.fetchall()
        batch = self.db.batch()
        
        for project in projects:
            project_data = dict(project)
            project_id = project_data.pop('id')
            
            # Add metadata
            project_data['migrated_at'] = datetime.now()
            project_data['source'] = 'sqlite'
            
            doc_ref = self.db.collection('projects').document(str(project_id))
            batch.set(doc_ref, project_data)
        
        batch.commit()
        self.stats['projects'] = len(projects)
        print(f"✓ Migrated {len(projects)} projects")

    def migrate_papers(self):
        """Migrate papers from SQLite to Firestore"""
        print("\n📝 Migrating Papers...")
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT * FROM papers")
        
        papers = cursor.fetchall()
        batch = self.db.batch()
        
        for i, paper in enumerate(papers):
            paper_data = dict(paper)
            paper_id = paper_data.pop('id')
            
            # Add metadata
            paper_data['migrated_at'] = datetime.now()
            paper_data['source'] = 'sqlite'
            
            doc_ref = self.db.collection('papers').document(str(paper_id))
            batch.set(doc_ref, paper_data)
            
            # Commit in batches of 500 (Firestore batch limit)
            if (i + 1) % 500 == 0:
                batch.commit()
                batch = self.db.batch()
        
        if papers:
            batch.commit()
        
        self.stats['papers'] = len(papers)
        print(f"✓ Migrated {len(papers)} papers")

    def create_indexes(self):
        """Create recommended Firestore indexes"""
        print("\n📑 Creating Firestore Indexes...")
        
        indexes = [
            # Composite indexes for common queries
            {
                'collection': 'projects',
                'fields': [
                    {'fieldPath': 'user_id', 'order': 'ASCENDING'},
                    {'fieldPath': 'created_at', 'order': 'DESCENDING'}
                ]
            },
            {
                'collection': 'papers',
                'fields': [
                    {'fieldPath': 'project_id', 'order': 'ASCENDING'},
                    {'fieldPath': 'added_at', 'order': 'DESCENDING'}
                ]
            },
        ]
        
        print("Note: Create composite indexes in GCP Console:")
        print("https://console.cloud.google.com/firestore/indexes")
        print("\nRequired indexes:")
        for idx in indexes:
            print(f"  - Collection: {idx['collection']}")
            for field in idx['fields']:
                print(f"    • {field['fieldPath']} ({field['order']})")

    def create_firestore_rules(self):
        """Create Firestore security rules"""
        print("\n🔐 Setting up Firestore Security Rules...")
        
        rules = """
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Users can only read/write their own documents
    match /users/{userId} {
      allow read, write: if request.auth.uid == userId;
    }
    
    // Projects: owned by user
    match /projects/{projectId} {
      allow read, write: if resource.data.user_id == request.auth.uid;
      
      // Subcollections
      match /{document=**} {
        allow read, write: if get(/databases/$(database)/documents/projects/$(projectId)).data.user_id == request.auth.uid;
      }
    }
    
    // Papers: belong to projects
    match /papers/{paperId} {
      allow read, write: if get(/databases/$(database)/documents/projects/$(resource.data.project_id)).data.user_id == request.auth.uid;
    }
    
    // Deny all by default
    match /{document=**} {
      allow read, write: if false;
    }
  }
}
"""
        
        with open('/tmp/firestore_rules.txt', 'w') as f:
            f.write(rules)
        
        print("Save these rules in Firebase Console:")
        print("https://console.firebase.google.com/")
        print("\nRules (also in /tmp/firestore_rules.txt):")
        print(rules)

    def verify_migration(self):
        """Verify migration by checking document counts"""
        print("\n✅ Verifying Migration...")
        
        collections = ['users', 'projects', 'papers']
        for collection in collections:
            count = len(self.db.collection(collection).stream())
            print(f"  {collection}: {count} documents")

    def run(self):
        """Execute full migration"""
        try:
            print("🚀 Starting SQLite → Firestore Migration")
            print("=" * 50)
            
            self.connect_sqlite()
            self.init_firestore()
            
            # Check what tables exist
            tables = self.get_sqlite_tables()
            
            # Migrate each table if it exists
            if 'users' in tables:
                self.migrate_users()
            if 'projects' in tables:
                self.migrate_projects()
            if 'papers' in tables:
                self.migrate_papers()
            
            self.create_indexes()
            self.create_firestore_rules()
            self.verify_migration()
            
            print("\n" + "=" * 50)
            print("✅ Migration Complete!")
            print(f"  Users: {self.stats['users']}")
            print(f"  Projects: {self.stats['projects']}")
            print(f"  Papers: {self.stats['papers']}")
            print(f"  Errors: {self.stats['errors']}")
            
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            sys.exit(1)
        finally:
            if self.db_connection:
                self.db_connection.close()


def main():
    parser = argparse.ArgumentParser(description='Migrate SQLite to Cloud Firestore')
    parser.add_argument(
        '--source',
        default='backend/data/research_ide.db',
        help='Path to SQLite database'
    )
    parser.add_argument(
        '--project',
        required=True,
        help='GCP Project ID'
    )
    
    args = parser.parse_args()
    
    migrator = FirestoreMigrator(args.project, args.source)
    migrator.run()


if __name__ == '__main__':
    main()
