"""ADK Integration Service for managing ADK API server interactions."""

import httpx
import json
import uuid
import os
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)

class ADKService:
    """Service for interacting with ADK API server endpoints."""
    
    def __init__(self, adk_base_url: str = "http://localhost:8000", app_name: str = "academic-research"):
        self.base_url = adk_base_url
        self.app_name = app_name
        
    async def list_available_agents(self) -> List[str]:
        """Get list of available ADK agents."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/list-apps")
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Failed to list agents: {e}")
                return []
    
    async def create_session(self, user_id: str, session_id: str, initial_state: Optional[Dict] = None) -> Dict:
        """Create or update an ADK session."""
        url = f"{self.base_url}/apps/{self.app_name}/users/{user_id}/sessions/{session_id}"
        
        payload = {
            "state": initial_state or {}
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Failed to create session: {e}")
                raise
    
    async def get_session(self, user_id: str, session_id: str) -> Optional[Dict]:
        """Get session details including state and events."""
        url = f"{self.base_url}/apps/{self.app_name}/users/{user_id}/sessions/{session_id}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    return None
                logger.error(f"Failed to get session: {e}")
                raise
            except Exception as e:
                logger.error(f"Failed to get session: {e}")
                raise
    
    async def delete_session(self, user_id: str, session_id: str) -> bool:
        """Delete a session and all associated data."""
        url = f"{self.base_url}/apps/{self.app_name}/users/{user_id}/sessions/{session_id}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.delete(url)
                response.raise_for_status()
                return True
            except Exception as e:
                logger.error(f"Failed to delete session: {e}")
                return False
    
    async def run_agent(self, user_id: str, session_id: str, message: str, attachments: list = None) -> List[Dict]:
        """Run agent and get all events at once."""
        # Prepare message parts according to ADK Content object format
        message_parts = [{"text": message}]
        
        # Process attachments if provided
        if attachments:
            import google.generativeai as genai
            
            # Configure Gemini API for file uploads
            GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
            if GOOGLE_API_KEY:
                genai.configure(api_key=GOOGLE_API_KEY)
            
            for attachment_url in attachments:
                try:
                    # Convert URL to file path
                    file_path = attachment_url.replace("/uploads/", "uploads/")
                    if os.path.exists(file_path):
                        # Upload file to Google API to get proper URI
                        uploaded_file = genai.upload_file(file_path)
                        
                        # Add file as attachment part using proper ADK format
                        message_parts.append({
                            "file_data": {
                                "file_uri": uploaded_file.uri,
                                "mime_type": uploaded_file.mime_type
                            }
                        })
                        
                        logger.info(f"Uploaded file to Google API: {uploaded_file.uri}")
                        logger.info(f"File name: {uploaded_file.name}, MIME type: {uploaded_file.mime_type}")
                        logger.info(f"Message parts now: {message_parts}")
                        
                except Exception as e:
                    logger.error(f"Error processing attachment {attachment_url}: {str(e)}")
                    # Add as text reference if file processing fails
                    message_parts.append({"text": f"\n[Attachment: {os.path.basename(attachment_url)}]"})
        
        # Use proper ADK Content object format
        payload = {
            "app_name": self.app_name,
            "user_id": user_id,
            "session_id": session_id,
            "new_message": {
                "parts": message_parts,
                "role": "user"
            }
        }
        
        logger.info(f"Sending payload to ADK: {payload}")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/run",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                result = response.json()
                
                # Ensure we return a list of events
                if isinstance(result, dict):
                    return [result]
                elif isinstance(result, list):
                    return result
                else:
                    logger.warning(f"Unexpected response format: {type(result)}")
                    return []
                    
            except httpx.HTTPStatusError as e:
                logger.error(f"ADK HTTP error: {e.response.status_code} - {e.response.text}")
                # Check if ADK server is not running
                if e.response.status_code == 404:
                    raise Exception("ADK server not found. Please start the ADK server with: python -m google.adk.agents.server --app academic-research --port 8000")
                raise Exception(f"ADK server error: {e.response.status_code} - {e.response.text}")
            except httpx.ConnectError as e:
                logger.error(f"ADK connection error: {e}")
                raise Exception("Cannot connect to ADK server. Please ensure the ADK server is running on port 8000")
            except httpx.RequestError as e:
                logger.error(f"ADK request error: {e}")
                raise Exception(f"ADK request failed: {str(e)}")
            except Exception as e:
                logger.error(f"Failed to run agent: {e}")
                raise Exception(f"ADK service error: {str(e)}")
    
    async def run_agent_streaming(self, user_id: str, session_id: str, message: str, streaming: bool = True, attachments: list = None) -> AsyncGenerator[Dict, None]:
        """Run agent with streaming response using ADK's native streaming."""
        # Prepare message parts according to ADK Content object format
        message_parts = [{"text": message}]
        
        # Process attachments if provided
        if attachments:
            import google.generativeai as genai
            
            # Configure Gemini API for file uploads
            GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
            if GOOGLE_API_KEY:
                genai.configure(api_key=GOOGLE_API_KEY)
            
            for attachment_url in attachments:
                try:
                    # Convert URL to file path
                    file_path = attachment_url.replace("/uploads/", "uploads/")
                    if os.path.exists(file_path):
                        # Upload file to Google API to get proper URI
                        uploaded_file = genai.upload_file(file_path)
                        
                        # Add file as attachment part using proper ADK format
                        message_parts.append({
                            "file_data": {
                                "file_uri": uploaded_file.uri,
                                "mime_type": uploaded_file.mime_type
                            }
                        })
                        
                        logger.info(f"Uploaded file to Google API: {uploaded_file.uri}")
                        
                except Exception as e:
                    logger.error(f"Error processing attachment {attachment_url}: {str(e)}")
                    # Add as text reference if file processing fails
                    message_parts.append({"text": f"\n[Attachment: {os.path.basename(attachment_url)}]"})
        
        payload = {
            "app_name": self.app_name,
            "user_id": user_id,
            "session_id": session_id,
            "new_message": {
                "parts": message_parts,
                "role": "user"
            }
        }
        
        logger.info(f"Sending streaming payload to ADK: {payload}")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                # Use the standard /run endpoint with streaming
                async with client.stream(
                    "POST",
                    f"{self.base_url}/run",
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "text/event-stream"
                    }
                ) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line.strip():
                            logger.debug(f"ADK streaming line: {line}")
                            if line.startswith("data: "):
                                try:
                                    event_data = json.loads(line[6:])  # Remove "data: " prefix
                                    logger.debug(f"ADK streaming event: {json.dumps(event_data, indent=2)}")
                                    yield event_data
                                except json.JSONDecodeError as e:
                                    logger.warning(f"Failed to parse streaming data: {line}, error: {e}")
                                    continue
                            elif line.startswith("event: "):
                                # Handle event type lines
                                logger.debug(f"ADK event type: {line}")
                                continue
                            else:
                                # Try to parse as direct JSON
                                try:
                                    event_data = json.loads(line)
                                    logger.debug(f"ADK direct JSON event: {json.dumps(event_data, indent=2)}")
                                    yield event_data
                                except json.JSONDecodeError:
                                    logger.debug(f"Non-JSON line: {line}")
                                    continue
                                    
            except httpx.HTTPStatusError as e:
                logger.error(f"ADK streaming HTTP error: {e.response.status_code} - {e.response.text}")
                if e.response.status_code == 404:
                    # Fallback to non-streaming if streaming not supported
                    logger.info("Streaming not supported, falling back to regular run")
                    events = await self.run_agent(user_id, session_id, message, attachments)
                    for event in events:
                        yield event
                else:
                    raise Exception(f"ADK streaming error: {e.response.status_code} - {e.response.text}")
            except httpx.ConnectError as e:
                logger.error(f"ADK connection error: {e}")
                raise Exception("Cannot connect to ADK server. Please ensure the ADK server is running on port 8000")
            except Exception as e:
                logger.error(f"Failed to run streaming agent: {e}")
                # Fallback to non-streaming
                logger.info("Streaming failed, falling back to regular run")
                events = await self.run_agent(user_id, session_id, message, attachments)
                for event in events:
                    yield event
    
    def generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return str(uuid.uuid4())
    
    def extract_response_text(self, events: List[Dict]) -> str:
        """Extract the final response text from ADK events."""
        response_parts = []
        
        for event in events:
            # Handle different event structures
            if isinstance(event, dict):
                # Check for direct content
                content = event.get("content", {})
                if content.get("role") == "model":
                    parts = content.get("parts", [])
                    for part in parts:
                        if isinstance(part, dict) and "text" in part:
                            response_parts.append(part["text"])
                        elif isinstance(part, str):
                            response_parts.append(part)
                
                # Check for nested event structure
                elif "event" in event:
                    nested_content = event["event"].get("content", {})
                    if nested_content.get("role") == "model":
                        parts = nested_content.get("parts", [])
                        for part in parts:
                            if isinstance(part, dict) and "text" in part:
                                response_parts.append(part["text"])
                            elif isinstance(part, str):
                                response_parts.append(part)
                
                # Check for direct text field
                elif "text" in event:
                    response_parts.append(event["text"])
                
                # Check for response field (common in ADK responses)
                elif "response" in event:
                    response_parts.append(str(event["response"]))
                
                # Check for message field
                elif "message" in event:
                    response_parts.append(str(event["message"]))
        
        result = "".join(response_parts).strip()
        
        # If no text found, return a helpful message
        if not result:
            logger.warning(f"No response text found in events: {events}")
            # Log the full event structure for debugging
            logger.debug(f"Full events for debugging: {json.dumps(events, indent=2)}")
            return "I apologize, but I encountered an issue processing your request. Please try again."
        
        return result
    
    async def get_or_create_session(self, user_id: str, session_id: str = None) -> tuple[str, Dict]:
        """Get existing session or create new one."""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Try to get existing session first
        try:
            session_data = await self.get_session(user_id, session_id)
            if session_data:
                return session_id, session_data
        except Exception:
            pass  # Session doesn't exist, create it
        
        # Create new session
        session_data = await self.create_session(user_id, session_id)
        return session_id, session_data
    
    def _get_mime_type(self, file_path: str) -> str:
        """Get MIME type for a file."""
        import mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or "application/octet-stream"
