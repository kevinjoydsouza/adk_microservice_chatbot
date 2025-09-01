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
import google.generativeai as genai
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from models import *
from production_storage import SimpleMessageService
from services.auth_service import AuthService
from services.adk_service import ADKService
from middleware.error_handler import validation_exception_handler, http_exception_handler, general_exception_handler
from config import VERTEX_AI_CONFIG, PRODUCTION_STORAGE

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Gemini Chatbot Backend",
    description="FastAPI backend for managing Gemini chatbot conversation history",
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
adk_service = ADKService()

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

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
    return {"message": "Gemini Chatbot Backend API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# Conversation endpoints
@app.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    request: CreateConversationRequest,
    user = Depends(get_current_user)
):
    """Create a new conversation"""
    # Create conversation using message service
    conversation_id = f"conv_{uuid.uuid4().hex[:12]}"
    # Note: For full conversation management, implement in message_service
    conversation = {"id": conversation_id, "title": request.title}
    return conversation

@app.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    user = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get user's conversations with pagination"""
    # For now, return empty list - implement conversation listing in message_service if needed
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
    # For now, return success - implement title management in message_service if needed
    return {"message": "Title updated successfully"}

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

# Initialize Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is required. Please set it in your .env file.")
genai.configure(api_key=GOOGLE_API_KEY)
client = genai
MODEL_ID = "gemini-2.0-flash"

system_instruction = """
You are Knowledge Surf, an intelligent AI assistant specialized in providing comprehensive information about coastal Karnataka, India. 

Your expertise covers:
- Culture and traditions of coastal Karnataka (Mangaluru, Udupi, Karwar, Kundapura, etc.)
- Local languages: Tulu, Konkani, Kannada dialects
- Tourism destinations: beaches, temples, heritage sites, hill stations
- Local cuisine: Mangalorean, Udupi, coastal delicacies
- Festivals and celebrations unique to the region
- History and heritage of coastal Karnataka
- Local arts, crafts, and performing arts
- Geography, climate, and natural attractions
- Transportation and travel information
- Local customs and lifestyle

Use Google search and grounding to provide accurate, up-to-date information. Always cite reliable sources when providing factual information about places, events, or cultural practices.
"""

