# IntelliSurf AI - RFP Research Platform

A specialized AI platform for RFP (Request for Proposal) research, analysis, and proposal generation. Built with FastAPI backend, Streamlit frontend, and Google Cloud integration.

## 🚀 Features

- **🔐 Authentication System** - Secure login with hardcoded credentials
- **📋 RFP Research Agent** - Specialized AI agent for RFP analysis and proposal generation
- **📄 Document Processing** - Upload and process RFP documents, requirements, and attachments
- **💬 Conversation Management** - Persistent chat history with session management
- **☁️ Cloud Storage** - Google Cloud Storage integration for file management
- **🗄️ Firestore Database** - Scalable document database for conversation and metadata storage

## 📁 Project Structure

```
IntelliSurf-RFP-Platform/
├── main.py                     # FastAPI backend server
├── streamlit_app.py            # Streamlit frontend application
├── auth.py                     # Authentication module
├── config.py                   # Configuration settings
├── models.py                   # Pydantic data models
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── rfp-research/              # RFP agent and subagents
│   ├── agent.py              # Main RFP research agent
│   ├── prompt.py             # Agent prompts and instructions
│   └── sub_agents/           # Specialized subagents
├── services/                  # Backend services
│   ├── adk_service.py        # ADK agent service
│   ├── auth_service.py       # Authentication service
│   ├── firestore_service.py  # Firestore database service
│   └── gcs_service.py        # Google Cloud Storage service
├── middleware/                # FastAPI middleware
└── firestore_schemas/         # Database schemas
```

## 🛠️ Setup Instructions

### Prerequisites

- Python 3.8+
- Google Cloud Project (for production)
- Google API Key (Gemini AI)

### Local Development Setup

1. **Clone and Setup Environment**
   ```bash
   git clone <repository-url>
   cd IntelliSurf-RFP-Platform
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Environment Configuration**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your local settings:
   ```env
   # Local Development Configuration
   GOOGLE_API_KEY=your-gemini-api-key
   BACKEND_URL=http://localhost:8080
   FRONTEND_PORT=8501
   BACKEND_PORT=8080
   
   # Local Storage (no cloud required)
   USE_GCS_FOR_UPLOADS=false
   USE_CLOUD_STORAGE=false
   USE_FIRESTORE_EMULATOR=true
   FIRESTORE_EMULATOR_HOST=localhost:8080
   ```

3. **Start Local Services**
   
   **Terminal 1 - Backend:**
   ```bash
   python main.py
   ```
   
   **Terminal 2 - Frontend:**
   ```bash
   streamlit run streamlit_app.py --server.port 8501
   ```

4. **Access Application**
   - Frontend: http://localhost:8501
   - Backend API: http://localhost:8080
   - Login credentials:
     - `admin` / `admin123`
     - `user` / `user123`
     - `demo` / `demo123`

### Production Setup (Google Cloud)

#### 1. Google Cloud Project Setup

```bash
# Create new project
gcloud projects create your-project-id
gcloud config set project your-project-id

# Enable required APIs
gcloud services enable firestore.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable aiplatform.googleapis.com
```

#### 2. Set up Application Default Credentials (ADC)

**For Local Development:**
```bash
# Install Google Cloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Initialize and authenticate
gcloud init
gcloud auth application-default login
```

**For Production (Compute Engine, Cloud Run, GKE):**
```bash
# Create service account for production resources
gcloud iam service-accounts create intellisurf-ai \
    --description="IntelliSurf AI Service Account" \
    --display-name="IntelliSurf AI"

# Grant necessary roles
gcloud projects add-iam-policy-binding your-project-id \
    --member="serviceAccount:intellisurf-ai@your-project-id.iam.gserviceaccount.com" \
    --role="roles/datastore.user"

gcloud projects add-iam-policy-binding your-project-id \
    --member="serviceAccount:intellisurf-ai@your-project-id.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

# Attach service account to compute resources (no JSON keys needed)
```

#### 3. Initialize Cloud Storage

```bash
# Create storage bucket
gsutil mb gs://your-project-id-intellisurf-storage

# Set bucket permissions (optional - for public access)
gsutil iam ch allUsers:objectViewer gs://your-project-id-intellisurf-storage
```

#### 4. Initialize Firestore

```bash
# Create Firestore database
gcloud firestore databases create --region=us-central1

# Initialize collections (run this Python script)
python create_firestore_database.py --project-id your-project-id --action create
```

#### 5. Production Environment Configuration

Create production `.env`:
```env
# Google Cloud Configuration (Uses ADC - No JSON keys needed)
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_API_KEY=your-gemini-api-key

# Cloud Storage
GOOGLE_CLOUD_STORAGE_BUCKET=your-project-id-intellisurf-storage
USE_GCS_FOR_UPLOADS=true
USE_CLOUD_STORAGE=true

# Firestore Production
FIRESTORE_DATABASE_ID=(default)
USE_FIRESTORE_EMULATOR=false

