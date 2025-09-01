"""
Google Agent Development Kit (ADK) Integration
This module provides integration between ADK agents and the FastAPI conversation backend
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

class ADKConversationManager:
    """Manages conversation persistence for ADK agents"""
    
    def __init__(self, backend_url: str = "http://localhost:8000", auth_token: str = None):
        self.backend_url = backend_url.rstrip('/')
        self.auth_token = auth_token or "dev-token-123"  # Mock token for development
        self.headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
    
    async def create_conversation(self, user_id: str, title: str = "New Conversation") -> Dict[str, Any]:
        """Create a new conversation for ADK agent"""
        async with aiohttp.ClientSession() as session:
            payload = {
                "title": title,
                "model_config": {
                    "model_name": "gemini-pro",
                    "temperature": 0.7
                }
            }
            
            async with session.post(
                f"{self.backend_url}/conversations",
                headers=self.headers,
                json=payload
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to create conversation: {response.status}")
    
    async def add_user_message(self, conversation_id: str, content: str, metadata: Dict = None) -> Dict[str, Any]:
        """Add user message to conversation"""
        async with aiohttp.ClientSession() as session:
            payload = {
                "role": "user",
                "content": content,
                "metadata": metadata or {}
            }
            
            async with session.post(
                f"{self.backend_url}/conversations/{conversation_id}/messages",
                headers=self.headers,
                json=payload
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to add user message: {response.status}")
    
    async def add_agent_response(self, conversation_id: str, content: str, metadata: Dict = None) -> Dict[str, Any]:
        """Add agent response to conversation"""
        async with aiohttp.ClientSession() as session:
            payload = {
                "role": "assistant",
                "content": content,
                "metadata": metadata or {}
            }
            
            async with session.post(
                f"{self.backend_url}/conversations/{conversation_id}/messages",
                headers=self.headers,
                json=payload
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to add agent response: {response.status}")
    
    async def get_conversation_history(self, conversation_id: str) -> Dict[str, Any]:
        """Get full conversation history for ADK context"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.backend_url}/conversations/{conversation_id}",
                headers=self.headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to get conversation: {response.status}")
    
    async def get_user_conversations(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get user's conversation list for ADK agent selection"""
        async with aiohttp.ClientSession() as session:
            params = {"limit": limit}
            async with session.get(
                f"{self.backend_url}/conversations",
                headers=self.headers,
                params=params
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to get conversations: {response.status}")
    
    def format_messages_for_adk(self, conversation: Dict[str, Any]) -> List[Dict[str, str]]:
        """Format conversation messages for ADK agent context"""
        formatted_messages = []
        
        for message in conversation.get("messages", []):
            formatted_messages.append({
                "role": message["role"],
                "content": message["content"],
                "timestamp": message["timestamp"]
            })
        
        return formatted_messages


class ADKAgentWrapper:
    """Wrapper for ADK agents with conversation persistence"""
    
    def __init__(self, agent_config: Dict[str, Any], backend_url: str = "http://localhost:8000"):
        self.agent_config = agent_config
        self.conversation_manager = ADKConversationManager(backend_url)
        self.current_conversation_id = None
    
    async def start_conversation(self, user_id: str, initial_message: str) -> Dict[str, Any]:
        """Start a new conversation with the ADK agent"""
        # Create new conversation
        conversation = await self.conversation_manager.create_conversation(
            user_id=user_id,
            title=initial_message[:50] + "..." if len(initial_message) > 50 else initial_message
        )
        
        self.current_conversation_id = conversation["id"]
        
        # Add initial user message
        await self.conversation_manager.add_user_message(
            conversation_id=self.current_conversation_id,
            content=initial_message
        )
        
        # Generate agent response (integrate with your ADK agent here)
        agent_response = await self._generate_agent_response(initial_message, [])
        
        # Save agent response
        await self.conversation_manager.add_agent_response(
            conversation_id=self.current_conversation_id,
            content=agent_response["content"],
            metadata=agent_response.get("metadata", {})
        )
        
        return {
            "conversation_id": self.current_conversation_id,
            "response": agent_response["content"]
        }
    
    async def continue_conversation(self, conversation_id: str, user_message: str) -> Dict[str, Any]:
        """Continue an existing conversation"""
        self.current_conversation_id = conversation_id
        
        # Add user message
        await self.conversation_manager.add_user_message(
            conversation_id=conversation_id,
            content=user_message
        )
        
        # Get conversation history for context
        conversation = await self.conversation_manager.get_conversation_history(conversation_id)
        message_history = self.conversation_manager.format_messages_for_adk(conversation)
        
        # Generate agent response with context
        agent_response = await self._generate_agent_response(user_message, message_history)
        
        # Save agent response
        await self.conversation_manager.add_agent_response(
            conversation_id=conversation_id,
            content=agent_response["content"],
            metadata=agent_response.get("metadata", {})
        )
        
        return {
            "conversation_id": conversation_id,
            "response": agent_response["content"]
        }
    
    async def _generate_agent_response(self, user_message: str, conversation_history: List[Dict]) -> Dict[str, Any]:
        """
        Generate agent response using ADK
        Replace this with your actual ADK agent implementation
        """
        # TODO: Integrate with your ADK agent here
        # Example structure:
        
        # Build context from conversation history
        context = "\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in conversation_history[-10:]  # Last 10 messages for context
        ])
        
        # Mock response - replace with actual ADK agent call
        mock_response = f"ADK Agent Response to: {user_message}"
        
        return {
            "content": mock_response,
            "metadata": {
                "model_version": "gemini-pro-1.0",
                "tokens_used": len(mock_response.split()),
                "response_time_ms": 1200,
                "finish_reason": "stop"
            }
        }


# Example usage for ADK integration
async def example_adk_integration():
    """Example of how to use ADK with conversation persistence"""
    
    # Initialize ADK agent wrapper
    agent_config = {
        "model": "gemini-pro",
        "temperature": 0.7,
        "instructions": "You are a helpful AI assistant."
    }
    
    adk_agent = ADKAgentWrapper(agent_config)
    
    # Start a new conversation
    user_id = "user-123"
    initial_message = "Hello, I need help with Python programming"
    
    result = await adk_agent.start_conversation(user_id, initial_message)
    print(f"Conversation ID: {result['conversation_id']}")
    print(f"Agent Response: {result['response']}")
    
    # Continue the conversation
    follow_up = "Can you explain list comprehensions?"
    result = await adk_agent.continue_conversation(
        result['conversation_id'], 
        follow_up
    )
    print(f"Follow-up Response: {result['response']}")


if __name__ == "__main__":
    # Run example
    asyncio.run(example_adk_integration())
