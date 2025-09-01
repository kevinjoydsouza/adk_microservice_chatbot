"""ADK Integration Service for managing ADK API server interactions."""

import httpx
import json
import uuid
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)

class ADKService:
    """Service for interacting with ADK API server endpoints."""
    
    def __init__(self, adk_base_url: str = "http://localhost:8000"):
        self.base_url = adk_base_url
        self.app_name = "academic-research"
        
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
    
    async def run_agent(self, user_id: str, session_id: str, message: str) -> List[Dict]:
        """Run agent and get all events at once."""
        payload = {
            "app_name": self.app_name,
            "user_id": user_id,
            "session_id": session_id,
            "new_message": {
                "role": "user",
                "parts": [{"text": message}]
            }
        }
        
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
    
    async def run_agent_streaming(self, user_id: str, session_id: str, message: str, streaming: bool = True) -> AsyncGenerator[Dict, None]:
        """Run agent with streaming response (SSE)."""
        payload = {
            "app_name": self.app_name,
            "user_id": user_id,
            "session_id": session_id,
            "new_message": {
                "role": "user",
                "parts": [{"text": message}]
            },
            "streaming": streaming
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/run_sse",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            try:
                                event_data = json.loads(line[6:])  # Remove "data: " prefix
                                yield event_data
                            except json.JSONDecodeError:
                                continue
            except Exception as e:
                logger.error(f"Failed to run streaming agent: {e}")
                raise
    
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
        
        result = "".join(response_parts).strip()
        
        # If no text found, return a helpful message
        if not result:
            logger.warning(f"No response text found in events: {events}")
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
