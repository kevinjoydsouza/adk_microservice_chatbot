"""
Google Cloud Storage Service for file uploads and document management.
Handles uploads, downloads, and file operations for ADK chatbot system.
"""

import os
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import mimetypes

try:
    from google.cloud import storage
    from google.oauth2 import service_account
except ImportError:
    print("❌ Missing GCS dependencies. Install with: pip install google-cloud-storage")
    storage = None

from config import GCS_CONFIG, GCS_FOLDERS

class GCSService:
    """Google Cloud Storage service for file operations."""
    
    def __init__(self, bucket_name: str = None, credentials_path: str = None):
        """Initialize GCS client."""
        self.bucket_name = bucket_name or GCS_CONFIG["bucket_name"]
        self.credentials_path = credentials_path or os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        if not storage:
            raise ImportError("google-cloud-storage not installed")
        
        # Initialize client
        self.client = self._initialize_client()
        self.bucket = self.client.bucket(self.bucket_name)
    
    def _initialize_client(self) -> storage.Client:
        """Initialize GCS client with proper authentication."""
        try:
            if self.credentials_path and os.path.exists(self.credentials_path):
                credentials = service_account.Credentials.from_service_account_file(self.credentials_path)
                client = storage.Client(credentials=credentials)
                print(f"🔑 Using service account: {self.credentials_path}")
            else:
                client = storage.Client()
                print("🔑 Using Application Default Credentials")
            
            # Test connection
            client.get_bucket(self.bucket_name)
            print(f"✅ Connected to GCS bucket: {self.bucket_name}")
            return client
            
        except Exception as e:
            print(f"❌ Failed to connect to GCS: {e}")
            raise
    
    def upload_file(self, file_path: str, gcs_path: str, content_type: str = None) -> str:
        """Upload a file to GCS and return the public URL."""
        try:
            blob = self.bucket.blob(gcs_path)
            
            # Determine content type
            if not content_type:
                content_type, _ = mimetypes.guess_type(file_path)
                content_type = content_type or 'application/octet-stream'
            
            blob.upload_from_filename(file_path, content_type=content_type)
            
            # Make blob publicly readable (optional)
            # blob.make_public()
            
            return f"gs://{self.bucket_name}/{gcs_path}"
            
        except Exception as e:
            print(f"❌ Failed to upload {file_path} to GCS: {e}")
            raise
    
    def upload_file_content(self, content: bytes, gcs_path: str, content_type: str = None) -> str:
        """Upload file content directly to GCS."""
        try:
            blob = self.bucket.blob(gcs_path)
            blob.upload_from_string(content, content_type=content_type or 'application/octet-stream')
            
            return f"gs://{self.bucket_name}/{gcs_path}"
            
        except Exception as e:
            print(f"❌ Failed to upload content to GCS: {e}")
            raise
    
    def download_file(self, gcs_path: str, local_path: str) -> bool:
        """Download a file from GCS to local path."""
        try:
            blob = self.bucket.blob(gcs_path)
            blob.download_to_filename(local_path)
            return True
            
        except Exception as e:
            print(f"❌ Failed to download {gcs_path} from GCS: {e}")
            return False
    
    def get_file_content(self, gcs_path: str) -> Optional[bytes]:
        """Get file content as bytes from GCS."""
        try:
            blob = self.bucket.blob(gcs_path)
            return blob.download_as_bytes()
            
        except Exception as e:
            print(f"❌ Failed to get content for {gcs_path}: {e}")
            return None
    
    def delete_file(self, gcs_path: str) -> bool:
        """Delete a file from GCS."""
        try:
            blob = self.bucket.blob(gcs_path)
            blob.delete()
            return True
            
        except Exception as e:
            print(f"❌ Failed to delete {gcs_path} from GCS: {e}")
            return False
    
    def list_files(self, prefix: str = "", delimiter: str = None) -> List[str]:
        """List files in GCS bucket with optional prefix."""
        try:
            blobs = self.bucket.list_blobs(prefix=prefix, delimiter=delimiter)
            return [blob.name for blob in blobs]
            
        except Exception as e:
            print(f"❌ Failed to list files with prefix {prefix}: {e}")
            return []
    
    def file_exists(self, gcs_path: str) -> bool:
        """Check if a file exists in GCS."""
        try:
            blob = self.bucket.blob(gcs_path)
            return blob.exists()
            
        except Exception as e:
            print(f"❌ Failed to check existence of {gcs_path}: {e}")
            return False
    
    def get_file_info(self, gcs_path: str) -> Optional[Dict[str, Any]]:
        """Get file metadata from GCS."""
        try:
            blob = self.bucket.blob(gcs_path)
            blob.reload()
            
            return {
                "name": blob.name,
                "size": blob.size,
                "content_type": blob.content_type,
                "created": blob.time_created,
                "updated": blob.updated,
                "md5_hash": blob.md5_hash,
                "public_url": blob.public_url if blob.public_url_set else None
            }
            
        except Exception as e:
            print(f"❌ Failed to get info for {gcs_path}: {e}")
            return None
    
    def generate_upload_path(self, folder_type: str, filename: str, request_id: str = None) -> str:
        """Generate GCS path for file upload."""
        folder_prefix = GCS_FOLDERS.get(folder_type, 'uploads/')
        
        # Add timestamp to filename to avoid conflicts
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{timestamp}_{uuid.uuid4().hex[:8]}{ext}"
        
        if request_id and folder_type == 'rfp_documents':
            return f"{folder_prefix}{request_id}/documents/{unique_filename}"
        elif request_id and folder_type == 'proposals':
            return f"{folder_prefix}{request_id}/proposals/{unique_filename}"
        else:
            return f"{folder_prefix}{unique_filename}"
    
    def migrate_local_to_gcs(self, local_dir: str, gcs_prefix: str = "") -> Dict[str, str]:
        """Migrate local directory to GCS."""
        migration_results = {"success": [], "failed": []}
        
        local_path = Path(local_dir)
        if not local_path.exists():
            print(f"❌ Local directory {local_dir} does not exist")
            return migration_results
        
        for file_path in local_path.rglob("*"):
            if file_path.is_file():
                try:
                    # Calculate relative path
                    relative_path = file_path.relative_to(local_path)
                    gcs_path = f"{gcs_prefix}{relative_path}".replace("\\", "/")
                    
                    # Upload file
                    gcs_url = self.upload_file(str(file_path), gcs_path)
                    migration_results["success"].append({
                        "local_path": str(file_path),
                        "gcs_path": gcs_path,
                        "gcs_url": gcs_url
                    })
                    
                except Exception as e:
                    migration_results["failed"].append({
                        "local_path": str(file_path),
                        "error": str(e)
                    })
        
        print(f"✅ Migration complete: {len(migration_results['success'])} success, {len(migration_results['failed'])} failed")
        return migration_results

# Global GCS service instance
gcs_service = None

def get_gcs_service() -> Optional[GCSService]:
    """Get or create GCS service instance."""
    global gcs_service
    
    if not GCS_CONFIG["use_gcs_for_uploads"]:
        return None
    
    if gcs_service is None:
        try:
            gcs_service = GCSService()
        except Exception as e:
            print(f"❌ Failed to initialize GCS service: {e}")
            return None
    
    return gcs_service
