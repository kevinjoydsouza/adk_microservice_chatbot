# IntelliSurf AI - Intelligent Knowledge & Document Solutions

A cutting-edge AI platform powered by Google ADK and Gemini, featuring intelligent research agents, document generation, and advanced conversation management for professional AI solutions.

## Features

### Backend API (FastAPI)
- **ADK Integration**: Google Agent Development Kit with intelligent research agents
- **Smart Storage**: Automatic local/cloud hybrid with unlimited content size
- **Document Generation**: RFP, proposal, and report generation with request tracking
- **Session Persistence**: Hybrid ADK + Firestore session management
- **File Processing**: Upload and analyze images, PDFs, documents
- **Local Development**: Works without Firestore for testing

### Frontend (Streamlit)
- **Professional AI Interface**: Modern chat UI with agent selection
- **Multi-Agent Support**: Switch between Research, RFP Generation, and General Chat
- **File Upload**: Drag-and-drop attachments with intelligent processing
- **Document Tracking**: Monitor RFP and document generation progress
- **Conversation Management**: Persistent chat history with search and organization

## Quick Start with Docker

1. **Clone and setup environment**:
```bash
git clone <repository>
cd Gemini-Backend-API
cp .env.example .env
# Edit .env with your Google API key
```

2. **Build and run Backend API**:
```bash
docker build -f Dockerfile.backend -t intellisurf-backend .
docker run --env-file .env -p 8080:8080 -p 8000:8000 -v $(pwd)/uploads:/app/uploads intellisurf-backend
```

3. **Build and run Frontend** (in a new terminal):
```bash
docker build -f Dockerfile.frontend -t intellisurf-frontend .
docker run --env-file .env -p 8501:8501 intellisurf-frontend
```

4. **Access the application**:
- Frontend: http://localhost:8501
- Backend API: http://localhost:8080
- ADK Server: http://localhost:8000
- API Docs: http://localhost:8080/docs

## Manual Setup (Without Docker)

### 1. Setup Environment
```bash
# Clone repository
git clone <repository>
cd IntelliSurf-AI

# Create virtual environment
python -m venv intellisurf-venv
.\intellisurf-venv\Scripts\activate  # Windows
# source intellisurf-venv/bin/activate  # Linux/Mac

# Create .env file from template
cp .env.example .env
# Edit .env file and add your GOOGLE_API_KEY
```

### 2. Install Dependencies
```bash
# Install all dependencies
pip install -r requirements.txt
pip install -r requirements_streamlit.txt
```

### 3. Start Services (3 Terminals)

**Manual Service Startup:**
```bash
cd IntelliSurf-AI
.\intellisurf-venv\Scripts\activate
adk api_server --host 0.0.0.0 --port 8000
```

**Terminal 2 - Backend API:**
```bash
cd IntelliSurf-AI
.\intellisurf-venv\Scripts\activate
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

**Terminal 3 - Frontend:**
```bash
cd IntelliSurf-AI
.\intellisurf-venv\Scripts\activate
streamlit run streamlit_app.py --server.port 8501
```

### Port Conflict Resolution
If you encounter "Port already in use" errors:

**Backend (FastAPI):**
```bash
# Check what's using port 8080
netstat -ano | findstr :8080

# Kill process (replace PID with actual process ID)
taskkill /PID <PID> /F

# Or use different port
uvicorn main:app --reload --host 0.0.0.0 --port 8081
```

**Frontend (Streamlit):**
```bash
# Check what's using port 8501
netstat -ano | findstr :8501

