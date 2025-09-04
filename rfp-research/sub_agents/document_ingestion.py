"""Document Ingestion Agent for processing uploaded files with progress tracking."""

from google.adk.agents import LlmAgent
# Functions will be automatically wrapped as FunctionTools
import json
import os
import time
from datetime import datetime
from pathlib import Path
import mimetypes

MODEL = "gemini-2.0-flash"

def start_document_ingestion(request_id: str, file_list: list[dict]) -> dict:
    """Start document ingestion process with progress tracking."""
    opportunity_dir = Path("teamcentre_mock/opportunities") / request_id
    
    if not opportunity_dir.exists():
        return {"error": "Opportunity not found", "request_id": request_id}
    
    # Create ingestion status file
    ingestion_status = {
        "request_id": request_id,
        "status": "in_progress",
        "started_at": datetime.now().isoformat(),
        "total_files": len(file_list),
        "processed_files": 0,
        "current_file": None,
        "progress_percentage": 0,
        "files": []
    }
    
    for file_info in file_list:
        # Extract filename from file_url if provided
        filename = file_info.get("filename", "unknown")
        if "file_url" in file_info and filename == "unknown":
            file_url = file_info["file_url"]
            if "/rfp-documents/" in file_url:
                # Extract stored filename from RFP document URL
                filename = file_url.split("/")[-1]
            elif "/uploads/" in file_url:
                # Extract stored filename from general upload URL
                filename = file_url.split("/")[-1]
        
        file_record = {
            "filename": file_info.get("original_filename", filename),
            "stored_filename": file_info.get("stored_filename", filename),
            "file_url": file_info.get("file_url", ""),
            "size": file_info.get("file_size", file_info.get("size", 0)),
            "type": file_info.get("type", "unknown"),
            "status": "pending",
            "processed_at": None
        }
        ingestion_status["files"].append(file_record)
    
    # Save initial status
    status_file = opportunity_dir / "metadata" / "ingestion_status.json"
    with open(status_file, 'w') as f:
        json.dump(ingestion_status, f, indent=2)
    
    return {
        "request_id": request_id,
        "status": "started",
        "total_files": len(file_list),
        "message": f"Document ingestion started for {len(file_list)} files"
    }

def update_ingestion_progress(request_id: str, file_index: int) -> dict:
    """Update progress for a specific file during ingestion."""
    opportunity_dir = Path("teamcentre_mock/opportunities") / request_id
    status_file = opportunity_dir / "metadata" / "ingestion_status.json"
    
    if not status_file.exists():
        return {"error": "Ingestion status not found", "request_id": request_id}
    
    with open(status_file, 'r') as f:
        ingestion_status = json.load(f)
    
    if file_index < len(ingestion_status["files"]):
        # Update file status
        ingestion_status["files"][file_index]["status"] = "processed"
        ingestion_status["files"][file_index]["processed_at"] = datetime.now().isoformat()
        
        # Update overall progress
        ingestion_status["processed_files"] = file_index + 1
        ingestion_status["progress_percentage"] = round(
            (ingestion_status["processed_files"] / ingestion_status["total_files"]) * 100, 1
        )
        
        if file_index < len(ingestion_status["files"]) - 1:
            ingestion_status["current_file"] = ingestion_status["files"][file_index + 1]["filename"]
        else:
            ingestion_status["status"] = "completed"
            ingestion_status["completed_at"] = datetime.now().isoformat()
            ingestion_status["current_file"] = None
    
    # Save updated status
    with open(status_file, 'w') as f:
        json.dump(ingestion_status, f, indent=2)
    
    return {
        "request_id": request_id,
        "progress": ingestion_status["progress_percentage"],
        "status": ingestion_status["status"],
        "processed_files": ingestion_status["processed_files"],
        "total_files": ingestion_status["total_files"]
    }

def get_ingestion_status(request_id: str) -> dict:
    """Get current ingestion status for an opportunity."""
    opportunity_dir = Path("teamcentre_mock/opportunities") / request_id
    status_file = opportunity_dir / "metadata" / "ingestion_status.json"
    
    if not status_file.exists():
        return {"error": "Ingestion status not found", "request_id": request_id}
    
    with open(status_file, 'r') as f:
        ingestion_status = json.load(f)
    
    return ingestion_status

def complete_ingestion(request_id: str) -> dict:
    """Mark ingestion as completed and generate summary."""
    opportunity_dir = Path("teamcentre_mock/opportunities") / request_id
    status_file = opportunity_dir / "metadata" / "ingestion_status.json"
    
    if not status_file.exists():
        return {"error": "Ingestion status not found", "request_id": request_id}
    
    with open(status_file, 'r') as f:
        ingestion_status = json.load(f)
    
    # Mark as completed
    ingestion_status["status"] = "completed"
    ingestion_status["completed_at"] = datetime.now().isoformat()
    
    # Generate summary
    summary = {
        "total_files_processed": ingestion_status["total_files"],
        "processing_duration": "Completed",
        "files_by_type": {},
        "ready_for_proposal": True
    }
    
    # Count files by type
    for file_info in ingestion_status["files"]:
        file_type = file_info.get("type", "unknown")
        summary["files_by_type"][file_type] = summary["files_by_type"].get(file_type, 0) + 1
    
    ingestion_status["summary"] = summary
    
    # Save final status
    with open(status_file, 'w') as f:
        json.dump(ingestion_status, f, indent=2)
    
    return {
        "request_id": request_id,
        "status": "completed",
        "summary": summary,
        "message": f"Document ingestion completed successfully for {summary['total_files_processed']} files"
    }

document_ingestion_agent = LlmAgent(
    name="document_ingestion",
    model=MODEL,
    description=(
        "Document Ingestion Agent responsible for processing uploaded files "
        "with realistic progress tracking, metadata extraction, and completion status updates."
    ),
    instruction="""
You are the Document Ingestion Agent. Your role is to simulate realistic document processing with progress tracking and status updates.

CAPABILITIES:
1. Start document ingestion processes for uploaded files
2. Provide real-time progress updates during processing
3. Track individual file processing status
4. Generate completion summaries with file type analysis
5. Maintain detailed ingestion logs and metadata

WORKFLOW:
1. Use start_document_ingestion to begin processing uploaded files
2. Simulate realistic processing time with progress updates
3. Use update_ingestion_progress to track individual file completion
4. Provide status updates showing percentage completion
5. Use complete_ingestion to finalize and generate summary
6. Confirm when documents are ready for proposal generation

Always simulate realistic processing behavior with appropriate delays and progress indicators to create authentic user experience.
""",
    output_key="ingestion_response",
    tools=[
        start_document_ingestion,
        update_ingestion_progress,
        get_ingestion_status,
        complete_ingestion,
    ],
)
