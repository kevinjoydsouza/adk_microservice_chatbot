#!/usr/bin/env python3
"""
Comprehensive Firestore Collection Management Script
Single script to create, manage, and maintain Firestore collections for ADK Chatbot Architecture.

Usage:
    python firestore_collection_manager.py create conversations
    python firestore_collection_manager.py create-all
    python firestore_collection_manager.py list
    python firestore_collection_manager.py delete conversations --confirm
    python firestore_collection_manager.py setup-indexes
    python firestore_collection_manager.py validate
"""

import os
import sys
import json
import argparse
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

try:
    from google.cloud import firestore
    from google.oauth2 import service_account
    import google.auth
except ImportError:
    print("❌ Missing dependencies. Install with:")
    print("pip install google-cloud-firestore google-auth")
    sys.exit(1)


class FirestoreCollectionManager:
    """Comprehensive Firestore collection management for ADK Chatbot."""
    
    def __init__(self, project_id: str = None, credentials_path: str = None, use_emulator: bool = False):
        """Initialize Firestore client with proper authentication."""
        self.project_id = project_id or os.getenv('GOOGLE_CLOUD_PROJECT')
        self.credentials_path = credentials_path or os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        # Set up emulator if specified
        if use_emulator:
            os.environ['FIRESTORE_EMULATOR_HOST'] = 'localhost:8080'
            print("🔧 Using Firestore Emulator")
        
        # Initialize client
        self.db = self._initialize_client()
        
        # Import collection schemas from config.py for consistency
        from config import COLLECTIONS, COLLECTION_SCHEMAS
        
        # Collection schemas based on your architecture with versioned names
        self.collection_schemas = {}
        for key, versioned_name in COLLECTIONS.items():
            self.collection_schemas[key] = {
                'versioned_name': versioned_name,
                'description': self._get_collection_description(key),
                'sample_data': self._get_sample_data_for_key(key),
                'indexes': self._get_collection_indexes(key)
            }
    
    def _initialize_client(self) -> firestore.Client:
        """Initialize Firestore client with proper authentication."""
        try:
            if self.credentials_path and os.path.exists(self.credentials_path):
                credentials = service_account.Credentials.from_service_account_file(self.credentials_path)
                client = firestore.Client(project=self.project_id, credentials=credentials)
                print(f"🔑 Using service account: {self.credentials_path}")
            else:
                client = firestore.Client(project=self.project_id)
                print("🔑 Using Application Default Credentials")
            
            # Test connection
            client.collection("test").limit(1).get()
            print(f"✅ Connected to Firestore project: {self.project_id}")
            return client
            
        except Exception as e:
            print(f"❌ Failed to connect to Firestore: {e}")
            print("💡 Make sure to:")
            print("   1. Set GOOGLE_CLOUD_PROJECT environment variable")
            print("   2. Set GOOGLE_APPLICATION_CREDENTIALS or run 'gcloud auth application-default login'")
            print("   3. Enable Firestore API in your GCP project")
            sys.exit(1)
    
    # Helper methods for collection metadata
    def _get_collection_description(self, key: str) -> str:
        """Get description for a collection."""
        descriptions = {
            'conversations': 'Chat conversations with agent metadata',
            'messages': 'Individual chat messages with attachments',
            'document_requests': 'RFP and document generation requests',
            'adk_sessions': 'Persistent ADK session storage',
            'user_profiles': 'User preferences and analytics',
            'system_metadata': 'Application configuration and feature flags'
        }
        return descriptions.get(key, f'{key} collection')
    
    def _get_collection_indexes(self, key: str) -> List[List[str]]:
        """Get index configuration for a collection."""
        indexes = {
            'conversations': [
                ['user_id', 'updated_at', 'DESCENDING'],
                ['agent_type', 'status', 'updated_at'],
                ['user_id', 'agent_type', 'updated_at']
            ],
            'messages': [
                ['conversation_id', 'timestamp', 'ASCENDING'],
                ['user_id', 'timestamp', 'DESCENDING'],
                ['conversation_id', 'role', 'timestamp']
            ],
            'document_requests': [
                ['user_id', 'processing_status.created_at', 'DESCENDING'],
                ['processing_status.status', 'processing_status.created_at', 'ASCENDING'],
                ['user_id', 'request_type', 'processing_status.status'],
                ['conversation_id', 'processing_status.created_at', 'DESCENDING']
            ],
            'adk_sessions': [
                ['user_id', 'last_accessed', 'DESCENDING'],
                ['status', 'expiry_date', 'ASCENDING'],
                ['agent_name', 'user_id', 'last_accessed']
            ],
            'user_profiles': [
                ['email', 'ASCENDING'],
                ['subscription.plan', 'created_at', 'DESCENDING'],
                ['usage_analytics.total_conversations', 'DESCENDING']
            ],
            'system_metadata': []
        }
        return indexes.get(key, [])
    
    def _get_sample_data_for_key(self, key: str) -> Dict[str, Any]:
        """Get sample data for a collection key."""
        if key == 'conversations':
            return self._get_conversation_sample()
        elif key == 'messages':
            return self._get_message_sample()
        elif key == 'document_requests':
            return self._get_document_request_sample()
        elif key == 'adk_sessions':
            return self._get_adk_session_sample()
        elif key == 'user_profiles':
            return self._get_user_profile_sample()
        elif key == 'system_metadata':
            return self._get_system_metadata_sample()
        return {}
    
    # Sample data generators based on your architecture
    def _get_conversation_sample(self) -> Dict[str, Any]:
        """Generate sample conversation data."""
        return {
            "id": "conv_sample_001",
            "user_id": "dev-user-123",
            "title": "Academic Research Discussion",
            "agent_type": "academic-research",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "message_count": 2,
            "model_settings": {
                "model_name": "academic-research",
                "temperature": 0.7,
                "max_tokens": 2048
            },
            "session_metadata": {
                "adk_session_id": "adk_sample_session",
                "last_activity": datetime.now(),
                "total_tokens_used": 150
            },
            "tags": ["research", "sample"],
            "status": "active"
        }
    
    def _get_message_sample(self) -> Dict[str, Any]:
        """Generate sample message data."""
        return {
            "id": "msg_sample_001",
            "conversation_id": "conv_sample_001",
            "role": "user",
            "content": "Can you help me find recent research on machine learning?",
            "timestamp": datetime.now(),
            "metadata": {
                "attachments": [],
                "model_version": "academic-research-v1.0",
                "processing_time_ms": 0,
                "token_count": 12
            },
            "edited": False,
            "parent_message_id": None
        }
    
    def _get_document_request_sample(self) -> Dict[str, Any]:
        """Generate sample document request data."""
        return {
            "id": "doc_req_sample_001",
            "user_id": "dev-user-123",
            "conversation_id": "conv_sample_001",
            "message_id": "msg_sample_001",
            "request_type": "rfp",
            "project_details": {
                "project_name": "AI Research Platform",
                "opportunity_id": "opp_sample_123",
                "client_email": "client@example.com",
                "deadline": (datetime.now() + timedelta(days=30))
            },
            "document_config": {
                "template_type": "technical_rfp",
                "sections": ["executive_summary", "technical_approach", "timeline"],
                "format": "pdf",
                "length": "detailed"
            },
            "processing_status": {
                "status": "pending",
                "created_at": datetime.now(),
                "started_at": None,
                "completed_at": None,
                "progress_percentage": 0,
                "current_stage": "queued",
                "estimated_completion": (datetime.now() + timedelta(minutes=30))
            },
            "output_details": {
                "document_url": None,
                "preview_url": None,
                "word_count": 0,
                "page_count": 0,
                "generation_metadata": {}
            },
            "webhook_logs": [
                {
                    "timestamp": datetime.now(),
                    "status": "created",
                    "details": "Document request created"
                }
            ]
        }
    
    def _get_adk_session_sample(self) -> Dict[str, Any]:
        """Generate sample ADK session data."""
        return {
            "id": "adk_sample_session",
            "user_id": "dev-user-123",
            "conversation_id": "conv_sample_001",
            "agent_name": "academic-research",
            "session_state": {
                "context_history": [],
                "agent_memory": {
                    "research_focus": "machine_learning",
                    "user_expertise": "intermediate",
                    "mentioned_papers": []
                },
                "tool_states": {},
                "user_preferences": {
                    "research_focus": "machine_learning",
                    "citation_style": "apa",
                    "detail_level": "comprehensive"
                }
            },
            "created_at": datetime.now(),
            "last_accessed": datetime.now(),
            "access_count": 1,
            "total_tokens": 0,
            "status": "active",
            "expiry_date": (datetime.now() + timedelta(days=7)),
            "backup_frequency": "daily"
        }
    
    def _get_user_profile_sample(self) -> Dict[str, Any]:
        """Generate sample user profile data."""
        return {
            "id": "dev-user-123",
            "email": "dev@example.com",
            "preferences": {
                "default_agent": "academic-research",
                "ui_theme": "dark",
                "notification_settings": {
                    "document_completion": True,
                    "session_expiry_warning": True
                }
            },
            "usage_analytics": {
                "total_conversations": 0,
                "total_documents_generated": 0,
                "favorite_agent": "academic-research",
                "avg_session_length_minutes": 0
            },
            "subscription": {
                "plan": "free",
                "tokens_used_this_month": 0,
                "token_limit": 50000,
                "document_requests_this_month": 0,
                "document_limit": 10
            },
            "created_at": datetime.now(),
            "last_login": datetime.now()
        }
    
    def _get_system_metadata_sample(self) -> Dict[str, Any]:
        """Generate sample system metadata."""
        return {
            "schema_version": "2.0",
            "last_updated": datetime.now(),
            "supported_agents": ["academic-research", "rfp-research"],
            "feature_flags": {
                "session_persistence": True,
                "document_generation": True,
                "multi_agent_support": False
            },
            "performance_settings": {
                "max_session_size_mb": 100,
                "session_timeout_hours": 2,
                "max_active_sessions_per_user": 3
            }
        }
    
    def delete_collection(self, collection_name: str, batch_size: int = 100) -> bool:
        """Delete a collection and all its documents."""
        if collection_name not in self.collection_schemas:
            print(f"❌ Unknown collection: {collection_name}")
            return False
        
        schema = self.collection_schemas[collection_name]
        versioned_name = schema['versioned_name']
        print(f"🗑️  Deleting collection: {collection_name} -> {versioned_name}")
        
        try:
            collection_ref = self.db.collection(versioned_name)
            docs = collection_ref.stream()
            deleted = 0
            
            for doc in docs:
                doc.reference.delete()
                deleted += 1
                
                if deleted % batch_size == 0:
                    print(f"   Deleted {deleted} documents...")
            
            print(f"   ✅ Deleted {deleted} documents from '{collection_name}'")
            return True
            
        except Exception as e:
            print(f"   ❌ Failed to delete {collection_name}: {e}")
            return False
    
    def list_collections(self) -> List[str]:
        """List all collections in the database."""
        try:
            collections = self.db.collections()
            collection_names = [col.id for col in collections]
            
            if collection_names:
                print(f"📋 Found {len(collection_names)} collections:")
                for name in sorted(collection_names):
                    # Show mapping from versioned name back to logical name
                    logical_name = self._get_logical_name(name)
                    if logical_name:
                        print(f"   • {name} ({logical_name})")
                    else:
                        print(f"   • {name}")
            else:
                print("📋 No collections found in database")
            
            return collection_names
            
        except Exception as e:
            print(f"❌ Failed to list collections: {e}")
            return []
    
    def _get_logical_name(self, versioned_name: str) -> str:
        """Get logical name from versioned collection name."""
        from config import COLLECTIONS
        for logical, versioned in COLLECTIONS.items():
            if versioned == versioned_name:
                return logical
        return ""
    
    def create_collection(self, collection_name: str, with_sample_data: bool = True) -> bool:
        """Create a single collection with optional sample data."""
        if collection_name not in self.collection_schemas:
            print(f"❌ Unknown collection: {collection_name}")
            print(f"Available collections: {list(self.collection_schemas.keys())}")
            return False
        
        schema = self.collection_schemas[collection_name]
        versioned_name = schema['versioned_name']
        print(f"📁 Creating collection: {collection_name} -> {versioned_name}")
        print(f"   Description: {schema['description']}")
        
        try:
            if with_sample_data:
                sample_data = schema['sample_data']
                doc_id = sample_data.get('id', 'sample_001')
                
                self.db.collection(versioned_name).document(doc_id).set(sample_data)
                print(f"   ✅ Created with sample data (doc_id: {doc_id})")
            else:
                # Create empty collection with placeholder
                placeholder = {
                    "id": "_placeholder",
                    "created_at": datetime.now(),
                    "type": "placeholder"
                }
                self.db.collection(versioned_name).document("_placeholder").set(placeholder)
                self.db.collection(versioned_name).document("_placeholder").delete()
                print(f"   ✅ Created empty collection")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Failed to create {collection_name}: {e}")
            return False
    
    def create_all_collections(self, with_sample_data: bool = True) -> bool:
        """Create all collections defined in the schema."""
        print("🏗️ Creating all collections for ADK Chatbot...")
        
        success_count = 0
        total_count = len(self.collection_schemas)
        
        for collection_name in self.collection_schemas.keys():
            if self.create_collection(collection_name, with_sample_data):
                success_count += 1
        
        print(f"\n📊 Created {success_count}/{total_count} collections successfully")
        
        if success_count == total_count:
            print("✅ All collections created successfully!")
            return True
        else:
            print("⚠️ Some collections failed to create")
            return False
    
    def list_collections(self) -> List[str]:
        """List all collections in the database."""
        try:
            collections = self.db.collections()
            collection_names = [col.id for col in collections]
            
            if collection_names:
                print(f"📋 Found {len(collection_names)} collections:")
                for name in sorted(collection_names):
                    # Show mapping from versioned name back to logical name
                    logical_name = self._get_logical_name(name)
                    if logical_name:
                        print(f"   • {name} ({logical_name})")
                    else:
                        print(f"   • {name}")
            else:
                print("📋 No collections found in database")
            
            return collection_names
            
        except Exception as e:
            print(f"❌ Failed to list collections: {e}")
            return []
    
    def _get_logical_name(self, versioned_name: str) -> str:
        """Get logical name from versioned collection name."""
        from config import COLLECTIONS
        for logical, versioned in COLLECTIONS.items():
            if versioned == versioned_name:
                return logical
        return ""
    
    def setup_indexes(self) -> None:
        """Print index creation commands for manual setup in GCP Console."""
        print("📊 Required Firestore Indexes")
        print("=" * 60)
        print("Copy and run these commands in Google Cloud Console or CLI:\n")
        
        for collection_name, schema in self.collection_schemas.items():
            if schema['indexes']:
                print(f"# {collection_name} collection indexes")
                for i, index_fields in enumerate(schema['indexes'], 1):
                    print(f"# Index {i} for {collection_name}")
                    
                    # Format for gcloud command
                    field_specs = []
                    for field in index_fields:
                        if len(field) == 2:
                            field_name, direction = field
                            field_specs.append(f"{field_name}:{direction.lower()}")
                        else:
                            field_specs.append(field)
                    
                    fields_str = ",".join(field_specs)
                    print(f"gcloud firestore indexes composite create --collection-group={collection_name} --field-config={fields_str}")
                print()
    
    def validate_collections(self) -> bool:
        """Validate that all required collections exist and have proper structure."""
        print("🔍 Validating collection structure...")
        
        all_valid = True
        existing_collections = [col.id for col in self.db.collections()]
        
        for collection_name, schema in self.collection_schemas.items():
            versioned_name = schema['versioned_name']
            print(f"\n📁 Validating {collection_name} -> {versioned_name}:")
            
            # Check if versioned collection exists
            if versioned_name not in existing_collections:
                print(f"   ❌ Collection missing")
                all_valid = False
                continue
            
            print(f"   ✅ Collection exists")
            
            # Check if collection has documents
            try:
                docs = list(self.db.collection(versioned_name).limit(1).stream())
                if docs:
                    print(f"   ✅ Has sample data")
                    
                    # Validate sample document structure
                    doc_data = docs[0].to_dict()
                    sample_data = schema['sample_data']
                    
                    missing_fields = []
                    for field in sample_data.keys():
                        if field not in doc_data:
                            missing_fields.append(field)
                    
                    if missing_fields:
                        print(f"   ⚠️  Missing fields: {missing_fields}")
                    else:
                        print(f"   ✅ Document structure valid")
                else:
                    print(f"   ⚠️  Collection empty")
                    
            except Exception as e:
                print(f"   ❌ Validation error: {e}")
                all_valid = False
        
        if all_valid:
            print(f"\n✅ All collections validated successfully!")
        else:
            print(f"\n❌ Some collections have issues")
        
        return all_valid
        print(f"\n📊 Validation Summary:")
        print(f"   Total collections: {len(self.collection_schemas)}")
        print(f"   Total documents: {validation_results['total_documents']}")
        print(f"   Issues found: {len(validation_results['issues'])}")
        
        return validation_results
    
    def _validate_document_structure(self, doc_data: Dict, collection_name: str) -> bool:
        """Validate document structure against expected schema."""
        # Basic validation - check for common required fields
        required_fields = {
            'conversations': ['id', 'user_id', 'title', 'agent_type'],
            'messages': ['id', 'conversation_id', 'role', 'content'],
            'document_requests': ['id', 'user_id', 'request_type'],
            'adk_sessions': ['id', 'user_id', 'agent_name'],
            'user_profiles': ['id', 'email'],
            'system_metadata': ['schema_version']
        }
        
        if collection_name in required_fields:
            for field in required_fields[collection_name]:
                if field not in doc_data:
                    return False
        
        return True
    
    def backup_collections(self, output_file: str = None) -> bool:
        """Create a JSON backup of all collections."""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"firestore_backup_{timestamp}.json"
        
        print(f"💾 Creating backup: {output_file}")
        
        try:
            backup_data = {
                "backup_timestamp": datetime.now().isoformat(),
                "project_id": self.project_id,
                "collections": {}
            }
            
            for collection_name in self.collection_schemas.keys():
                print(f"   Backing up {collection_name}...")
                docs = self.db.collection(collection_name).stream()
                backup_data["collections"][collection_name] = {}
                
                doc_count = 0
                for doc in docs:
                    backup_data["collections"][collection_name][doc.id] = doc.to_dict()
                    doc_count += 1
                
                print(f"   ✅ {collection_name}: {doc_count} documents")
            
            # Save to file
            with open(output_file, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            print(f"✅ Backup saved to {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return False


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Comprehensive Firestore Collection Manager for ADK Chatbot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python firestore_collection_manager.py create conversations
  python firestore_collection_manager.py create-all --no-sample-data
  python firestore_collection_manager.py list
  python firestore_collection_manager.py delete conversations --confirm
  python firestore_collection_manager.py setup-indexes
  python firestore_collection_manager.py validate
  python firestore_collection_manager.py backup --output my_backup.json
        """
    )
    
    parser.add_argument("--project-id", help="Google Cloud Project ID")
    parser.add_argument("--credentials", help="Path to service account JSON file")
    parser.add_argument("--emulator", action="store_true", help="Use Firestore emulator")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Create single collection
    create_parser = subparsers.add_parser("create", help="Create a single collection")
    create_parser.add_argument("collection_name", help="Name of collection to create")
    create_parser.add_argument("--no-sample-data", action="store_true", help="Create without sample data")
    
    # Create all collections
    create_all_parser = subparsers.add_parser("create-all", help="Create all collections")
    create_all_parser.add_argument("--no-sample-data", action="store_true", help="Create without sample data")
    
    # List collections
    list_parser = subparsers.add_parser("list", help="List all collections")
    
    # Delete collection
    delete_parser = subparsers.add_parser("delete", help="Delete a collection")
    delete_parser.add_argument("collection_name", help="Name of collection to delete")
    delete_parser.add_argument("--confirm", action="store_true", help="Confirm deletion")
    
    # Setup indexes
    indexes_parser = subparsers.add_parser("setup-indexes", help="Show index creation commands")
    
    # Validate collections
    validate_parser = subparsers.add_parser("validate", help="Validate all collections")
    
    # Backup collections
    backup_parser = subparsers.add_parser("backup", help="Backup all collections to JSON")
    backup_parser.add_argument("--output", help="Output file path")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize manager
    try:
        manager = FirestoreCollectionManager(
            project_id=args.project_id,
            credentials_path=args.credentials,
            use_emulator=args.emulator
        )
    except SystemExit:
        return
    
    # Execute command
    if args.command == "create":
        with_sample_data = not args.no_sample_data
        manager.create_collection(args.collection_name, with_sample_data)
    
    elif args.command == "create-all":
        with_sample_data = not args.no_sample_data
        manager.create_all_collections(with_sample_data)
    
    elif args.command == "list":
        manager.list_collections()
    
    elif args.command == "delete":
        manager.delete_collection(args.collection_name, args.confirm)
    
    elif args.command == "setup-indexes":
        manager.setup_indexes()
    
    elif args.command == "validate":
        results = manager.validate_collections()
        if results["issues"]:
            print("\n⚠️ Issues found:")
            for issue in results["issues"]:
                print(f"   - {issue}")
    
    elif args.command == "backup":
        manager.backup_collections(args.output)


if __name__ == "__main__":
    main()
