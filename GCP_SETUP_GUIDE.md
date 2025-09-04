# GCP Project Setup Guide for ADK Chatbot Firestore Database

## 📋 Required Files to Update

Once your GCP project is available, you need to update the following files with your project details:

### 1. **`.env` file** (Primary Configuration)
Create this file from `.env.template` and update these values:

```bash
# Google Cloud & Vertex AI
GOOGLE_CLOUD_PROJECT=your-actual-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=path/to/your-service-account.json
GOOGLE_API_KEY=your-actual-gemini-api-key

# Firestore Configuration
FIRESTORE_DATABASE_ID=(default)
USE_FIRESTORE_EMULATOR=false

# Production Storage
GOOGLE_CLOUD_STORAGE_BUCKET=your-project-id-storage
```

### 2. **Service Account JSON File**
Download from GCP Console and place in your project directory:
- File name: `service-account.json` (or your preferred name)
- Update `GOOGLE_APPLICATION_CREDENTIALS` path in `.env` to point to this file

## 🚀 Step-by-Step Setup Instructions

### Step 1: GCP Project Preparation

1. **Enable Required APIs** in GCP Console:
   ```bash
   gcloud services enable firestore.googleapis.com
   gcloud services enable storage-api.googleapis.com
   gcloud services enable aiplatform.googleapis.com
   ```

2. **Create Service Account**:
   - Go to IAM & Admin > Service Accounts
   - Create new service account: `adk-chatbot-service`
   - Grant these roles:
     - `Firestore User`
     - `Firestore Service Agent`
     - `Storage Admin`
     - `AI Platform User`

3. **Download Service Account Key**:
   - Generate JSON key for the service account
   - Save as `service-account.json` in your project root

### Step 2: Update Configuration Files

1. **Copy environment template**:
   ```bash
   cp .env.template .env
   ```

2. **Edit `.env` file** with your actual values:
   ```bash
   # Replace these with your actual values
   GOOGLE_CLOUD_PROJECT=your-project-id-here
   GOOGLE_APPLICATION_CREDENTIALS=./service-account.json
   GOOGLE_API_KEY=your-gemini-api-key-here
   GOOGLE_CLOUD_STORAGE_BUCKET=your-project-id-storage
   ```

### Step 3: Create Firestore Database

Choose one of these methods:

#### Option A: Using the new comprehensive script (Recommended)
```bash
python firestore_collection_manager.py create-all --project-id your-project-id
```

#### Option B: Using the existing setup script
```bash
python create_firestore_database.py --project-id your-project-id --action create
```

#### Option C: Using the setup wizard
```bash
python setup_firestore.py
```

### Step 4: Verify Setup

1. **Test connection**:
   ```bash
   python firestore_collection_manager.py validate --project-id your-project-id
   ```

2. **List collections**:
   ```bash
   python firestore_collection_manager.py list --project-id your-project-id
   ```

## 📁 File Locations Summary

| File | Purpose | What to Update |
|------|---------|----------------|
| `.env` | Main configuration | Project ID, credentials path, API keys |
| `service-account.json` | GCP authentication | Download from GCP Console |
| `config.py` | Collection schemas | No changes needed (already configured) |

## 🔧 Configuration Values Needed

### From GCP Console:
- **Project ID**: Found in GCP Console dashboard
- **Service Account JSON**: Download from IAM & Admin > Service Accounts
- **Gemini API Key**: From Google AI Studio or GCP Console

### Generated/Default Values:
- **Storage Bucket**: `{your-project-id}-storage` (will be created automatically)
- **Firestore Database**: `(default)` (will be created automatically)
- **Location**: `us-central1` (recommended)

## 🏗️ Collections That Will Be Created

The setup will create these Firestore collections with sample data:

1. **conversations** - Chat conversations with agent metadata
2. **messages** - Individual chat messages with attachments
3. **document_requests** - RFP and document generation requests
4. **adk_sessions** - Persistent ADK session storage
5. **user_profiles** - User preferences and analytics
6. **system_metadata** - Application configuration

## 🔍 Verification Commands

After setup, verify everything works:

```bash
# Check all collections exist
python firestore_collection_manager.py list

# Validate collection structure
python firestore_collection_manager.py validate

# Test the main application
python main.py

# Test Streamlit frontend
streamlit run streamlit_app.py
```

## 🚨 Troubleshooting

### Common Issues:

1. **Authentication Error**:
   - Verify service account JSON path in `.env`
   - Check service account has correct permissions

2. **Project Not Found**:
   - Verify `GOOGLE_CLOUD_PROJECT` in `.env`
   - Ensure Firestore API is enabled

3. **Permission Denied**:
   - Check service account roles
   - Verify billing is enabled on GCP project

### Debug Commands:

```bash
# Test authentication
gcloud auth application-default login
gcloud config set project your-project-id

# Verify environment variables
python -c "import os; print(os.getenv('GOOGLE_CLOUD_PROJECT'))"

# Test Firestore connection
python -c "from google.cloud import firestore; db = firestore.Client(); print('Connected successfully')"
```

## 📞 Support

If you encounter issues:
1. Check the logs in terminal output
2. Verify all environment variables are set correctly
3. Ensure GCP billing is enabled
4. Check service account permissions in GCP Console

---

## 🐳 Docker Deployment

### Three-Service Architecture

The system deploys as three services:
1. **Backend Service** (Port 8080) - FastAPI + ADK Server (Port 8000)
2. **Frontend Service** (Port 8501) - Streamlit UI
3. **Firestore Emulator** (Port 8088) - For development

### Quick Start with Docker

```bash
# 1. Set environment variables
export GOOGLE_API_KEY="your-gemini-api-key"
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_STORAGE_BUCKET="your-bucket-name"
export USE_GCS_FOR_UPLOADS="true"

# 2. Place service account key
cp /path/to/your/service-account.json ./service-account.json

# 3. Build and run all services
docker-compose up --build

# 4. Access the application
# - Streamlit UI: http://localhost:8501
# - FastAPI Backend: http://localhost:8080
# - ADK Server: http://localhost:8000
# - Firestore Emulator: http://localhost:8088
```

### Production Deployment

For production, update `docker-compose.yml`:

```yaml
# Remove firestore emulator service
# Update environment variables:
environment:
  - USE_FIRESTORE_EMULATOR=false
  - FIRESTORE_EMULATOR_HOST=""
```

### Health Checks

All services include health checks:
- Backend: `curl http://localhost:8080/health`
- Frontend: `curl http://localhost:8501/_stcore/health`
- Services auto-restart on failure

### Volume Mounts

- `./uploads` → `/app/uploads` (local file storage)
- `./teamcentre_mock` → `/app/teamcentre_mock` (RFP data)
- `./service-account.json` → `/app/service-account.json` (GCP credentials)

---

**Next Steps**: After successful setup, you can start using the RFP Research Agent and Academic Research features with full Firestore persistence and cloud storage!
