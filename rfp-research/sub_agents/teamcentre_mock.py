"""TeamCentre Mock Agent for opportunity creation and file management."""

from google.adk.agents import LlmAgent
# Functions will be automatically wrapped as FunctionTools
import json
import os
import uuid
from datetime import datetime
from pathlib import Path

MODEL = "gemini-2.0-flash"

def create_opportunity(project_details: dict) -> dict:
    """Create opportunity in mock TeamCentre with local folder structure."""
    request_id = f"RFP_{uuid.uuid4().hex[:8].upper()}"
    
    # Create base directory structure
    base_dir = Path("teamcentre_mock/opportunities")
    opportunity_dir = base_dir / request_id
    
    # Create folder structure
    folders = [
        "documents/uploaded",
        "documents/processed", 
        "documents/generated",
        "metadata",
        "proposals"
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
    metadata_file = opportunity_dir / "metadata" / "opportunity.json"
    with open(metadata_file, 'w') as f:
        json.dump(opportunity_data, f, indent=2)
    
    return {
        "request_id": request_id,
        "status": "created",
        "folder_path": str(opportunity_dir),
        "message": f"Opportunity created successfully with Request ID: {request_id}"
    }

def store_uploaded_files(request_id: str, file_info: list[dict]) -> dict:
    """Store uploaded files in the opportunity folder."""
    opportunity_dir = Path("teamcentre_mock/opportunities") / request_id
    
    if not opportunity_dir.exists():
        return {"error": "Opportunity not found", "request_id": request_id}
    
    stored_files = []
    upload_dir = opportunity_dir / "documents" / "uploaded"
    
    for file_data in file_info:
        # In real implementation, files would be moved here
        # For mock, we'll just record the file information
        file_record = {
            "filename": file_data.get("filename"),
            "original_path": file_data.get("path"),
            "size": file_data.get("size"),
            "type": file_data.get("type"),
            "uploaded_at": datetime.now().isoformat()
        }
        stored_files.append(file_record)
    
    # Update opportunity metadata
    metadata_file = opportunity_dir / "metadata" / "opportunity.json"
    with open(metadata_file, 'r') as f:
        opportunity_data = json.load(f)
    
    opportunity_data["files_uploaded"].extend(stored_files)
    opportunity_data["processing_status"] = "files_uploaded"
    opportunity_data["updated_at"] = datetime.now().isoformat()
    
    with open(metadata_file, 'w') as f:
        json.dump(opportunity_data, f, indent=2)
    
    return {
        "request_id": request_id,
        "files_stored": len(stored_files),
        "status": "files_uploaded",
        "message": f"Successfully stored {len(stored_files)} files for opportunity {request_id}"
    }

def get_opportunity_status(request_id: str) -> dict:
    """Get current status of an opportunity."""
    opportunity_dir = Path("teamcentre_mock/opportunities") / request_id
    metadata_file = opportunity_dir / "metadata" / "opportunity.json"
    
    if not metadata_file.exists():
        return {"error": "Opportunity not found", "request_id": request_id}
    
    with open(metadata_file, 'r') as f:
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
