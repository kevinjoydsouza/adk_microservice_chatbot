"""
Production-ready storage solution for IntelliSurf AI
Simple Cloud Storage + Firestore hybrid with local fallback
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
import uuid

# Local fallback storage
class LocalStorage:
    """Local file-based storage for development without Firestore."""
    
    def __init__(self, storage_dir: str = "./local_storage"):
        self.storage_dir = storage_dir
        os.makedirs(f"{storage_dir}/messages", exist_ok=True)
        os.makedirs(f"{storage_dir}/conversations", exist_ok=True)
        os.makedirs(f"{storage_dir}/documents", exist_ok=True)
    
    def store_message(self, conversation_id: str, role: str, content: str, metadata: Dict = None) -> str:
        message_id = f"msg_{uuid.uuid4().hex[:12]}"
        message_data = {
            "id": message_id,
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        with open(f"{self.storage_dir}/messages/{message_id}.json", "w") as f:
            json.dump(message_data, f, indent=2)
        
        return message_id
    
    def get_message_content(self, message_id: str) -> Optional[str]:
        try:
            with open(f"{self.storage_dir}/messages/{message_id}.json", "r") as f:
                data = json.load(f)
                return data.get("content", "")
        except FileNotFoundError:
            return None
    
    def get_conversation_messages(self, conversation_id: str) -> list:
        messages = []
        message_dir = f"{self.storage_dir}/messages"
        
        if not os.path.exists(message_dir):
            return messages
        
        for filename in os.listdir(message_dir):
            if filename.endswith('.json'):
                try:
                    with open(f"{message_dir}/{filename}", "r") as f:
                        data = json.load(f)
                        if data.get("conversation_id") == conversation_id:
                            messages.append({
                                "role": data["role"],
                                "content": data["content"],
                                "timestamp": data["timestamp"],
                                "attachments": data.get("metadata", {}).get("attachments", [])
                            })
                except:
                    continue
        
        # Sort by timestamp
        messages.sort(key=lambda x: x["timestamp"])
        return messages

try:
    from google.cloud import storage
    from google.cloud import firestore
    CLOUD_AVAILABLE = True
except ImportError:
    CLOUD_AVAILABLE = False

class ProductionStorage:
    """Simple production storage: Small data in Firestore, large content in Cloud Storage."""
    
    def __init__(self, project_id: str, bucket_name: str):
        self.project_id = project_id
        self.bucket_name = bucket_name
        self.storage_client = storage.Client(project=project_id)
        self.firestore_client = firestore.Client(project=project_id)
        self.bucket = self.storage_client.bucket(bucket_name)
        
        # Size threshold: anything over 500KB goes to Cloud Storage
        self.size_threshold = 500_000  # 500KB
    
    def store_message(self, conversation_id: str, role: str, content: str, metadata: Dict = None) -> str:
        """Store message with automatic storage decision."""
        message_id = f"msg_{uuid.uuid4().hex[:12]}"
        content_size = len(content.encode('utf-8'))
        
        message_doc = {
            "id": message_id,
            "conversation_id": conversation_id,
            "role": role,
            "timestamp": datetime.utcnow(),
            "content_size": content_size,
            "metadata": metadata or {}
        }
        
        if content_size <= self.size_threshold:
            # Store directly in Firestore
            message_doc["content"] = content
            message_doc["storage_type"] = "firestore"
        else:
            # Store in Cloud Storage
            storage_path = f"messages/{conversation_id}/{message_id}.txt"
            blob = self.bucket.blob(storage_path)
            blob.upload_from_string(content, content_type='text/plain')
            
            message_doc["content_url"] = f"gs://{self.bucket_name}/{storage_path}"
            message_doc["storage_type"] = "cloud_storage"
            message_doc["content_preview"] = content[:200] + "..." if len(content) > 200 else content
        
        # Store message document in Firestore
        self.firestore_client.collection("messages").document(message_id).set(message_doc)
        return message_id
    
    def get_message_content(self, message_id: str) -> Optional[str]:
        """Retrieve message content from appropriate storage."""
        doc = self.firestore_client.collection("messages").document(message_id).get()
        if not doc.exists:
            return None
        
        data = doc.to_dict()
        
        if data.get("storage_type") == "firestore":
            return data.get("content", "")
        
        elif data.get("storage_type") == "cloud_storage":
            content_url = data.get("content_url", "")
            if content_url.startswith("gs://"):
                # Extract blob path from gs:// URL
                blob_path = content_url.replace(f"gs://{self.bucket_name}/", "")
                blob = self.bucket.blob(blob_path)
                return blob.download_as_text()
        
        return None
    
    def store_document_request(self, user_id: str, document_type: str, content: str, metadata: Dict = None) -> str:
        """Store document generation request."""
        request_id = f"doc_{uuid.uuid4().hex[:12]}"
        
        # Always store large documents in Cloud Storage
        storage_path = f"documents/{user_id}/{request_id}.txt"
        blob = self.bucket.blob(storage_path)
        blob.upload_from_string(content, content_type='text/plain')
        
        doc_request = {
            "request_id": request_id,
            "user_id": user_id,
            "document_type": document_type,
            "content_url": f"gs://{self.bucket_name}/{storage_path}",
            "content_size": len(content.encode('utf-8')),
            "status": "completed",
            "created_at": datetime.utcnow(),
            "metadata": metadata or {}
        }
        
        self.firestore_client.collection("document_requests").document(request_id).set(doc_request)
        return request_id
    
    def cleanup_old_content(self, days_old: int = 30):
        """Clean up old Cloud Storage content (optional maintenance)."""
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        # List and delete old blobs
        blobs = self.bucket.list_blobs(prefix="messages/")
        deleted_count = 0
        
        for blob in blobs:
            if blob.time_created.replace(tzinfo=None) < cutoff_date:
                blob.delete()
                deleted_count += 1
        
        return deleted_count

# Smart storage service with automatic fallback
class SimpleMessageService:
    """Drop-in replacement for existing message handling with local fallback."""
    
    def __init__(self, project_id: str = None, bucket_name: str = None):
        # Auto-detect environment and choose storage
        use_cloud = (
            CLOUD_AVAILABLE and 
            project_id and 
            bucket_name and 
            os.getenv("USE_CLOUD_STORAGE", "false").lower() == "true"
        )
        
        if use_cloud:
            try:
                self.storage = ProductionStorage(project_id, bucket_name)
                self.storage_type = "cloud"
                print("✅ Using Cloud Storage + Firestore")
            except Exception as e:
                print(f"⚠️ Cloud storage failed, using local: {e}")
                self.storage = LocalStorage()
                self.storage_type = "local"
        else:
            self.storage = LocalStorage()
            self.storage_type = "local"
            print("📁 Using local file storage")
    
    def add_message_to_conversation(self, conversation_id: str, role: str, content: str, attachments: list = None):
        """Add message - compatible with existing code."""
        metadata = {"attachments": attachments or []}
        return self.storage.store_message(conversation_id, role, content, metadata)
    
    def get_conversation_messages(self, conversation_id: str) -> list:
        """Get all messages for a conversation."""
        if self.storage_type == "local":
            return self.storage.get_conversation_messages(conversation_id)
        
        # Cloud storage logic
        messages = []
        docs = self.storage.firestore_client.collection("messages")\
                   .where("conversation_id", "==", conversation_id)\
                   .order_by("timestamp").get()
        
        for doc in docs:
            data = doc.to_dict()
            
            # Get full content
            if data.get("storage_type") == "firestore":
                content = data.get("content", "")
            else:
                content = self.storage.get_message_content(data["id"])
            
            messages.append({
                "role": data["role"],
                "content": content,
                "timestamp": data["timestamp"],
                "attachments": data.get("metadata", {}).get("attachments", [])
            })
        
        return messages
