#!/usr/bin/env python3
"""
Firestore Database Manager
Independent script for managing Firestore collections, indexes, and data operations.
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import argparse
import os
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter


class FirestoreManager:
    """Enhanced Firestore manager for ADK chatbot system."""
    
    def __init__(self, project_id: str = None, use_emulator: bool = True):
        """Initialize Firestore client."""
        if use_emulator:
            os.environ['FIRESTORE_EMULATOR_HOST'] = 'localhost:8080'
            print("🔧 Using Firestore Emulator")
        
        self.db = firestore.Client(project=project_id) if project_id else firestore.Client()
        
        # Import collection name mappings from config
        from config import COLLECTIONS
        self.collections = COLLECTIONS
    
    # ==================== COLLECTION SETUP ====================
    
    async def setup_collections(self):
        """Create all collections with sample data."""
        print("🏗️ Setting up Firestore collections...")
        
        # Create collections with initial documents
        await self._create_sample_user_profile()
        await self._create_sample_conversation()
        await self._create_sample_document_request()
        await self._create_sample_adk_session()
        await self._create_system_metadata()
        
        print("✅ All collections created successfully!")
    
    async def _create_sample_user_profile(self):
        """Create sample user profile."""
        user_data = {
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
            "created_at": datetime.now().isoformat(),
            "last_login": datetime.now().isoformat()
        }
        
        self.db.collection(self.collections['user_profiles']).document("dev-user-123").set(user_data)
        print("👤 Created sample user profile")
    
    async def _create_sample_conversation(self):
        """Create sample conversation."""
        conv_id = str(uuid.uuid4())
        conv_data = {
            "id": conv_id,
            "user_id": "dev-user-123",
            "title": "Academic Research Discussion",
            "agent_type": "academic-research",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "message_count": 2,
            "model_settings": {
                "model_name": "academic-research",
                "temperature": 0.7,
                "max_tokens": 2048
            },
            "session_metadata": {
                "adk_session_id": f"adk_{uuid.uuid4()}",
                "last_activity": datetime.now().isoformat(),
                "total_tokens_used": 150
            },
            "tags": ["research", "sample"],
            "status": "active"
        }
        
        self.db.collection(self.collections['conversations']).document(conv_id).set(conv_data)
        
        # Add sample messages
        messages = [
            {
                "id": str(uuid.uuid4()),
                "conversation_id": conv_id,
                "role": "user",
                "content": "Can you help me find recent research on machine learning?",
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "attachments": [],
                    "model_version": "academic-research-v1.0",
                    "processing_time_ms": 0,
                    "token_count": 12
                },
                "edited": False,
                "parent_message_id": None
            },
            {
                "id": str(uuid.uuid4()),
                "conversation_id": conv_id,
                "role": "assistant", 
                "content": "I'd be happy to help you find recent machine learning research. Let me search for the latest papers and trends in this field.",
                "timestamp": (datetime.now() + timedelta(seconds=30)).isoformat(),
                "metadata": {
                    "attachments": [],
                    "model_version": "academic-research-v1.0",
                    "processing_time_ms": 1500,
                    "token_count": 25,
                    "agent_events": []
                },
                "edited": False,
                "parent_message_id": None
            }
        ]
        
        for msg in messages:
            self.db.collection(self.collections['messages']).document(msg["id"]).set(msg)
        
        print("💬 Created sample conversation with messages")
    
    async def _create_sample_document_request(self):
        """Create sample document request."""
        req_id = str(uuid.uuid4())
        req_data = {
            "id": req_id,
            "user_id": "dev-user-123",
            "conversation_id": None,
            "message_id": None,
            "request_type": "rfp",
            "project_details": {
                "project_name": "AI Research Platform",
                "opportunity_id": "opp_sample_123",
                "client_email": "client@example.com",
                "deadline": (datetime.now() + timedelta(days=30)).isoformat()
            },
            "document_config": {
                "template_type": "technical_rfp",
                "sections": ["executive_summary", "technical_approach", "timeline"],
                "format": "pdf",
                "length": "detailed"
            },
            "processing_status": {
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "started_at": None,
                "completed_at": None,
                "progress_percentage": 0,
                "current_stage": "queued",
                "estimated_completion": (datetime.now() + timedelta(minutes=30)).isoformat()
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
                    "timestamp": datetime.now().isoformat(),
                    "status": "created",
                    "details": "Document request created"
                }
            ]
        }
        
        self.db.collection(self.collections['document_requests']).document(req_id).set(req_data)
        print("📄 Created sample document request")
    
    async def _create_sample_adk_session(self):
        """Create sample ADK session."""
        session_id = str(uuid.uuid4())
        session_data = {
            "id": session_id,
            "user_id": "dev-user-123",
            "conversation_id": None,
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
            "created_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
            "access_count": 1,
            "total_tokens": 0,
            "status": "active",
            "expiry_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "backup_frequency": "daily"
        }
        
        self.db.collection(self.collections['adk_sessions']).document(session_id).set(session_data)
        print("🧠 Created sample ADK session")
    
    async def _create_system_metadata(self):
        """Create system metadata."""
        metadata = {
            "schema_version": "2.0",
            "last_updated": datetime.now().isoformat(),
            "supported_agents": ["academic-research", "rfp-generation"],
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
        
        self.db.collection(self.collections['system_metadata']).document("config").set(metadata)
        print("⚙️ Created system metadata")
    
    # ==================== DATA OPERATIONS ====================
    
    async def get_user_conversations(self, user_id: str, limit: int = 20) -> List[Dict]:
        """Get user conversations with pagination."""
        query = (self.db.collection(self.collections['conversations'])
                .where(filter=FieldFilter("user_id", "==", user_id))
                .order_by("updated_at", direction=firestore.Query.DESCENDING)
                .limit(limit))
        
        docs = query.stream()
        conversations = []
        for doc in docs:
            data = doc.to_dict()
            conversations.append(data)
        
        return conversations
    
    async def get_conversation_messages(self, conversation_id: str) -> List[Dict]:
        """Get all messages for a conversation."""
        query = (self.db.collection(self.collections['messages'])
                .where(filter=FieldFilter("conversation_id", "==", conversation_id))
                .order_by("timestamp", direction=firestore.Query.ASCENDING))
        
        docs = query.stream()
        messages = []
        for doc in docs:
            data = doc.to_dict()
            messages.append(data)
        
        return messages
    
    async def create_document_request(self, user_id: str, request_type: str, 
                                    project_details: Dict, document_config: Dict,
                                    conversation_id: str = None, message_id: str = None) -> str:
        """Create a new document generation request."""
        req_id = str(uuid.uuid4())
        req_data = {
            "id": req_id,
            "user_id": user_id,
            "conversation_id": conversation_id,
            "message_id": message_id,
            "request_type": request_type,
            "project_details": project_details,
            "document_config": document_config,
            "processing_status": {
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "started_at": None,
                "completed_at": None,
                "progress_percentage": 0,
                "current_stage": "queued",
                "estimated_completion": (datetime.now() + timedelta(minutes=30)).isoformat()
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
                    "timestamp": datetime.now().isoformat(),
                    "status": "created",
                    "details": "Document request created"
                }
            ]
        }
        
        self.db.collection(self.collections['document_requests']).document(req_id).set(req_data)
        return req_id
    
    async def update_document_status(self, request_id: str, status: str, 
                                   details: str = None, progress: int = None,
                                   output_data: Dict = None):
        """Update document request status (called by Cloud Functions)."""
        doc_ref = self.db.collection(self.collections['document_requests']).document(request_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise ValueError(f"Document request {request_id} not found")
        
        data = doc.to_dict()
        now = datetime.now().isoformat()
        
        # Update processing status
        updates = {
            "processing_status.status": status,
            "processing_status.last_updated": now
        }
        
        if progress is not None:
            updates["processing_status.progress_percentage"] = progress
        
        if status == "in_progress" and not data["processing_status"]["started_at"]:
            updates["processing_status.started_at"] = now
        
        if status == "completed":
            updates["processing_status.completed_at"] = now
            updates["processing_status.progress_percentage"] = 100
            
            if output_data:
                for key, value in output_data.items():
                    updates[f"output_details.{key}"] = value
        
        # Add webhook log
        webhook_log = {
            "timestamp": now,
            "status": status,
            "details": details or f"Status updated to {status}"
        }
        
        # Get current logs and append
        current_logs = data.get("webhook_logs", [])
        current_logs.append(webhook_log)
        updates["webhook_logs"] = current_logs
        
        doc_ref.update(updates)
        print(f"📄 Updated document request {request_id} to {status}")
    
    async def backup_adk_session(self, session_id: str, session_data: Dict):
        """Backup ADK session to Firestore."""
        backup_data = {
            "id": session_id,
            "session_state": session_data,
            "last_backup": datetime.now().isoformat(),
            "backup_size_mb": len(json.dumps(session_data).encode('utf-8')) / (1024 * 1024),
            "status": "active"
        }
        
        self.db.collection(self.collections['adk_sessions']).document(session_id).set(
            backup_data, merge=True
        )
        print(f"💾 Backed up ADK session {session_id}")
    
    async def restore_adk_session(self, session_id: str) -> Optional[Dict]:
        """Restore ADK session from Firestore."""
        doc = self.db.collection(self.collections['adk_sessions']).document(session_id).get()
        
        if not doc.exists:
            return None
        
        data = doc.to_dict()
        
        # Update access tracking
        self.db.collection(self.collections['adk_sessions']).document(session_id).update({
            "last_accessed": datetime.now().isoformat(),
            "access_count": firestore.Increment(1)
        })
        
        print(f"🔄 Restored ADK session {session_id}")
        return data.get("session_state")
    
    # ==================== CLEANUP OPERATIONS ====================
    
    async def cleanup_expired_sessions(self):
        """Clean up expired ADK sessions."""
        cutoff_date = datetime.now() - timedelta(days=7)
        
        query = (self.db.collection(self.collections['adk_sessions'])
                .where(filter=FieldFilter("expiry_date", "<", cutoff_date.isoformat())))
        
        docs = query.stream()
        deleted_count = 0
        
        for doc in docs:
            doc.reference.delete()
            deleted_count += 1
        
        print(f"🧹 Cleaned up {deleted_count} expired ADK sessions")
    
    async def archive_old_conversations(self, days_old: int = 30):
        """Archive conversations older than specified days."""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        query = (self.db.collection(self.collections['conversations'])
                .where(filter=FieldFilter("updated_at", "<", cutoff_date.isoformat()))
                .where(filter=FieldFilter("status", "==", "active")))
        
        docs = query.stream()
        archived_count = 0
        
        for doc in docs:
            doc.reference.update({"status": "archived"})
            archived_count += 1
        
        print(f"📦 Archived {archived_count} old conversations")
    
    # ==================== ANALYTICS ====================
    
    async def get_usage_analytics(self, user_id: str = None) -> Dict:
        """Get usage analytics for user or system-wide."""
        analytics = {
            "total_conversations": 0,
            "total_messages": 0,
            "total_document_requests": 0,
            "active_sessions": 0,
            "storage_usage_mb": 0
        }
        
        # Count conversations
        conv_query = self.db.collection(self.collections['conversations'])
        if user_id:
            conv_query = conv_query.where(filter=FieldFilter("user_id", "==", user_id))
        
        conversations = list(conv_query.stream())
        analytics["total_conversations"] = len(conversations)
        
        # Count messages
        if user_id:
            # Get user's conversation IDs
            conv_ids = [doc.to_dict()["id"] for doc in conversations]
            if conv_ids:
                msg_query = (self.db.collection(self.collections['messages'])
                           .where(filter=FieldFilter("conversation_id", "in", conv_ids[:10])))  # Firestore limit
                analytics["total_messages"] = len(list(msg_query.stream()))
        else:
            analytics["total_messages"] = len(list(self.db.collection(self.collections['messages']).stream()))
        
        # Count document requests
        doc_query = self.db.collection(self.collections['document_requests'])
        if user_id:
            doc_query = doc_query.where(filter=FieldFilter("user_id", "==", user_id))
        
        analytics["total_document_requests"] = len(list(doc_query.stream()))
        
        # Count active sessions
        session_query = (self.db.collection(self.collections['adk_sessions'])
                        .where(filter=FieldFilter("status", "==", "active")))
        if user_id:
            session_query = session_query.where(filter=FieldFilter("user_id", "==", user_id))
        
        analytics["active_sessions"] = len(list(session_query.stream()))
        
        return analytics
    
    # ==================== COLLECTION MANAGEMENT ====================
    
    async def create_collection(self, collection_name: str, sample_data: Dict = None):
        """Create a new collection with optional sample data."""
        if collection_name in self.collections.values():
            print(f"⚠️ Collection '{collection_name}' already exists")
            return
        
        # Add to collections registry
        self.collections[collection_name] = collection_name
        
        if sample_data:
            doc_id = sample_data.get("id", str(uuid.uuid4()))
            self.db.collection(collection_name).document(doc_id).set(sample_data)
            print(f"✅ Created collection '{collection_name}' with sample data")
        else:
            # Create empty collection by adding a placeholder document
            placeholder = {
                "id": "placeholder",
                "created_at": datetime.now().isoformat(),
                "type": "placeholder"
            }
            self.db.collection(collection_name).document("placeholder").set(placeholder)
            print(f"✅ Created empty collection '{collection_name}'")
    
    async def delete_collection(self, collection_name: str, confirm: bool = False):
        """Delete entire collection with confirmation."""
        if not confirm:
            print(f"⚠️ This will DELETE ALL data in '{collection_name}' collection!")
            print("Use --confirm flag to proceed")
            return
        
        docs = self.db.collection(collection_name).stream()
        batch = self.db.batch()
        count = 0
        
        for doc in docs:
            batch.delete(doc.reference)
            count += 1
            
            if count % 500 == 0:
                batch.commit()
                batch = self.db.batch()
        
        if count % 500 != 0:
            batch.commit()
        
        # Remove from collections registry
        if collection_name in self.collections:
            del self.collections[collection_name]
        
        print(f"🗑️ Deleted {count} documents from '{collection_name}'")
    
    async def add_field_to_collection(self, collection_name: str, field_name: str, default_value: Any):
        """Add new field to all documents in collection."""
        docs = self.db.collection(collection_name).stream()
        batch = self.db.batch()
        count = 0
        
        for doc in docs:
            data = doc.to_dict()
            if field_name not in data:
                batch.update(doc.reference, {field_name: default_value})
                count += 1
                
                if count % 500 == 0:
                    batch.commit()
                    batch = self.db.batch()
        
        if count % 500 != 0:
            batch.commit()
        
        print(f"✅ Added field '{field_name}' to {count} documents in {collection_name}")
    
    async def rename_field(self, collection_name: str, old_field: str, new_field: str):
        """Rename field in all documents."""
        docs = self.db.collection(collection_name).stream()
        batch = self.db.batch()
        count = 0
        
        for doc in docs:
            data = doc.to_dict()
            if old_field in data:
                batch.update(doc.reference, {
                    new_field: data[old_field],
                    old_field: firestore.DELETE_FIELD
                })
                count += 1
                
                if count % 500 == 0:
                    batch.commit()
                    batch = self.db.batch()
        
        if count % 500 != 0:
            batch.commit()
        
        print(f"✅ Renamed '{old_field}' to '{new_field}' in {count} documents")
    
    async def remove_field_from_collection(self, collection_name: str, field_name: str):
        """Remove field from all documents in collection."""
        docs = self.db.collection(collection_name).stream()
        batch = self.db.batch()
        count = 0
        
        for doc in docs:
            data = doc.to_dict()
            if field_name in data:
                batch.update(doc.reference, {field_name: firestore.DELETE_FIELD})
                count += 1
                
                if count % 500 == 0:
                    batch.commit()
                    batch = self.db.batch()
        
        if count % 500 != 0:
            batch.commit()
        
        print(f"🗑️ Removed field '{field_name}' from {count} documents in {collection_name}")
    
    async def list_collections(self):
        """List all collections in the database."""
        collections = self.db.collections()
        print("📚 Available collections:")
        
        for collection in collections:
            doc_count = len(list(collection.stream()))
            print(f"  📁 {collection.id}: {doc_count} documents")
    
    async def test_connection(self):
        """Test Firestore connection."""
        try:
            # Try to read system metadata
            doc = self.db.collection('system_metadata').document('config').get()
            
            if doc.exists:
                print("✅ Firestore connection successful")
                data = doc.to_dict()
                print(f"   Schema version: {data.get('schema_version', 'unknown')}")
                return True
            else:
                print("⚠️ Connected but no system metadata found")
                print("   Run 'python firestore_manager.py setup' to initialize")
                return False
                
        except Exception as e:
            print(f"❌ Firestore connection failed: {e}")
            print("   Check your credentials and project ID")
            return False
    
    # ==================== MAINTENANCE ====================
    
    async def optimize_storage(self):
        """Optimize storage by compressing old data."""
        print("🔧 Starting storage optimization...")
        
        # Compress old messages (remove agent_events from old messages)
        cutoff_date = datetime.now() - timedelta(days=7)
        
        query = (self.db.collection(self.collections['messages'])
                .where(filter=FieldFilter("timestamp", "<", cutoff_date.isoformat())))
        
        docs = query.stream()
        optimized_count = 0
        
        for doc in docs:
            data = doc.to_dict()
            if "metadata" in data and "agent_events" in data["metadata"]:
                # Remove large agent_events array
                doc.reference.update({
                    "metadata.agent_events": firestore.DELETE_FIELD
                })
                optimized_count += 1
        
        print(f"💾 Optimized {optimized_count} old messages")
    
    async def daily_maintenance(self):
        """Run daily maintenance tasks."""
        print("🔧 Starting daily maintenance...")
        
        # 1. Clean up expired sessions
        expired_count = await self.cleanup_expired_sessions()
        
        # 2. Compress old messages
        compressed_count = await self.optimize_storage()
        
        # 3. Archive old conversations
        await self.archive_old_conversations(days_old=30)
        
        # 4. Update system analytics
        analytics = await self.get_usage_analytics()
        
        self.db.collection('system_metadata').document('daily_stats').set({
            'date': datetime.now().isoformat(),
            'expired_sessions_cleaned': expired_count,
            'system_analytics': analytics
        })
        
        print("✅ Daily maintenance completed")
    
    async def generate_weekly_report(self):
        """Generate weekly usage report."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # Query conversations created this week
        weekly_conversations = list(
            self.db.collection('conversations')
            .where(filter=FieldFilter("created_at", ">=", start_date.isoformat()))
            .where(filter=FieldFilter("created_at", "<=", end_date.isoformat()))
            .stream()
        )
        
        # Query document requests this week
        weekly_docs = list(
            self.db.collection('document_requests')
            .where(filter=FieldFilter("processing_status.created_at", ">=", start_date.isoformat()))
            .stream()
        )
        
        report = {
            'week_ending': end_date.isoformat(),
            'new_conversations': len(weekly_conversations),
            'document_requests': len(weekly_docs),
            'active_users': len(set(doc.to_dict()['user_id'] for doc in weekly_conversations))
        }
        
        print("📊 Weekly Report:")
        for key, value in report.items():
            print(f"  {key}: {value}")
        
        return report
    
    async def backup_database(self, backup_path: str = "firestore_backup.json"):
        """Create a JSON backup of all collections."""
        backup_data = {}
        
        for collection_name in self.collections.values():
            docs = self.db.collection(collection_name).stream()
            backup_data[collection_name] = {}
            
            for doc in docs:
                backup_data[collection_name][doc.id] = doc.to_dict()
        
        with open(backup_path, 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)
        
        print(f"💾 Database backed up to {backup_path}")
    
    # ==================== QUERY HELPERS ====================
    
    async def search_conversations(self, user_id: str, query: str, limit: int = 10) -> List[Dict]:
        """Search conversations by title or content."""
        # Simple text search (Firestore doesn't have full-text search)
        conv_query = (self.db.collection(self.collections['conversations'])
                     .where(filter=FieldFilter("user_id", "==", user_id))
                     .order_by("updated_at", direction=firestore.Query.DESCENDING)
                     .limit(limit * 2))  # Get more to filter
        
        docs = conv_query.stream()
        results = []
        
        for doc in docs:
            data = doc.to_dict()
            if query.lower() in data.get("title", "").lower():
                results.append(data)
                if len(results) >= limit:
                    break
        
        return results
    
    async def get_pending_document_requests(self) -> List[Dict]:
        """Get all pending document requests."""
        query = (self.db.collection(self.collections['document_requests'])
                .where(filter=FieldFilter("processing_status.status", "==", "pending"))
                .order_by("processing_status.created_at"))
        
        docs = query.stream()
        return [doc.to_dict() for doc in docs]