# Global chat history
chat_history = []

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    user = Depends(get_current_user)
):
    """Upload a file and return its URL"""
    try:
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Return file URL
        file_url = f"/uploads/{unique_filename}"
        return {
            "filename": file.filename,
            "file_url": file_url,
            "file_size": os.path.getsize(file_path)
        }
    except Exception as e:
        logger.error(f"File upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

@app.post("/chat")
async def chat_endpoint(
    request: dict,
    user = Depends(get_current_user)
):
    """Chat with Gemini AI"""
    try:
        user_input = request.get("user_input")
        conversation_id = request.get("conversation_id")
        attachments = request.get("attachments", [])  # List of file URLs
        
        if not user_input:
            raise HTTPException(status_code=400, detail="user_input is required")
        
        # Create conversation if not provided
        if not conversation_id:
            # Generate title from first few words of user input
            title_words = user_input.split()[:4]
            title = " ".join(title_words) + ("..." if len(user_input.split()) > 4 else "")
            
            conversation_id = f"conv_{uuid.uuid4().hex[:12]}"
        
        # Add user message with attachments
        user_metadata = MessageMetadata(attachments=attachments) if attachments else None
        message_service.add_message_to_conversation(
            conversation_id=conversation_id,
            role="user",
            content=user_input
        )
        
        # Get conversation history
        messages = message_service.get_conversation_messages(conversation_id)
        
        # Format history for Gemini
        history = []
        for msg in messages[:-1]:  # Exclude the last message (current user input)
            if msg.get("role") == "user":
                history.append({"role": "user", "parts": [msg["content"]]})
            elif msg.get("role") == "assistant":
                history.append({"role": "model", "parts": [msg["content"]]})
        
        # Prepare multimodal content for current message
        message_parts = [user_input]
        
        # Process attachments for multimodal input
        if attachments:
            for attachment_url in attachments:
                try:
                    # Get file path from URL
                    file_path = attachment_url.replace("/uploads/", "uploads/")
                    
                    if os.path.exists(file_path):
                        mime_type, _ = mimetypes.guess_type(file_path)
                        
                        # Handle images - use genai.upload_file for proper multimodal support
                        if mime_type and mime_type.startswith('image/'):
                            # Upload file to Gemini File API
                            uploaded_file = genai.upload_file(file_path)
                            message_parts.append(uploaded_file)
                        
                        # Handle text files
                        elif mime_type and mime_type.startswith('text/'):
                            with open(file_path, 'r', encoding='utf-8') as f:
                                file_content = f.read()
                            message_parts.append(f"\n\nFile content from {os.path.basename(file_path)}:\n{file_content}")
                        
                        # Handle PDFs and other documents
                        elif file_path.lower().endswith(('.pdf', '.doc', '.docx')):
                            # Upload document to Gemini File API
                            try:
                                uploaded_file = genai.upload_file(file_path)
                                message_parts.append(uploaded_file)
                            except:
                                message_parts.append(f"\n\nAttached document: {os.path.basename(file_path)} (document processing not supported)")
                        
                except Exception as e:
                    logger.error(f"Error processing attachment {attachment_url}: {str(e)}")
                    message_parts.append(f"\n\nNote: Could not process attachment {os.path.basename(attachment_url)}")
        
        # Generate response with Gemini using latest model
        model = genai.GenerativeModel(
            model_name=MODEL_ID,
            system_instruction=system_instruction
        )
        
        # Generate response with proper context
        if len(message_parts) > 1:
            # Multimodal content - include context in the prompt
            context_prompt = ""
            if history:
                context_prompt = "\n\nPrevious conversation context:\n"
                for msg in history[-5:]:  # Include last 5 messages for context
                    role = "User" if msg["role"] == "user" else "Assistant"
                    context_prompt += f"{role}: {msg['parts'][0]}\n"
                context_prompt += "\nCurrent message:\n"
            
            # Add context to the first text part
            message_parts[0] = context_prompt + message_parts[0]
            response = model.generate_content(message_parts)
        else:
            # Text only - use chat with history
            chat = model.start_chat(history=history)
            response = chat.send_message(message_parts[0])
        
        # Add assistant response
        message_service.add_message_to_conversation(
            conversation_id=conversation_id,
            role="assistant",
            content=response.text
        )
        
        return {
            "response": response.text,
            "conversation_id": conversation_id
        }
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/adk-chat")
async def adk_chat_endpoint(
    request: dict,
    user = Depends(get_current_user)
):
    """Chat with ADK Academic Research Agent with session persistence"""
    try:
        user_input = request.get("user_input")
        session_id = request.get("session_id")  # Optional - will create new if not provided
        conversation_id = request.get("conversation_id")  # For Firestore persistence
        streaming = request.get("streaming", False)
        attachments = request.get("attachments", [])  # Handle attachments
        
        if not user_input:
            raise HTTPException(status_code=400, detail="user_input is required")
        
        user_id = user["uid"]
        
        # Get or create ADK session
        session_id, session_data = await adk_service.get_or_create_session(
            user_id=user_id,
            session_id=session_id
        )
        
        # Create Firestore conversation if not provided (for UI persistence)
        if not conversation_id:
            title_words = user_input.split()[:4]
            title = " ".join(title_words) + ("..." if len(user_input.split()) > 4 else "")
            
            conversation_id = f"conv_{uuid.uuid4().hex[:12]}"
        
        # Process attachments for ADK
        enhanced_message = user_input
        if attachments:
            enhanced_message += "\n\nAttached documents:"
            for attachment_url in attachments:
                try:
                    # Get file path from URL
                    file_path = attachment_url.replace("/uploads/", "uploads/")
                    
                    if os.path.exists(file_path):
                        mime_type, _ = mimetypes.guess_type(file_path)
                        
                        # Handle PDFs and documents
                        if file_path.lower().endswith(('.pdf', '.doc', '.docx')):
                            enhanced_message += f"\n- Document: {os.path.basename(file_path)} (attached for analysis)"
                        
                        # Handle text files
                        elif mime_type and mime_type.startswith('text/'):
                            with open(file_path, 'r', encoding='utf-8') as f:
                                file_content = f.read()
                            enhanced_message += f"\n- Text file {os.path.basename(file_path)}:\n{file_content[:2000]}..."
                        
                        # Handle images
                        elif mime_type and mime_type.startswith('image/'):
                            enhanced_message += f"\n- Image: {os.path.basename(file_path)} (attached for analysis)"
                        
                except Exception as e:
                    logger.error(f"Error processing attachment {attachment_url}: {str(e)}")
                    enhanced_message += f"\n- Could not process attachment: {os.path.basename(attachment_url)}"

        # Convert attachment URLs to AttachmentMetadata objects
        attachment_metadata = []
        if attachments:
            for attachment_url in attachments:
                try:
                    # Get file path from URL
                    file_path = attachment_url.replace("/uploads/", "uploads/")
                    
                    if os.path.exists(file_path):
                        mime_type, _ = mimetypes.guess_type(file_path)
                        file_size = os.path.getsize(file_path)
                        filename = os.path.basename(file_path)
                        
                        attachment_metadata.append(AttachmentMetadata(
                            filename=filename,
                            url=attachment_url,
                            type=mime_type or "application/octet-stream",
                            size=file_size,
                            uploaded_at=datetime.now()
                        ))
                except Exception as e:
                    logger.error(f"Error processing attachment metadata {attachment_url}: {str(e)}")
                    continue

        # Add user message with attachments
        user_metadata = MessageMetadata(attachments=attachment_metadata) if attachment_metadata else None
        message_service.add_message_to_conversation(
            conversation_id=conversation_id,
            role="user",
            content=user_input
        )
        
        if streaming:
            # Return streaming response
            from fastapi.responses import StreamingResponse
            import json
            
            async def generate_stream():
                response_text = ""
                async for event in adk_service.run_agent_streaming(user_id, session_id, enhanced_message):
                    # Extract text from streaming events
                    content = event.get("content", {})
                    if content.get("role") == "model":
                        parts = content.get("parts", [])
                        for part in parts:
                            if "text" in part:
                                chunk_text = part["text"]
                                response_text += chunk_text
                                yield f"data: {json.dumps({'chunk': chunk_text, 'session_id': session_id, 'conversation_id': conversation_id})}\n\n"
                
                # Save complete response
                if response_text:
                    message_service.add_message_to_conversation(
                        conversation_id=conversation_id,
                        role="assistant",
                        content=response_text
                    )
                
                yield f"data: {json.dumps({'done': True, 'session_id': session_id, 'conversation_id': conversation_id})}\n\n"
            
            return StreamingResponse(
                generate_stream(),
                media_type="text/plain",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
            )
        else:
            # Non-streaming response
            try:
                events = await adk_service.run_agent(user_id, session_id, enhanced_message)
                response_text = adk_service.extract_response_text(events)
                
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
                    "events": events  # Full ADK events for debugging
                }
            except Exception as adk_error:
                logger.error(f"ADK agent error: {str(adk_error)}")
                
                # Return error message with helpful instructions
                error_message = f"ADK Agent Error: {str(adk_error)}"
                
                # Save error message
                message_service.add_message_to_conversation(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=error_message
                )
                
                return {
                    "response": error_message,
                    "session_id": session_id,
                    "conversation_id": conversation_id,
                    "error": True
                }
            
    except Exception as e:
        logger.error(f"ADK Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/adk-sessions/{session_id}")
async def get_adk_session(
    session_id: str,
    user = Depends(get_current_user)
):
    """Get ADK session details"""
    try:
        session_data = await adk_service.get_session(user["uid"], session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        return session_data
    except Exception as e:
        logger.error(f"Get ADK session error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/adk-sessions/{session_id}")
async def delete_adk_session(
    session_id: str,
    user = Depends(get_current_user)
):
    """Delete ADK session"""
    try:
        success = await adk_service.delete_session(user["uid"], session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"message": "Session deleted successfully"}
    except Exception as e:
        logger.error(f"Delete ADK session error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/adk-agents")
async def list_adk_agents():
    """List available ADK agents"""
    try:
        agents = await adk_service.list_available_agents()
        return {"agents": agents}
    except Exception as e:
        logger.error(f"List ADK agents error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=True
    )