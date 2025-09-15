from fastapi import FastAPI, HTTPException, Depends, Query, Header, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.staticfiles import StaticFiles
from typing import List, Optional
from datetime import datetime
import os
import uuid
import shutil
import base64
import mimetypes
from PIL import Image
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from models import *
from production_storage import SimpleMessageService
from services.adk_service import ADKService
from services.auth_service import AuthService
from services.gcs_service import get_gcs_service
from middleware.error_handler import validation_exception_handler, http_exception_handler, general_exception_handler
from config import VERTEX_AI_CONFIG, PRODUCTION_STORAGE

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="IntelliSurf RFP Research Backend",
    description="FastAPI backend for RFP Research Agent and conversation management",
    version="1.0.0"
)

# Add exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Services
message_service = SimpleMessageService(
    project_id=VERTEX_AI_CONFIG.get("project_id"),
    bucket_name=PRODUCTION_STORAGE.get("bucket_name")
)
auth_service = AuthService()
rfp_adk_service = ADKService(app_name="rfp-research")

# Mount static files for uploads (only if not using GCS)
from config import GCS_CONFIG
if not GCS_CONFIG["use_gcs_for_uploads"]:
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
    # Mount static files for RFP documents
    app.mount("/rfp-documents", StaticFiles(directory="teamcentre_mock/opportunities"), name="rfp_documents")

# Upload directory
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate JWT token and return user info - Mock for development"""
    # For development without Firebase - return mock user
    return {
        "uid": "dev-user-123",
        "email": "dev@example.com", 
        "name": "Development User",
        "provider": "mock"
    }

@app.get("/")
async def root():
    return {"message": "IntelliSurf RFP Research Backend is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat(), "version": "1.0.0"}

# Conversation endpoints
@app.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    request: CreateConversationRequest,
    user = Depends(get_current_user)
):
    """Create a new conversation"""
    try:
        conversation_id = f"conv_{uuid.uuid4().hex[:12]}"
        conversation = message_service.create_conversation(
            conversation_id=conversation_id,
            user_id=user["uid"],
            title=request.title
        )
        return conversation
    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    user = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get user's conversations with pagination"""
    try:
        conversations = message_service.get_user_conversations(user["uid"], limit, offset)
        return conversations
    except Exception as e:
        logger.error(f"Error fetching conversations: {str(e)}")
        return []

@app.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    user = Depends(get_current_user)
):
    """Get a specific conversation with all messages"""
    messages = message_service.get_conversation_messages(conversation_id)
    
    return {
        "id": conversation_id,
        "title": f"Conversation {conversation_id[:8]}",
        "messages": messages,
        "created_at": datetime.utcnow().isoformat()
    }

@app.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def add_message(
    conversation_id: str,
    request: AddMessageRequest,
    user = Depends(get_current_user)
):
    """Add a message to a conversation"""
    message_id = message_service.add_message_to_conversation(
        conversation_id=conversation_id,
        role=request.role,
        content=request.content
    )
    
    return {
        "id": message_id,
        "conversation_id": conversation_id,
        "role": request.role,
        "content": request.content,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.put("/conversations/{conversation_id}/title")
async def update_conversation_title(
    conversation_id: str,
    title: str,
    user = Depends(get_current_user)
):
    """Update conversation title"""
    try:
        success = message_service.update_conversation_title(conversation_id, title)
        if success:
            return {"message": "Title updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Conversation not found")
    except Exception as e:
        logger.error(f"Error updating conversation title: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user = Depends(get_current_user)
):
    """Delete a conversation"""
    # For now, return success - implement deletion in message_service if needed
    return {"message": "Conversation deleted successfully"}

@app.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: str,
    user = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100),
    before_timestamp: Optional[str] = Query(None)
):
    """Get messages from a conversation with pagination"""
    messages = message_service.get_conversation_messages(conversation_id)
    return messages[:limit] if messages else []