# ==================== CLI INTERFACE ====================

async def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="Firestore Database Manager")
    parser.add_argument("--project-id", help="Google Cloud Project ID")
    parser.add_argument("--emulator", action="store_true", default=True, 
                       help="Use Firestore emulator (default: True)")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Setup collections with sample data")
    
    # Analytics command
    analytics_parser = subparsers.add_parser("analytics", help="Show usage analytics")
    analytics_parser.add_argument("--user-id", help="User ID for user-specific analytics")
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up expired data")
    
    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Backup database to JSON")
    backup_parser.add_argument("--output", default="firestore_backup.json", help="Output file path")
    
    # Document status command
    doc_parser = subparsers.add_parser("update-doc", help="Update document request status")
    doc_parser.add_argument("request_id", help="Document request ID")
    doc_parser.add_argument("status", choices=["pending", "in_progress", "completed", "failed"])
    doc_parser.add_argument("--details", help="Status details")
    doc_parser.add_argument("--progress", type=int, help="Progress percentage")
    
    # Collection management commands
    create_parser = subparsers.add_parser("create-collection", help="Create new collection")
    create_parser.add_argument("collection_name", help="Name of collection to create")
    create_parser.add_argument("--sample-data", help="JSON file with sample data")
    
    delete_parser = subparsers.add_parser("delete-collection", help="Delete collection")
    delete_parser.add_argument("collection_name", help="Name of collection to delete")
    delete_parser.add_argument("--confirm", action="store_true", help="Confirm deletion")
    
    list_parser = subparsers.add_parser("list-collections", help="List all collections")
    
    # Field management commands
    add_field_parser = subparsers.add_parser("add-field", help="Add field to collection")
    add_field_parser.add_argument("collection_name", help="Collection name")
    add_field_parser.add_argument("field_name", help="Field name")
    add_field_parser.add_argument("default_value", help="Default value (JSON format)")
    
    rename_field_parser = subparsers.add_parser("rename-field", help="Rename field in collection")
    rename_field_parser.add_argument("collection_name", help="Collection name")
    rename_field_parser.add_argument("old_field", help="Current field name")
    rename_field_parser.add_argument("new_field", help="New field name")
    
    remove_field_parser = subparsers.add_parser("remove-field", help="Remove field from collection")
    remove_field_parser.add_argument("collection_name", help="Collection name")
    remove_field_parser.add_argument("field_name", help="Field name to remove")
    
    # Connection test
    test_parser = subparsers.add_parser("test-connection", help="Test Firestore connection")
    
    # Maintenance commands
    maintenance_parser = subparsers.add_parser("maintenance", help="Run maintenance tasks")
    maintenance_parser.add_argument("--daily", action="store_true", help="Run daily maintenance")
    
    report_parser = subparsers.add_parser("weekly-report", help="Generate weekly usage report")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize manager
    manager = FirestoreManager(project_id=args.project_id, use_emulator=args.emulator)
    
    try:
        if args.command == "setup":
            await manager.setup_collections()
        
        elif args.command == "analytics":
            analytics = await manager.get_usage_analytics(args.user_id)
            print("\n📊 Usage Analytics:")
            for key, value in analytics.items():
                print(f"  {key}: {value}")
        
        elif args.command == "cleanup":
            await manager.cleanup_expired_sessions()
            await manager.archive_old_conversations()
            await manager.optimize_storage()
        
        elif args.command == "backup":
            await manager.backup_database(args.output)
        
        elif args.command == "update-doc":
            await manager.update_document_status(
                args.request_id, 
                args.status,
                details=args.details,
                progress=args.progress
            )
        
        elif args.command == "create-collection":
            sample_data = None
            if args.sample_data:
                with open(args.sample_data, 'r') as f:
                    sample_data = json.load(f)
            await manager.create_collection(args.collection_name, sample_data)
        
        elif args.command == "delete-collection":
            await manager.delete_collection(args.collection_name, args.confirm)
        
        elif args.command == "list-collections":
            await manager.list_collections()
        
        elif args.command == "add-field":
            try:
                default_value = json.loads(args.default_value)
            except json.JSONDecodeError:
                default_value = args.default_value  # Treat as string
            await manager.add_field_to_collection(args.collection_name, args.field_name, default_value)
        
        elif args.command == "rename-field":
            await manager.rename_field(args.collection_name, args.old_field, args.new_field)
        
        elif args.command == "remove-field":
            await manager.remove_field_from_collection(args.collection_name, args.field_name)
        
        elif args.command == "test-connection":
            await manager.test_connection()
        
        elif args.command == "maintenance":
            if args.daily:
                await manager.daily_maintenance()
            else:
                await manager.cleanup_expired_sessions()
                await manager.optimize_storage()
        
        elif args.command == "weekly-report":
            await manager.generate_weekly_report()
        
        print("✅ Operation completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
