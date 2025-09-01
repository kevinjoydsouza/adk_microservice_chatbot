import firebase_admin
from firebase_admin import credentials, firestore
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import os

from models import ConversationResponse, MessageResponse, ModelConfig, MessageRole, MessageMetadata

class FirestoreService:
    def __init__(self):
        # Initialize mock storage
        self._mock_conversations = {}
        self._mock_messages = {}
        
        # Initialize Firebase Admin SDK
        try:
            if not firebase_admin._apps:
                # Check if using Firestore emulator
                if os.getenv('FIRESTORE_EMULATOR_HOST'):
                    print("Using Firestore Emulator for local development")
                    # Initialize with default project for emulator
                    firebase_admin.initialize_app(options={'projectId': 'demo-project'})
                    self.db = firestore.client()
                else:
                    # Use service account key file or default credentials
                    cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
                    if cred_path and os.path.exists(cred_path):
                        cred = credentials.Certificate(cred_path)
                        firebase_admin.initialize_app(cred)
                        self.db = firestore.client()
                    else:
                        # For development - skip Firebase initialization
                        print("WARNING: Firebase credentials not found. Using mock data for development.")
                        print("To use Firestore emulator, set FIRESTORE_EMULATOR_HOST=localhost:8080")
                        self.db = None
            else:
                self.db = firestore.client()
            
            self.conversations_collection = "conversations"
            self.messages_collection = "messages"
            
            if self.db:
                print("Firestore client initialized successfully")
            else:
                print("Running in mock mode")
                
        except Exception as e:
            print(f"WARNING: Firebase initialization failed: {e}")
            print("Using mock data for development.")
            self.db = None
            self.conversations_collection = "conversations"
            self.messages_collection = "messages"

    async def create_conversation(
        self, 
        user_id: str, 
        title: str, 
        model_config: ModelConfig
    ) -> ConversationResponse:
        """Create a new conversation"""
        conversation_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        conversation_data = {
            "id": conversation_id,
            "user_id": user_id,
            "title": title,
            "created_at": now,
            "updated_at": now,
            "message_count": 0,
            "model_settings": model_config.dict()
        }
        
        # Save to Firestore (or mock for development)
        if self.db:
            self.db.collection(self.conversations_collection).document(conversation_id).set(conversation_data)
        else:
            print(f"MOCK: Created conversation {conversation_id} for user {user_id}")
            # Store in memory for mock mode
            if not hasattr(self, '_mock_conversations'):
                self._mock_conversations = {}
            self._mock_conversations[conversation_id] = conversation_data
        
        return ConversationResponse(
            id=conversation_id,
            user_id=user_id,
            title=title,
            created_at=now,
            updated_at=now,
            message_count=0,
            model_settings=model_config,
            messages=[]
        )

    async def get_user_conversations(
        self, 
        user_id: str, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[ConversationResponse]:
        """Get user's conversations with pagination"""
        if not self.db:
            print(f"MOCK: Getting conversations for user {user_id}")
            if not hasattr(self, '_mock_conversations'):
                self._mock_conversations = {}
            
            conversations = []
            for conv_id, conv_data in self._mock_conversations.items():
                if conv_data["user_id"] == user_id:
                    conversation = ConversationResponse(
                        id=conv_data["id"],
                        user_id=conv_data["user_id"],
                        title=conv_data["title"],
                        created_at=conv_data["created_at"],
                        updated_at=conv_data["updated_at"],
                        message_count=conv_data["message_count"],
                        model_settings=ModelConfig(**conv_data.get("model_settings", {"model_name": "gemini-2.5-flash", "temperature": 0.7})),
                        messages=[]
                    )
                    conversations.append(conversation)
            return conversations
            
        query = (
            self.db.collection(self.conversations_collection)
            .where("user_id", "==", user_id)
            .order_by("updated_at", direction=firestore.Query.DESCENDING)
            .limit(limit)
            .offset(offset)
        )
        
        docs = query.stream()
        conversations = []
        
        for doc in docs:
            data = doc.to_dict()
            
            # Get recent messages for preview
            messages = await self._get_conversation_messages(doc.id, limit=5)
            
            conversation = ConversationResponse(
                id=data["id"],
                user_id=data["user_id"],
                title=data["title"],
                created_at=data["created_at"],
                updated_at=data["updated_at"],
                message_count=data["message_count"],
                model_settings=ModelConfig(**data.get("model_settings", {"model_name": "gemini-2.5-flash", "temperature": 0.7})),
                messages=messages
            )
            conversations.append(conversation)
        
        return conversations

    async def get_conversation(
        self, 
        conversation_id: str, 
        user_id: str
    ) -> Optional[ConversationResponse]:
        """Get a specific conversation with all messages"""
        if not self.db:
            print(f"MOCK: Getting conversation {conversation_id} for user {user_id}")
            if not hasattr(self, '_mock_conversations'):
                self._mock_conversations = {}
            if not hasattr(self, '_mock_messages'):
                self._mock_messages = {}
            
            if conversation_id not in self._mock_conversations:
                return None
            
            conv_data = self._mock_conversations[conversation_id]
            if conv_data["user_id"] != user_id:
                return None
            
            # Get messages for this conversation
            messages = []
            for msg_id, msg_data in self._mock_messages.items():
                if msg_data["conversation_id"] == conversation_id:
                    message = MessageResponse(
                        id=msg_data["id"],
                        conversation_id=msg_data["conversation_id"],
                        role=MessageRole(msg_data["role"]),
                        content=msg_data["content"],
                        timestamp=msg_data["timestamp"],
                        metadata=MessageMetadata(**msg_data["metadata"]) if msg_data["metadata"] else None
                    )
                    messages.append(message)
            
            return ConversationResponse(
                id=conv_data["id"],
                user_id=conv_data["user_id"],
                title=conv_data["title"],
                created_at=conv_data["created_at"],
                updated_at=conv_data["updated_at"],
                message_count=conv_data["message_count"],
                model_settings=ModelConfig(**conv_data.get("model_settings", {"model_name": "gemini-2.5-flash", "temperature": 0.7})),
                messages=messages
            )
        
        doc_ref = self.db.collection(self.conversations_collection).document(conversation_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            return None
        
        data = doc.to_dict()
        
        # Verify user ownership
        if data["user_id"] != user_id:
            return None
        
        # Get all messages
        messages = await self._get_conversation_messages(conversation_id)
        
        return ConversationResponse(
            id=data["id"],
            user_id=data["user_id"],
            title=data["title"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            message_count=data["message_count"],
            model_settings=ModelConfig(**data.get("model_settings", {"model_name": "gemini-2.5-flash", "temperature": 0.7})),
            messages=messages
        )

    async def add_message(
        self,
        conversation_id: str,
        user_id: str,
        role: MessageRole,
        content: str,
        metadata: Optional[MessageMetadata] = None
    ) -> MessageResponse:
        """Add a message to a conversation"""
        if not self.db:
            print(f"MOCK: Adding message to conversation {conversation_id}")
            if not hasattr(self, '_mock_conversations'):
                self._mock_conversations = {}
            if not hasattr(self, '_mock_messages'):
                self._mock_messages = {}
            
            if conversation_id not in self._mock_conversations:
                raise ValueError("Conversation not found")
            
            conv_data = self._mock_conversations[conversation_id]
            if conv_data["user_id"] != user_id:
                raise ValueError("Access denied")
            
            message_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            message_data = {
                "id": message_id,
                "conversation_id": conversation_id,
                "role": role.value,
                "content": content,
                "timestamp": now,
                "metadata": metadata.dict() if metadata else None
            }
            
            self._mock_messages[message_id] = message_data
            
            # Update conversation
            self._mock_conversations[conversation_id]["updated_at"] = now
            self._mock_conversations[conversation_id]["message_count"] += 1
            
            return MessageResponse(
                id=message_id,
                conversation_id=conversation_id,
                role=role,
                content=content,
                timestamp=now,
                metadata=metadata
            )
        
        # Verify conversation exists and user owns it
        conv_ref = self.db.collection(self.conversations_collection).document(conversation_id)
        conv_doc = conv_ref.get()
        
        if not conv_doc.exists or conv_doc.to_dict()["user_id"] != user_id:
            raise ValueError("Conversation not found or access denied")
        
        message_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        message_data = {
            "id": message_id,
            "conversation_id": conversation_id,
            "role": role.value,
            "content": content,
            "timestamp": now,
            "metadata": metadata.dict() if metadata else None
        }
        
        # Use batch write for atomicity
        batch = self.db.batch()
        
        # Add message
        message_ref = self.db.collection(self.messages_collection).document(message_id)
        batch.set(message_ref, message_data)
        
        # Update conversation
        batch.update(conv_ref, {
            "updated_at": now,
            "message_count": firestore.Increment(1)
        })
        
        # Auto-generate title from first user message if title is generic
        conv_data = conv_doc.to_dict()
        if (role == MessageRole.USER and 
            conv_data["message_count"] == 0 and 
            conv_data["title"] in ["New Conversation", "Untitled"]):
            
            # Generate title from first 50 characters of user message
            new_title = content[:50] + "..." if len(content) > 50 else content
            batch.update(conv_ref, {"title": new_title})
        
        batch.commit()
        
        return MessageResponse(
            id=message_id,
            conversation_id=conversation_id,
            role=role,
            content=content,
            timestamp=now,
            metadata=metadata
        )

    async def get_messages(
        self,
        conversation_id: str,
        user_id: str,
        limit: int = 50,
        before_timestamp: Optional[str] = None
    ) -> List[MessageResponse]:
        """Get messages from a conversation with pagination"""
        # Verify user owns conversation
        conv_ref = self.db.collection(self.conversations_collection).document(conversation_id)
        conv_doc = conv_ref.get()
        
        if not conv_doc.exists or conv_doc.to_dict()["user_id"] != user_id:
            return []
        
        return await self._get_conversation_messages(
            conversation_id, 
            limit=limit, 
            before_timestamp=before_timestamp
        )

    async def _get_conversation_messages(
        self,
        conversation_id: str,
        limit: int = 50,
        before_timestamp: Optional[str] = None
    ) -> List[MessageResponse]:
        """Internal method to get conversation messages"""
        query = (
            self.db.collection(self.messages_collection)
            .where("conversation_id", "==", conversation_id)
            .order_by("timestamp", direction=firestore.Query.DESCENDING)
            .limit(limit)
        )
        
        if before_timestamp:
            before_dt = datetime.fromisoformat(before_timestamp.replace('Z', '+00:00'))
            query = query.where("timestamp", "<", before_dt)
        
        docs = query.stream()
        messages = []
        
        for doc in docs:
            data = doc.to_dict()
            metadata = None
            if data.get("metadata"):
                metadata = MessageMetadata(**data["metadata"])
            
            message = MessageResponse(
                id=data["id"],
                conversation_id=data["conversation_id"],
                role=MessageRole(data["role"]),
                content=data["content"],
                timestamp=data["timestamp"],
                metadata=metadata
            )
            messages.append(message)
        
        # Return in chronological order (oldest first)
        return list(reversed(messages))

    async def update_conversation_title(
        self,
        conversation_id: str,
        user_id: str,
        title: str
    ) -> bool:
        """Update conversation title"""
        doc_ref = self.db.collection(self.conversations_collection).document(conversation_id)
        doc = doc_ref.get()
        
        if not doc.exists or doc.to_dict()["user_id"] != user_id:
            return False
        
        doc_ref.update({
            "title": title,
            "updated_at": datetime.utcnow()
        })
        
        return True

    async def delete_conversation(
        self,
        conversation_id: str,
        user_id: str
    ) -> bool:
        """Delete a conversation and all its messages"""
        # Verify conversation exists and user owns it
        conv_ref = self.db.collection(self.conversations_collection).document(conversation_id)
        conv_doc = conv_ref.get()
        
        if not conv_doc.exists or conv_doc.to_dict()["user_id"] != user_id:
            return False
        
        # Delete all messages in batches
        messages_query = (
            self.db.collection(self.messages_collection)
            .where("conversation_id", "==", conversation_id)
        )
        
        # Delete in batches of 500 (Firestore limit)
        batch_size = 500
        docs = messages_query.limit(batch_size).stream()
        
        while True:
            batch = self.db.batch()
            count = 0
            
            for doc in docs:
                batch.delete(doc.reference)
                count += 1
            
            if count == 0:
                break
            
            batch.commit()
            
            if count < batch_size:
                break
            
            docs = messages_query.limit(batch_size).stream()
        
        # Delete conversation
        conv_ref.delete()
        
        return True