@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    user = Depends(get_current_user),
    request_id: Optional[str] = Query(None, description="RFP Request ID for RFP-specific uploads")
):
    """Upload a file and return its URL. Uses GCS if configured, otherwise local storage."""
    try:
        gcs_service = get_gcs_service()
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{timestamp}_{file.filename}"
        
        # Read file content
        content = await file.read()
        
        if gcs_service:
            # Upload to GCS
            if request_id and request_id.startswith("RFP_"):
                gcs_path = gcs_service.generate_upload_path('rfp_documents', unique_filename, request_id)
            else:
                gcs_path = gcs_service.generate_upload_path('uploads', unique_filename)
            
            file_url = gcs_service.upload_file_content(content, gcs_path, file.content_type)
            
        else:
            # Local storage fallback
            if request_id and request_id.startswith("RFP_"):
                # RFP-specific upload
                rfp_documents_dir = f"teamcentre_mock/opportunities/{request_id}/documents"
                os.makedirs(rfp_documents_dir, exist_ok=True)
                file_path = os.path.join(rfp_documents_dir, unique_filename)
                file_url = f"/rfp-documents/{request_id}/documents/{unique_filename}"
            else:
                # General upload
                file_path = os.path.join(UPLOAD_DIR, unique_filename)
                file_url = f"/uploads/{unique_filename}"
            
            # Save file locally
            with open(file_path, "wb") as buffer:
                buffer.write(content)
        
        return {
            "filename": file.filename,
            "file_url": file_url,
            "file_size": len(content),
            "upload_time": datetime.now().isoformat(),
            "storage_type": "gcs" if gcs_service else "local"
        }
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/rfp-chat")
async def rfp_chat_endpoint(
    request: dict,
    user = Depends(get_current_user)
):
    """Chat with RFP Research Agent for opportunity management and proposal generation"""
    try:
        user_input = request.get("user_input")
        session_id = request.get("session_id")
        conversation_id = request.get("conversation_id")
        streaming = request.get("streaming", False)
        attachments = request.get("attachments", [])
        
        if not user_input:
            raise HTTPException(status_code=400, detail="user_input is required")
        
        user_id = user["uid"]
        
        # Initialize activity tracking
        activity_tracker = {
            "current_step": "initializing",
            "steps": [
                {"name": "Initializing", "status": "in_progress", "description": "Setting up RFP session"},
                {"name": "RFP Coordinator", "status": "pending", "description": "Collecting project details"},
                {"name": "TeamCentre Mock", "status": "pending", "description": "Creating opportunity structure"},
                {"name": "Document Ingestion", "status": "pending", "description": "Processing uploaded files"},
                {"name": "Proposal Generator", "status": "pending", "description": "Generating final proposal"}
            ],
            "progress_percentage": 10,
            "message": "Initializing RFP Research Agent session..."
        }
        
        # If streaming is enabled, return SSE response
        if streaming:
            return StreamingResponse(
                stream_rfp_response(user_id, session_id, conversation_id, user_input, attachments, activity_tracker),
                media_type="text/plain"
            )
        
        # Get or create RFP ADK session
        activity_tracker["current_step"] = "session_setup"
        activity_tracker["steps"][0]["status"] = "completed"
        activity_tracker["steps"][1]["status"] = "in_progress"
        activity_tracker["progress_percentage"] = 20
        activity_tracker["message"] = "Setting up agent session and analyzing request..."
        
        session_id, session_data = await rfp_adk_service.get_or_create_session(
            user_id=user_id,
            session_id=session_id
        )
        
        # Create Firestore conversation if not provided
        if not conversation_id:
            title_words = user_input.split()[:4]
            title = " ".join(title_words) + ("..." if len(user_input.split()) > 4 else "")
            
            conversation_id = f"rfp_{uuid.uuid4().hex[:12]}"
            message_service.create_conversation(conversation_id, user["uid"], title)
        
        # Add user message
        message_service.add_message_to_conversation(
            conversation_id=conversation_id,
            role="user",
            content=user_input
        )
        
        # Update activity: Processing attachments
        if attachments:
            activity_tracker["current_step"] = "processing_attachments"
            activity_tracker["progress_percentage"] = 30
            activity_tracker["message"] = f"Processing {len(attachments)} uploaded files..."
        
        # Process attachments for RFP context
        processed_attachments = []
        if attachments:
            # Try to get current request_id from session or extract from conversation
            current_request_id = None
            try:
                session_data = await rfp_adk_service.get_session(user_id, session_id)
                if session_data and "request_id" in session_data:
                    current_request_id = session_data["request_id"]
            except:
                pass
            
            # Process each attachment with RFP context
            for attachment_url in attachments:
                try:
                    # Convert general upload URLs to RFP-specific paths if needed
                    if "/uploads/" in attachment_url and current_request_id:
                        # Move file from general uploads to RFP-specific location
                        general_filename = attachment_url.split("/")[-1]
                        general_path = f"uploads/{general_filename}"
                        
                        if os.path.exists(general_path):
                            # Create RFP documents directory
                            rfp_documents_dir = f"teamcentre_mock/opportunities/{current_request_id}/documents"
                            os.makedirs(rfp_documents_dir, exist_ok=True)
                            
                            # Move file to RFP location
                            rfp_path = f"{rfp_documents_dir}/{general_filename}"
                            shutil.move(general_path, rfp_path)
                            
                            # Update attachment URL
                            attachment_url = f"/rfp-documents/{current_request_id}/{general_filename}"
                    
                    processed_attachments.append(attachment_url)
                except Exception as e:
                    logger.error(f"Error processing RFP attachment {attachment_url}: {str(e)}")
                    processed_attachments.append(attachment_url)

        # Update activity: Running RFP agent
        activity_tracker["current_step"] = "agent_processing"
        activity_tracker["progress_percentage"] = 50
        activity_tracker["message"] = "RFP Research Agent analyzing request and determining workflow..."

        # Process with RFP agent
        try:
            events = await rfp_adk_service.run_agent(user_id, session_id, user_input, processed_attachments)
            
            # Analyze events to determine which sub-agents were called
            agent_activities = analyze_agent_events(events)
            
            # Update activity tracker based on agent activities
            for activity in agent_activities:
                if "rfp_coordinator" in activity.lower():
                    activity_tracker["steps"][1]["status"] = "completed"
                    activity_tracker["steps"][2]["status"] = "in_progress"
                    activity_tracker["progress_percentage"] = 60
                    activity_tracker["message"] = "RFP Coordinator collecting project details..."
                elif "teamcentre" in activity.lower():
                    activity_tracker["steps"][2]["status"] = "completed"
                    activity_tracker["steps"][3]["status"] = "in_progress"
                    activity_tracker["progress_percentage"] = 70
                    activity_tracker["message"] = "Creating opportunity structure in TeamCentre..."
                elif "document_ingestion" in activity.lower():
                    activity_tracker["steps"][3]["status"] = "completed"
                    activity_tracker["steps"][4]["status"] = "in_progress"
                    activity_tracker["progress_percentage"] = 85
                    activity_tracker["message"] = "Processing and ingesting uploaded documents..."
                elif "proposal_generator" in activity.lower():
                    activity_tracker["steps"][4]["status"] = "completed"
                    activity_tracker["progress_percentage"] = 95
                    activity_tracker["message"] = "Generating comprehensive proposal document..."
            
            response_text = rfp_adk_service.extract_response_text(events)
            
            # Final activity update
            activity_tracker["current_step"] = "completed"
            activity_tracker["progress_percentage"] = 100
            activity_tracker["message"] = "RFP Research Agent processing completed successfully!"
            
            # Save assistant response
            message_service.add_message_to_conversation(
                conversation_id=conversation_id,
                role="assistant",
                content=response_text
            )
            
            return {
                "response": response_text,
                "session_id": session_id,
                "conversation_id": conversation_id,
                "agent_type": "rfp_research",
                "activity_tracker": activity_tracker
            }
        except Exception as rfp_error:
            logger.error(f"RFP agent error: {str(rfp_error)}")
            error_message = f"RFP Agent Error: {str(rfp_error)}"
            
            # Update activity tracker for error
            activity_tracker["current_step"] = "error"
            activity_tracker["message"] = f"Error occurred: {str(rfp_error)}"
            
            message_service.add_message_to_conversation(
                conversation_id=conversation_id,
                role="assistant",
                content=error_message
            )
            
            return {
                "response": error_message,
                "session_id": session_id,
                "conversation_id": conversation_id,
                "error": True,
                "activity_tracker": activity_tracker
            }
            
    except Exception as e:
        logger.error(f"RFP Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def stream_rfp_response(user_id: str, session_id: str, conversation_id: str, user_input: str, attachments: list, activity_tracker: dict):
    """Stream RFP response with real-time events from ADK only."""
    try:
        response_text = ""
        
        try:
            # Stream directly from ADK without any hardcoded steps
            async for event in rfp_adk_service.run_agent_streaming(user_id, session_id, user_input, True, attachments):
                
                # Process real ADK events and extract meaningful information
                if isinstance(event, dict):
                    # Look for content that indicates agent activity
                    if "content" in event:
                        content = event["content"]
                        if isinstance(content, dict) and content.get("role") == "model":
                            parts = content.get("parts", [])
                            for part in parts:
                                if isinstance(part, dict) and "text" in part:
                                    text_chunk = part["text"]
                                    if text_chunk.strip():
                                        response_text += text_chunk
                                        # Send real content as thinking step
                                        yield f"data: {json.dumps({'type': 'thinking', 'step': f'Agent: {text_chunk[:50]}...', 'progress': 50})}\n\n"
                    
                    # Handle tool usage events
                    elif "tool_call" in event or "function_call" in event:
                        tool_name = event.get("tool_call", {}).get("name", "research tool")
                        yield f"data: {json.dumps({'type': 'thinking', 'step': f'Using {tool_name}', 'progress': 60})}\n\n"
                    
                    # Handle agent state changes
                    elif "agent_state" in event:
                        state = event.get("agent_state", "")
                        yield f"data: {json.dumps({'type': 'thinking', 'step': f'Agent state: {state}', 'progress': 70})}\n\n"
                    
                    # Handle any other meaningful events
                    elif "message" in event:
                        message = str(event["message"])[:100]
                        yield f"data: {json.dumps({'type': 'thinking', 'step': message, 'progress': 80})}\n\n"
                    
                    # Handle error events
                    elif "error" in event:
                        error_msg = str(event["error"])
                        yield f"data: {json.dumps({'type': 'thinking', 'step': f'Handling: {error_msg}', 'progress': 40})}\n\n"
            
            # If no response from streaming, fallback to regular call
            if not response_text.strip():
                events = await rfp_adk_service.run_agent(user_id, session_id, user_input, attachments)
                response_text = rfp_adk_service.extract_response_text(events)
        
        except Exception as e:
            logger.error(f"ADK streaming failed: {e}")
            # Fallback to non-streaming
            events = await rfp_adk_service.run_agent(user_id, session_id, user_input, attachments)
            response_text = rfp_adk_service.extract_response_text(events)
        
        # Update activity tracker
        activity_tracker["status"] = "completed"
        activity_tracker["response"] = response_text
        
        # Store conversation
        if conversation_id:
            conversation_data = {
                "id": conversation_id,
                "user_input": user_input,
                "response": response_text,
                "timestamp": datetime.now().isoformat(),
                "attachments": attachments or []
            }
            await firestore_service.store_conversation(user_id, conversation_id, conversation_data)
        
        # Send final response
        yield f"data: {json.dumps({'type': 'response', 'content': response_text, 'session_id': session_id, 'conversation_id': conversation_id})}\n\n"
        
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        error_message = f"I encountered an error while processing your request: {str(e)}"
        yield f"data: {json.dumps({'type': 'error', 'message': error_message})}\n\n"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=True
    )