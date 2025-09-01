# Code Architecture & Training Documentation

## 🏗️ System Overview

This is a **ChatGPT-style multimodal AI chatbot** built with:
- **Backend**: FastAPI (Python) - REST API server
- **Frontend**: Streamlit (Python) - Web interface
- **AI Engine**: Google Gemini 1.5 Flash - Multimodal AI
- **Storage**: Mock mode (in-memory) for local development

## 📊 Data Flow Architecture

```
User Input → Streamlit Frontend → FastAPI Backend → Gemini API
    ↓              ↓                    ↓              ↓
File Upload → File Processing → Multimodal Content → AI Response
    ↓              ↓                    ↓              ↓
Local Storage ← Mock Database ← Conversation History ← Response
```

## 🔄 How Local Storage Works (Mock Mode)

### Without Firestore Database

The application runs in **"Mock Mode"** when no Firebase credentials are provided:

**In-Memory Storage**:
```python
# FirestoreService.__init__()
self._mock_conversations = {}  # Stores conversation metadata
self._mock_messages = {}       # Stores all messages
```

**Data Structure**:
```python
# Conversation Storage
_mock_conversations = {
    "conversation_id_1": {
        "id": "uuid",
        "user_id": "dev-user-123",
        "title": "Chat about coastal Karnataka",
        "created_at": datetime,
        "updated_at": datetime,
        "message_count": 5,
        "model_config": {...}
    }
}

# Message Storage  
_mock_messages = {
    "message_id_1": {
        "id": "uuid",
        "conversation_id": "conversation_id_1",
        "role": "user",
        "content": "Tell me about Mangalore beaches",
        "timestamp": datetime,
        "metadata": {"attachments": [...]}
    }
}
```

**Persistence**: Data exists only while the server is running. Restart = fresh start.

## 🔧 Backend Components

### 1. Main Application (`main.py`)

**Key Functions**:
- **Authentication**: Mock user (`dev-user-123`) for development
- **File Upload**: Handles multimodal attachments
- **Chat Endpoint**: Processes user input + files → Gemini → Response
- **Conversation Management**: CRUD operations for chat history

**Critical Code Sections**:

```python
# Mock Authentication (Line 65-72)
async def get_current_user():
    return {
        "uid": "dev-user-123",
        "email": "dev@example.com", 
        "name": "Development User"
    }

# Chat Processing (Line 240-380)
@app.post("/chat")
async def chat_endpoint(request: dict, user = Depends(get_current_user)):
    # 1. Extract user input and attachments
    # 2. Create/get conversation
    # 3. Process multimodal content (images, PDFs, text)
    # 4. Send to Gemini API
    # 5. Store response in mock database
    # 6. Return AI response
```

### 2. Firestore Service (`services/firestore_service.py`)

**Mock Mode Logic**:
```python
def __init__(self):
    try:
        # Try to initialize Firebase
        if os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
            # Use real Firestore
        else:
            # Fall back to mock mode
            print("Using mock data for development")
            self.db = None
    except:
        self.db = None  # Mock mode
```

**Mock Operations**:
- `create_conversation()` → Stores in `_mock_conversations`
- `add_message()` → Stores in `_mock_messages`
- `get_user_conversations()` → Retrieves from memory
- All operations print debug messages: `"MOCK: Created conversation..."`

### 3. Models (`models.py`)

**Data Structures**:
```python
class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"

class ConversationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    model_config: ModelConfig
    messages: List[MessageResponse]
```

## 🎨 Frontend Components

### 1. Streamlit App (`streamlit_app.py`)

**Key Features**:
- **Sidebar**: Conversation list with create/switch functionality
- **Main Chat**: Message display with user/assistant bubbles
- **File Upload**: Drag-and-drop with preview chips
- **Real-time Updates**: Auto-refresh conversation list

**Critical Code Sections**:

```python
# Session State Management (Line 20-35)
if 'conversations' not in st.session_state:
    st.session_state.conversations = []
if 'current_conversation_id' not in st.session_state:
    st.session_state.current_conversation_id = None

# File Upload with Dynamic Keys (Line 189-196)
uploader_key = f"file_uploader_{st.session_state.current_conversation_id or 'new'}"
uploaded_files = st.file_uploader(..., key=uploader_key)

# Chat Processing (Line 300-350)
if user_input:
    # 1. Upload files to backend
    # 2. Send chat request with attachments
    # 3. Display response
    # 4. Refresh conversation list
```

### 2. API Communication

**Backend Requests**:
```python
# Get conversations
response = requests.get(f"{BACKEND_URL}/conversations")

# Send chat message
response = requests.post(f"{BACKEND_URL}/chat", json={
    "user_input": message,
    "conversation_id": conv_id,
    "attachments": file_urls
})

# Upload files
files = {"file": uploaded_file}
response = requests.post(f"{BACKEND_URL}/upload", files=files)
```

## 🔄 Complete Request Flow

### 1. User Sends Message with Image

```
1. User types message + uploads image in Streamlit
2. Streamlit uploads image to FastAPI /upload endpoint
3. FastAPI saves image to /uploads/ directory
4. Streamlit sends chat request with message + image URL
5. FastAPI processes multimodal content:
   - Text: user message
   - Image: uploaded via genai.upload_file()
6. FastAPI sends to Gemini API
7. Gemini returns AI response
8. FastAPI stores conversation in mock database
9. FastAPI returns response to Streamlit
10. Streamlit displays AI response
11. Streamlit refreshes conversation list
```

### 2. Mock Database Operations

```python
# When user sends first message:
conversation_id = create_conversation()
_mock_conversations[conv_id] = {...}

# When adding messages:
message_id = add_message()
_mock_messages[msg_id] = {...}
_mock_conversations[conv_id]["message_count"] += 1

# When loading conversations:
for conv_id, conv_data in _mock_conversations.items():
    if conv_data["user_id"] == current_user:
        conversations.append(conv_data)
```

## 🚀 Training Your Team

### Development Setup

1. **Start Backend**:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

2. **Start Frontend**:
```bash
streamlit run streamlit_app.py --server.port 8501
```

3. **Access**:
- Frontend: http://localhost:8501
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Key Learning Points

**Backend (FastAPI)**:
- REST API design with automatic OpenAPI docs
- Dependency injection for authentication
- File upload handling
- External API integration (Gemini)
- Mock vs real database patterns

**Frontend (Streamlit)**:
- Session state management
- Real-time UI updates
- File upload with preview
- API communication
- Modern chat interface design

**Architecture Patterns**:
- Service layer separation (`FirestoreService`)
- Model-based data validation (`Pydantic`)
- Environment-based configuration
- Mock mode for development
- Multimodal AI integration

### Debug Information

**Console Output**:
```
# Backend logs show:
MOCK: Created conversation f8e79d7d-... for user dev-user-123
MOCK: Adding message to conversation f8e79d7d-...
MOCK: Getting conversations for user dev-user-123

# Frontend logs show:
Fetched 0 conversations  # Initially empty
Fetched 1 conversations  # After first chat
Fetched 2 conversations  # After second chat
```

**File Structure**:
```
uploads/                    # User uploaded files
├── uuid1.jpg              # Images for AI processing
├── uuid2.pdf              # Documents for AI processing
└── uuid3.txt              # Text files for AI processing

_mock_conversations = {}    # In-memory conversation storage
_mock_messages = {}         # In-memory message storage
```

This architecture demonstrates modern web application patterns while keeping complexity low for training purposes. The mock mode allows immediate development without external dependencies.