# Kill process or use different port
streamlit run streamlit_app.py --server.port 8502
```

## Environment Variables

**Required:**
- `GOOGLE_API_KEY` - Your Google Gemini API key (get from [Google AI Studio](https://makersuite.google.com/app/apikey))

**Production (Cloud Storage):**
- `GOOGLE_CLOUD_PROJECT` - Your Google Cloud Project ID
- `GOOGLE_APPLICATION_CREDENTIALS` - Path to service account JSON file
- `GOOGLE_CLOUD_STORAGE_BUCKET` - Storage bucket name (e.g., intellisurf-ai-storage)
- `USE_CLOUD_STORAGE` - Set to "true" for production

**Development (Local):**
- `USE_CLOUD_STORAGE` - Set to "false" for local file storage
- No Firestore or Cloud Storage required for testing

### Getting Your Google API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated key
5. Add it to your `.env` file:
```bash
GOOGLE_API_KEY=your_actual_api_key_here
```

**⚠️ Security Note:** Never commit your actual API key to version control. The `.env` file is gitignored for security.

## API Endpoints

### Core Chat Endpoints
- `POST /adk-chat` - Send message to IntelliSurf Research Agent
- `POST /chat` - Send message with Direct Gemini (legacy)
- `POST /upload` - Upload files for chat attachments

### Conversation Management
- `GET /conversations` - List user conversations
- `GET /conversations/{id}` - Get conversation with messages
- `POST /conversations` - Create new conversation
- `PUT /conversations/{id}/title` - Update conversation title

### Document Generation
- `POST /create-document-request` - Create RFP/document generation request
- `GET /document-requests` - List user's document requests
- `POST /webhook/document-status` - Update document processing status

### ADK Session Management
- `GET /adk-sessions/{session_id}` - Get ADK session details
- `DELETE /adk-sessions/{session_id}` - Delete ADK session
- `GET /adk-agents` - List available ADK agents

## File Support

- **Images**: JPG, PNG, GIF, WebP (visual analysis)
- **Documents**: PDF, DOC, DOCX (content extraction)
- **Text Files**: TXT, CSV, JSON (content processing)

## Architecture

```
Streamlit UI (8501) → FastAPI Backend (8080) → ADK Server (8000)
                    ↓                        ↓
                Firestore DB              Research Agents
                                             ↓
                                        Gemini 2.5 Pro
```

### Component Overview
- **Streamlit Frontend**: Professional AI chat interface
- **FastAPI Backend**: API orchestration and session management
- **ADK Server**: Google Agent Development Kit with research agents
- **Firestore**: Conversation persistence and document request tracking

## Development & Production

**Local Development:**
- **No Setup Required**: Works with local file storage (`./local_storage/`)
- **Automatic Fallback**: Detects missing cloud credentials and uses local storage
- **File Processing**: Automatic file type detection and processing

**Production Deployment:**
- **Cloud Storage**: Unlimited content size with Google Cloud Storage
- **Firestore**: Metadata and conversation management
- **Auto-scaling**: Handles any load with Google Cloud infrastructure
- **Smart Storage**: Automatic local/cloud storage selection

##############################################################
🚀 Terminal Commands to Run the Application
## Option 1: Non-Docker Setup
Step 1: Setup Environment

bash
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
Step 2: Run Backend (Terminal 1)

bash
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
Step 3: Run Frontend (Terminal 2)

bash
pip install -r requirements_streamlit.txt
streamlit run streamlit_app.py --server.port 8501
## Option 2: Docker Setup
Backend (Terminal 1)

bash
docker build -f Dockerfile.backend -t knowledge-surf-backend .
docker run --env-file .env -p 8000:8000 -v $(pwd)/uploads:/app/uploads knowledge-surf-backend
Frontend (Terminal 2)

bash
docker build -f Dockerfile.frontend -t knowledge-surf-frontend .
docker run --env-file .env -p 8501:8501 knowledge-surf-frontend
If Ports Are In Use:
Backend on different port:

bash
uvicorn main:app --reload --host 0.0.0.0 --port 8001
# Update BACKEND_URL=http://localhost:8001 in .env
Frontend on different port:

bash
streamlit run streamlit_app.py --server.port 8502
Access URLs:
Frontend: http://localhost:8501
Backend API: http://localhost:8000
API Docs: http://localhost:8000/docs
✅ What's Included:
✅ .env file support for both Docker and non-Docker
✅ Port conflict resolution instructions
✅ Complete setup documentation
✅ Separate Dockerfiles (no compose needed)
✅ Environment variable loading with python-dotenv
Your ChatGPT-style multimodal chatbot is ready to run! 🎉



## Appendix
# creating your virtual environment
step1: python -m venv [gemini-venv]
step2: .\[gemini-venv]\Scripts\activate
step3: pip install -r requirements.txt
step4: pip install -r requirements_streamlit.txt

# running the application
step1: uvicorn main:app --reload --host 0.0.0.0 --port 8000
step2: streamlit run streamlit_app.py --server.port 8501

# running the application with docker
step1: docker build -f Dockerfile.backend -t knowledge-surf-backend .
step2: docker run --env-file .env -p 8000:8000 -v $(pwd)/uploads:/app/uploads knowledge-surf-backend
step3: docker build -f Dockerfile.frontend -t knowledge-surf-frontend .
step4: docker run --env-file .env -p 8501:8501 knowledge-surf-frontend

# accessing the application
step1: http://localhost:8501
step2: http://localhost:8000/docs                       