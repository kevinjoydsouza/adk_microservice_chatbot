from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum

# ==================== ENUMS ====================

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ConversationStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"

class DocumentRequestType(str, Enum):
    RFP = "rfp"
    PROPOSAL = "proposal"
    REPORT = "report"
    SUMMARY = "summary"

class DocumentStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class AgentType(str, Enum):
    ACADEMIC_RESEARCH = "academic-research"
    RFP_GENERATION = "rfp-generation"
    GENERAL_CHAT = "general-chat"

# ==================== BASE MODELS ====================

class ModelConfig(BaseModel):
    model_name: str = "gemini-2.5-flash"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=2048, gt=0)
    top_p: Optional[float] = Field(default=0.9, ge=0.0, le=1.0)
    top_k: Optional[int] = Field(default=40, gt=0)

class AttachmentMetadata(BaseModel):
    filename: str
    url: str
    type: str  # MIME type
    size: int  # bytes
    uploaded_at: datetime = Field(default_factory=datetime.now)

class MessageMetadata(BaseModel):
    attachments: List[AttachmentMetadata] = Field(default_factory=list)
    model_version: Optional[str] = None
    processing_time_ms: Optional[int] = None
    token_count: Optional[int] = None
    agent_events: Optional[List[Dict]] = Field(default_factory=list)
    related_request_id: Optional[str] = None

# ==================== CONVERSATION MODELS ====================

class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: MessageRole
    content: str
    timestamp: datetime
    metadata: Optional[MessageMetadata] = None

class ConversationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    agent_type: AgentType = AgentType.ACADEMIC_RESEARCH
    created_at: datetime
    updated_at: datetime
    message_count: int
    model_settings: ModelConfig
    status: ConversationStatus = ConversationStatus.ACTIVE
    messages: List[MessageResponse] = Field(default_factory=list)

class CreateConversationRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    agent_type: AgentType = AgentType.ACADEMIC_RESEARCH
    model_settings: Optional[ModelConfig] = Field(default_factory=ModelConfig)

class AddMessageRequest(BaseModel):
    role: MessageRole
    content: str = Field(..., min_length=1)
    metadata: Optional[MessageMetadata] = None

class UpdateTitleRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)

class ConversationSummary(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    last_message_preview: Optional[str] = None

# ==================== DOCUMENT REQUEST MODELS ====================

class ProjectDetails(BaseModel):
    project_name: str
    opportunity_id: str
    client_email: str
    deadline: datetime
    budget_range: Optional[str] = None
    industry: Optional[str] = None

class DocumentConfig(BaseModel):
    template_type: str
    sections: List[str]
    format: str = "pdf"
    length: str = "detailed"
    custom_requirements: Optional[Dict[str, Any]] = None

class DocumentRequest(BaseModel):
    id: str
    user_id: str
    conversation_id: Optional[str] = None
    request_type: DocumentRequestType
    project_details: ProjectDetails
    document_config: DocumentConfig
    status: DocumentStatus = DocumentStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)

# ==================== API MODELS ====================

class ChatRequest(BaseModel):
    user_input: str
    conversation_id: Optional[str] = None
    session_id: Optional[str] = None
    agent_type: AgentType = AgentType.ACADEMIC_RESEARCH
    streaming: bool = False
    attachments: List[AttachmentMetadata] = Field(default_factory=list)

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    session_id: Optional[str] = None
    message_id: str
    processing_time_ms: int
    token_count: int
