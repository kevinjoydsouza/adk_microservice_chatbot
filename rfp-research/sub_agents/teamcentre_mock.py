"""TeamCentre Mock Agent for opportunity creation and file management."""

from google.adk.agents import LlmAgent
# Functions will be automatically wrapped as FunctionTools
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from services.gcs_service import get_gcs_service

MODEL = "gemini-2.0-flash"

def create_opportunity(project_details: Dict[str, Any]) -> Dict[str, Any]:
    """Create opportunity in mock TeamCentre with GCS or local folder structure."""
    request_id = f"RFP_{uuid.uuid4().hex[:8].upper()}"
    gcs_service = get_gcs_service()
    
    if gcs_service:
        # Create GCS folder structure by uploading placeholder files
        folders = [
            f"teamcentre_mock/opportunities/{request_id}/documents/uploaded/.placeholder",
            f"teamcentre_mock/opportunities/{request_id}/documents/processed/.placeholder",
            f"teamcentre_mock/opportunities/{request_id}/metadata/.placeholder",
            f"teamcentre_mock/opportunities/{request_id}/proposals/.placeholder",
            f"teamcentre_mock/opportunities/{request_id}/analysis/.placeholder"
        ]
        
        for folder_path in folders:
            try:
                gcs_service.upload_file_content(b"# Placeholder file for folder structure", folder_path, "text/plain")
            except Exception as e:
                print(f"Warning: Failed to create GCS folder {folder_path}: {e}")
    else:
        # Create local directory structure
        base_dir = Path("teamcentre_mock/opportunities")
        opportunity_dir = base_dir / request_id
        
        folders = [
            "documents/uploaded",
            "documents/processed",
            "metadata",
            "proposals",
            "analysis"
        ]
        
        for folder in folders:
            (opportunity_dir / folder).mkdir(parents=True, exist_ok=True)
    
    # Create opportunity metadata
    opportunity_data = {
        "request_id": request_id,
        "project_details": project_details,
        "created_at": datetime.now().isoformat(),
        "status": "created",
        "folder_structure": folders,
        "files_uploaded": [],
        "processing_status": "pending"
    }
    
    # Save metadata
    if gcs_service:
        metadata_path = f"teamcentre_mock/opportunities/{request_id}/metadata/opportunity.json"
        metadata_content = json.dumps(opportunity_data, indent=2).encode('utf-8')
        gcs_service.upload_file_content(metadata_content, metadata_path, "application/json")
    else:
        metadata_file = opportunity_dir / "metadata" / "opportunity.json"
        with open(metadata_file, 'w') as f:
            json.dump(opportunity_data, f, indent=2)
    
    return {
        "request_id": request_id,
        "status": "created",
        "folder_path": str(opportunity_dir) if not gcs_service else f"gs://teamcentre_mock/opportunities/{request_id}",
        "message": f"Opportunity created successfully with Request ID: {request_id}"
    }

def store_uploaded_files(request_id: str, file_info: list[dict]) -> dict:
    """Store uploaded files metadata in the opportunity folder (GCS or local)."""
    gcs_service = get_gcs_service()
    
    if gcs_service:
        # Check if opportunity exists in GCS by looking for metadata placeholder
        metadata_path = f"teamcentre_mock/opportunities/{request_id}/metadata/.placeholder"
        if not gcs_service.file_exists(metadata_path):
            return {"error": "Opportunity not found", "request_id": request_id}
    else:
        # Local storage check
        opportunity_dir = Path("teamcentre_mock/opportunities") / request_id
        if not opportunity_dir.exists():
            return {"error": "Opportunity not found", "request_id": request_id}
    
    uploaded_files = []
    
    for file_data in file_info:
        try:
            filename = file_data.get("filename")
            file_url = file_data.get("file_url")
            file_size = file_data.get("file_size", 0)
            
            # Store file metadata
            file_metadata = {
                "filename": filename,
                "file_url": file_url,
                "file_size": file_size,
                "upload_time": datetime.now().isoformat(),
                "status": "uploaded",
                "request_id": request_id,
                "storage_type": "gcs" if gcs_service else "local"
            }
            
            uploaded_files.append(file_metadata)
            
        except Exception as e:
            return {"error": f"Failed to store file {filename}: {str(e)}", "request_id": request_id}
    
    # Save file registry
    registry_data = {
        "request_id": request_id,
        "uploaded_files": uploaded_files,
        "total_files": len(uploaded_files),
        "last_updated": datetime.now().isoformat()
    }
    
    if gcs_service:
        # Store registry in GCS
        registry_path = f"teamcentre_mock/opportunities/{request_id}/metadata/file_registry.json"
        registry_content = json.dumps(registry_data, indent=2).encode('utf-8')
        gcs_service.upload_file_content(registry_content, registry_path, "application/json")
    else:
        # Store registry locally
        opportunity_dir = Path("teamcentre_mock/opportunities") / request_id
        registry_file = opportunity_dir / "metadata" / "file_registry.json"
        with open(registry_file, "w") as f:
            json.dump(registry_data, f, indent=2)
    
    return {
        "request_id": request_id,
        "uploaded_files": uploaded_files,
        "total_files": len(uploaded_files),
        "status": "success"
    }

def get_opportunity_status(request_id: str) -> dict:
    """Get current status of an opportunity from GCS or local storage."""
    gcs_service = get_gcs_service()
    
    if gcs_service:
        # Get from GCS
        metadata_path = f"teamcentre_mock/opportunities/{request_id}/metadata/opportunity.json"
        try:
            content = gcs_service.get_file_content(metadata_path)
            if content:
                opportunity_data = json.loads(content.decode('utf-8'))
                return opportunity_data
            else:
                return {"error": "Opportunity not found", "request_id": request_id}
        except Exception as e:
            return {"error": f"Failed to retrieve opportunity: {str(e)}", "request_id": request_id}
    else:
        # Get from local storage
        opportunity_dir = Path("teamcentre_mock/opportunities") / request_id
        metadata_file = opportunity_dir / "metadata" / "opportunity.json"
        
        if not metadata_file.exists():
            return {"error": "Opportunity not found", "request_id": request_id}
        
        with open(metadata_file, "r") as f:
            opportunity_data = json.load(f)
        
        return opportunity_data

teamcentre_mock_agent = LlmAgent(
    name="teamcentre_mock",
    model=MODEL,
    description=(
        "TeamCentre Mock Agent responsible for creating opportunities, "
        "managing file storage, and maintaining opportunity metadata "
        "in a local folder structure that simulates enterprise TeamCentre functionality."
    ),
    instruction="""
You are the TeamCentre Mock Agent. Your role is to simulate enterprise TeamCentre functionality for RFP opportunity management.

CAPABILITIES:
1. Create new opportunities with unique request IDs
2. Set up organized folder structures for each opportunity
3. Store and manage uploaded files
4. Maintain comprehensive metadata for tracking
5. Provide status updates and confirmations

WORKFLOW:
1. When creating opportunities, use create_opportunity function with project details
2. Generate unique request IDs in format RFP_XXXXXXXX
3. Create folder structure: documents/{uploaded,processed,generated}, metadata, proposals
4. Store opportunity metadata as JSON files
5. Provide clear confirmation messages with request IDs

Always simulate realistic enterprise behavior with proper folder organization and metadata tracking.
""",
    output_key="teamcentre_response",
    tools=[
        create_opportunity,
        store_uploaded_files,
        get_opportunity_status,
    ],
)