# Production API URLs
BACKEND_URL=https://your-domain.com
FRONTEND_PORT=8501
BACKEND_PORT=8080

# Performance Settings
MAX_TOKENS=8192
TEMPERATURE=0.7
CONTENT_SIZE_THRESHOLD=500000
```

#### 6. Deploy to Cloud Run (Optional)

```bash
# Build and deploy backend
gcloud run deploy intellisurf-backend \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=your-project-id"

# Build and deploy frontend
gcloud run deploy intellisurf-frontend \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --port 8501
```

## 🔧 Configuration Variables

### Required Environment Variables

| Variable | Description | Local Default | Production Example |
|----------|-------------|---------------|-------------------|
| `GOOGLE_API_KEY` | Gemini AI API key | Required | `AIza...` |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID | Not required | `intellisurf-ai-prod` |
| `GOOGLE_CLOUD_STORAGE_BUCKET` | GCS bucket name | Not required | `intellisurf-ai-storage` |
| `USE_GCS_FOR_UPLOADS` | Enable cloud storage | `false` | `true` |
| `USE_CLOUD_STORAGE` | Enable cloud storage for large content | `false` | `true` |
| `USE_FIRESTORE_EMULATOR` | Use local Firestore emulator | `true` | `false` |

### Optional Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `BACKEND_URL` | Backend API URL | `http://localhost:8080` |
| `FRONTEND_PORT` | Streamlit port | `8501` |
| `BACKEND_PORT` | FastAPI port | `8080` |
| `MAX_TOKENS` | AI model max tokens | `8192` |
| `TEMPERATURE` | AI model temperature | `0.7` |
| `CONTENT_SIZE_THRESHOLD` | Cloud storage threshold | `500000` (500KB) |

## 🗄️ Database Schema

### Firestore Collections

- **conversations_v1**: Chat conversation metadata
- **messages_v1**: Individual chat messages
- **document_requests_v1**: RFP document processing requests
- **adk_sessions_v1**: AI agent session data
- **user_profiles_v1**: User profile information

### Cloud Storage Structure

```
gs://bucket-name/
├── uploads/                    # General file uploads
├── teamcentre_mock/
│   └── opportunities/
│       └── {request_id}/
│           ├── documents/      # RFP documents
│           └── proposals/      # Generated proposals
└── temp/                      # Temporary files
```

## 🚀 Usage

### Starting a New RFP Project

1. **Login** to the application
2. **Create New Conversation** 
3. **Upload RFP Documents** - PDFs, Word docs, requirements
4. **Ask the RFP Agent** questions like:
   - "Analyze this RFP and identify key requirements"
   - "Generate a compliance matrix for this opportunity"
   - "Create a proposal outline based on the requirements"
   - "What are the evaluation criteria for this RFP?"

### RFP Agent Capabilities

- **Document Analysis**: Extract requirements, deadlines, evaluation criteria
- **Compliance Checking**: Verify proposal meets all requirements
- **Proposal Generation**: Create structured proposal documents
- **Opportunity Management**: Track RFP opportunities and deadlines
- **Risk Assessment**: Identify potential risks and mitigation strategies

## 🔍 Troubleshooting

### Local Development Issues

**Backend won't start:**
```bash
# Check if port 8080 is available
netstat -an | grep 8080
# Kill process if needed
pkill -f "python main.py"
```

**Streamlit connection errors:**
```bash
# Ensure backend is running first
curl http://localhost:8080/health
# Check environment variables
cat .env
```

### Production Issues

****ADC Authentication:**
```bash
# Check current authentication
gcloud auth list
gcloud auth application-default print-access-token

# Re-authenticate if needed
gcloud auth application-default login
gsutil ls gs://your-bucket-name
```

**Firestore Connection:**
```bash
# Test Firestore access
gcloud firestore collections list --project=your-project-id
```

**Cloud Run Deployment:**
```bash
# Check logs
gcloud run services logs read intellisurf-backend --region=us-central1
```

## 📊 Monitoring & Maintenance

### Health Checks

- Backend: `GET /health`
- Database: Monitor Firestore usage in GCP Console
- Storage: Monitor GCS usage and costs

### Performance Optimization

- **Large Documents**: Automatically stored in Cloud Storage when > 500KB
- **Session Management**: ADK sessions timeout after 2 hours
- **Conversation Cleanup**: Old conversations archived after 30 days

## 🔒 Security

- **Authentication**: Hardcoded credentials (replace with OAuth in production)
- **API Security**: Bearer token authentication
- **File Upload**: Restricted file types and size limits
- **Cloud Authentication**: Application Default Credentials (ADC) - no JSON keys stored
- **Cloud Storage**: Private bucket with IAM-based access control

## 📝 License

This project is proprietary software for IntelliSurf AI RFP Research Platform.

## 🆘 Support

For technical support or questions:
1. Check the troubleshooting section above
2. Review logs in `/logs` directory
3. Contact the development team

---

**Version**: 1.0.0  
**Last Updated**: January 2025
