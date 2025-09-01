#!/usr/bin/env python3
"""
Simplified Firestore Database Setup Script for IntelliSurf AI
Creates collections, initializes with sample data, and manages Vertex AI credentials.
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional
import argparse

try:
    from google.cloud import firestore
    from google.oauth2 import service_account
    import google.auth
except ImportError:
    print("❌ Missing dependencies. Install with: pip install google-cloud-firestore google-auth")
    sys.exit(1)

# Import configuration
from config import (
    COLLECTIONS, COLLECTION_SCHEMAS, VERTEX_AI_CONFIG, FIRESTORE_CONFIG,
    get_collection_name, get_all_collections, get_sample_data, validate_config
)

class FirestoreSetup:
    """Simplified Firestore database setup and management."""
    
    def __init__(self, project_id: str, credentials_path: Optional[str] = None):
        self.project_id = project_id
        self.credentials_path = credentials_path
        self.db = None
        
    def initialize_client(self) -> bool:
        """Initialize Firestore client with credentials."""
        try:
            # Check for emulator
            if FIRESTORE_CONFIG["use_emulator"] and FIRESTORE_CONFIG["emulator_host"]:
                os.environ["FIRESTORE_EMULATOR_HOST"] = FIRESTORE_CONFIG["emulator_host"]
                self.db = firestore.Client(project=self.project_id)
                print(f"🔧 Connected to Firestore Emulator: {FIRESTORE_CONFIG['emulator_host']}")
                return True
            
            # Use service account credentials if provided
            if self.credentials_path and os.path.exists(self.credentials_path):
                credentials = service_account.Credentials.from_service_account_file(self.credentials_path)
                self.db = firestore.Client(project=self.project_id, credentials=credentials)
                print(f"🔑 Using service account: {self.credentials_path}")
            else:
                # Use default credentials (ADC)
                self.db = firestore.Client(project=self.project_id)
                print("🔑 Using Application Default Credentials")
            
            # Test connection
            self.db.collection("test").limit(1).get()
            print(f"✅ Connected to Firestore project: {self.project_id}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to Firestore: {e}")
            return False
    
    def create_collections(self) -> bool:
        """Create all collections with sample data."""
        if not self.db:
            print("❌ Database not initialized")
            return False
        
        success_count = 0
        total_collections = len(COLLECTIONS)
        
        print(f"\n📁 Creating {total_collections} collections...")
        
        for collection_key, collection_name in COLLECTIONS.items():
            try:
                # Get sample data
                sample_data = get_sample_data(collection_key)
                
                if sample_data:
                    # Add timestamps
                    if "created_at" in sample_data or "timestamp" in sample_data:
                        timestamp = datetime.utcnow()
                        if "created_at" in sample_data:
                            sample_data["created_at"] = timestamp
                        if "updated_at" in sample_data:
                            sample_data["updated_at"] = timestamp
                        if "timestamp" in sample_data:
                            sample_data["timestamp"] = timestamp
                        if "last_activity" in sample_data:
                            sample_data["last_activity"] = timestamp
                        if "last_login" in sample_data:
                            sample_data["last_login"] = timestamp
                    
                    # Create document
                    doc_id = sample_data.get("id", sample_data.get("request_id", sample_data.get("session_id", sample_data.get("user_id", sample_data.get("key", "sample_001")))))
                    
                    self.db.collection(collection_name).document(doc_id).set(sample_data)
                    print(f"  ✅ {collection_name} (with sample data)")
                else:
                    # Create empty collection by adding a temporary document
                    self.db.collection(collection_name).document("_init").set({"created_at": datetime.utcnow()})
                    self.db.collection(collection_name).document("_init").delete()
                    print(f"  ✅ {collection_name} (empty)")
                
                success_count += 1
                
            except Exception as e:
                print(f"  ❌ {collection_name}: {e}")
        
        print(f"\n📊 Created {success_count}/{total_collections} collections successfully")
        return success_count == total_collections
    
    def list_collections(self) -> None:
        """List all collections and their document counts."""
        if not self.db:
            print("❌ Database not initialized")
            return
        
        print("\n📋 Current Collections:")
        print("-" * 50)
        
        for collection_name in get_all_collections():
            try:
                docs = self.db.collection(collection_name).limit(1000).get()
                count = len(docs)
                print(f"  📁 {collection_name:<20} ({count} documents)")
            except Exception as e:
                print(f"  ❌ {collection_name:<20} (Error: {e})")
    
    def delete_all_collections(self) -> bool:
        """Delete all collections (use with caution)."""
        if not self.db:
            print("❌ Database not initialized")
            return False
        
        print("\n⚠️  DELETING ALL COLLECTIONS...")
        confirm = input("Type 'DELETE' to confirm: ")
        
        if confirm != "DELETE":
            print("❌ Deletion cancelled")
            return False
        
        success_count = 0
        
        for collection_name in get_all_collections():
            try:
                # Delete all documents in collection
                docs = self.db.collection(collection_name).limit(500).get()
                for doc in docs:
                    doc.reference.delete()
                
                print(f"  ✅ Deleted {collection_name}")
                success_count += 1
                
            except Exception as e:
                print(f"  ❌ {collection_name}: {e}")
        
        print(f"\n🗑️  Deleted {success_count}/{len(COLLECTIONS)} collections")
        return success_count == len(COLLECTIONS)
    
    def validate_setup(self) -> Dict[str, Any]:
        """Validate the database setup."""
        if not self.db:
            return {"status": "error", "message": "Database not initialized"}
        
        validation = {
            "status": "success",
            "collections": {},
            "total_documents": 0
        }
        
        for collection_name in get_all_collections():
            try:
                docs = self.db.collection(collection_name).limit(1000).get()
                count = len(docs)
                validation["collections"][collection_name] = {
                    "exists": True,
                    "document_count": count
                }
                validation["total_documents"] += count
            except Exception as e:
                validation["collections"][collection_name] = {
                    "exists": False,
                    "error": str(e)
                }
        
        return validation

def main():
    """Main function with CLI interface."""
    parser = argparse.ArgumentParser(description="IntelliSurf AI Firestore Database Setup")
    parser.add_argument("--project-id", required=True, help="Google Cloud Project ID")
    parser.add_argument("--credentials", help="Path to service account JSON file")
    parser.add_argument("--action", choices=["create", "list", "delete", "validate"], 
                       default="create", help="Action to perform")
    parser.add_argument("--emulator", action="store_true", help="Use Firestore emulator")
    
    args = parser.parse_args()
    
    # Set emulator if specified
    if args.emulator:
        os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"
    
    print("🚀 IntelliSurf AI Firestore Database Setup")
    print("=" * 50)
    
    # Validate configuration
    config_validation = validate_config()
    print(f"📋 Configuration Status:")
    for key, status in config_validation.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {key}")
    
    # Initialize setup
    setup = FirestoreSetup(args.project_id, args.credentials)
    
    if not setup.initialize_client():
        print("\n❌ Failed to initialize Firestore client")
        sys.exit(1)
    
    # Perform action
    if args.action == "create":
        success = setup.create_collections()
        if success:
            print("\n🎉 Database setup completed successfully!")
            setup.list_collections()
        else:
            print("\n❌ Database setup failed")
            sys.exit(1)
    
    elif args.action == "list":
        setup.list_collections()
    
    elif args.action == "delete":
        setup.delete_all_collections()
    
    elif args.action == "validate":
        validation = setup.validate_setup()
        print(f"\n📊 Validation Results:")
        print(json.dumps(validation, indent=2, default=str))

if __name__ == "__main__":
    main()
