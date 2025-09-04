"""
Central configuration file for IntelliSurf AI Firestore database and application settings.
"""

import os
from typing import Dict, List, Any

# ================================
# FIRESTORE CONFIGURATION
# ================================

# Collection Names with Version Suffix
# Note: Firestore has a 1MB document size limit. Large content should be split across multiple documents
# or stored in Cloud Storage with references in Firestore.
COLLECTIONS = {
    "conversations": "conversations_v1",
    "messages": "messages_v1", 
    "document_requests": "document_requests_v1",
    "adk_sessions": "adk_sessions_v1",
    "user_profiles": "user_profiles_v1",
    "system_metadata": "system_metadata_v1"
}

# To add a new collection:
# 1. Add the collection name to COLLECTIONS dict above
# 2. Add the schema definition to COLLECTION_SCHEMAS below
# 3. Run: python create_firestore_database.py --project-id your-project --action create

# Collection Schemas and Sample Data
COLLECTION_SCHEMAS = {
    "conversations": {
        "fields": {
            "id": "string",
            "user_id": "string", 
            "title": "string",
            "created_at": "timestamp",
            "updated_at": "timestamp",
            "message_count": "number",
            "tags": "array",
            "metadata": "map"
        },
        "sample_data": {
            "id": "conv_sample_001",
            "user_id": "user_demo",
            "title": "IntelliSurf Research Demo",
            "message_count": 2,
            "tags": ["research", "demo"],
            "metadata": {"model": "intellisurf_research_agent", "session_type": "adk"}
        }
    },
    "messages": {
        "fields": {
            "id": "string",
            "conversation_id": "string",
            "role": "string",
            "content": "string",  # WARNING: Keep under 1MB. For large content, use content_chunks subcollection
            "timestamp": "timestamp",
            "metadata": "map"
        },
        "sample_data": {
            "id": "msg_sample_001",
            "conversation_id": "conv_sample_001",
            "role": "user",
            "content": "What are the latest trends in AI research?",
            "metadata": {"attachments": [], "model": "intellisurf_research_agent", "content_size": 42}
        },
        "size_considerations": {
            "max_document_size": "1MB",
            "large_content_strategy": "Use subcollections or Cloud Storage references",
            "recommended_content_limit": "800KB to allow metadata overhead"
        }
    },
    "document_requests": {
        "fields": {
            "request_id": "string",
            "user_id": "string",
            "document_type": "string",
            "title": "string",
            "description": "string",
            "status": "string",
            "created_at": "timestamp",
            "updated_at": "timestamp",
            "metadata": "map"
        },
        "sample_data": {
            "request_id": "doc_req_001",
            "user_id": "user_demo", 
            "document_type": "rfp",
            "title": "AI Implementation RFP",
            "description": "Request for proposal for AI system implementation",
            "status": "pending",
            "metadata": {"priority": "high", "department": "IT"}
        }
    },
    "adk_sessions": {
        "fields": {
            "session_id": "string",
            "user_id": "string",
            "agent_name": "string",
            "status": "string",
            "created_at": "timestamp",
            "last_activity": "timestamp",
            "memory_tier": "string",
            "session_data": "map"
        },
        "sample_data": {
            "session_id": "adk_session_001",
            "user_id": "user_demo",
            "agent_name": "intellisurf_research_agent", 
            "status": "active",
            "memory_tier": "hot",
            "session_data": {"context": "research_analysis", "conversation_count": 5}
        }
    },
    "user_profiles": {
        "fields": {
            "user_id": "string",
            "email": "string",
            "name": "string",
            "preferences": "map",
            "created_at": "timestamp",
            "last_login": "timestamp"
        },
        "sample_data": {
            "user_id": "user_demo",
            "email": "demo@intellisurf.ai",
            "name": "Demo User",
            "preferences": {"default_agent": "intellisurf_research_agent", "theme": "light"}
        }
    },
    "system_metadata": {
        "fields": {
            "key": "string",
            "value": "string",
            "category": "string",
            "updated_at": "timestamp"
        },
        "sample_data": {
            "key": "app_version",
            "value": "1.0.0",
            "category": "system"
        }
    }
}

# ================================
# VERTEX AI CONFIGURATION  
# ================================

# Vertex AI Settings
VERTEX_AI_CONFIG = {
    "project_id": os.getenv("GOOGLE_CLOUD_PROJECT", ""),
    "location": os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
    "credentials_path": os.getenv("GOOGLE_APPLICATION_CREDENTIALS", ""),
    "service_account_key": os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY", "")
}

# ================================
# APPLICATION CONFIGURATION
# ================================

# API Configuration
API_CONFIG = {
    "backend_url": os.getenv("BACKEND_URL", "http://localhost:8080"),
    "adk_base_url": os.getenv("ADK_BASE_URL", "http://localhost:8000"),
    "frontend_port": int(os.getenv("FRONTEND_PORT", "8501")),
    "backend_port": int(os.getenv("BACKEND_PORT", "8080")),
    "adk_port": int(os.getenv("ADK_PORT", "8000"))
}

# Firestore Configuration
FIRESTORE_CONFIG = {
    "emulator_host": os.getenv("FIRESTORE_EMULATOR_HOST", ""),
    "database_id": os.getenv("FIRESTORE_DATABASE_ID", "(default)"),
    "use_emulator": bool(os.getenv("USE_FIRESTORE_EMULATOR", "false").lower() == "true")
}

# AI Model Configuration
AI_CONFIG = {
    "google_api_key": os.getenv("GOOGLE_API_KEY", ""),
    "default_model": "gemini-2.5-pro",
    "adk_agent_name": "intellisurf_research_agent",
    "max_tokens": int(os.getenv("MAX_TOKENS", "8192")),
    "temperature": float(os.getenv("TEMPERATURE", "0.7"))
}

# File Upload Configuration
UPLOAD_CONFIG = {
    "max_file_size": int(os.getenv("MAX_FILE_SIZE", "10485760")),  # 10MB
    "allowed_extensions": [".pdf", ".doc", ".docx", ".txt", ".csv", ".json", ".jpg", ".png", ".gif", ".webp"],
    "upload_directory": os.getenv("UPLOAD_DIRECTORY", "./uploads")
}

# Production Storage Configuration
PRODUCTION_STORAGE = {
    "bucket_name": os.getenv('GOOGLE_CLOUD_STORAGE_BUCKET', 'intellisurf-ai-storage'),
    "content_size_threshold": int(os.getenv("CONTENT_SIZE_THRESHOLD", "500000")),  # 500KB
    "use_cloud_storage": bool(os.getenv("USE_CLOUD_STORAGE", "true").lower() == "true"),
    "cleanup_days": int(os.getenv("CLEANUP_OLD_CONTENT_DAYS", "30"))
}

# Google Cloud Storage Configuration
GCS_CONFIG = {
    "bucket_name": os.getenv('GOOGLE_CLOUD_STORAGE_BUCKET', 'intellisurf-ai-storage'),
    "use_gcs_for_uploads": os.getenv('USE_GCS_FOR_UPLOADS', 'false').lower() == 'true'
}

# GCS Folder Structure
GCS_FOLDERS = {
    'uploads': 'uploads/',
    'rfp_documents': 'teamcentre_mock/opportunities/',
    'proposals': 'proposals/',
    'temp': 'temp/'
}

# Session Management
SESSION_CONFIG = {
    "adk_session_timeout": int(os.getenv("ADK_SESSION_TIMEOUT", "7200")),  # 2 hours
    "conversation_timeout": int(os.getenv("CONVERSATION_TIMEOUT", "86400")),  # 24 hours
    "memory_tier_hot_duration": int(os.getenv("MEMORY_TIER_HOT", "7200")),  # 2 hours
    "memory_tier_warm_duration": int(os.getenv("MEMORY_TIER_WARM", "86400"))  # 24 hours
}

# ================================
# HELPER FUNCTIONS
# ================================

def add_new_collection(collection_key: str, collection_name: str, schema: Dict[str, Any]) -> str:
    """
    Generate code to add a new collection to the configuration.
    
    Args:
        collection_key: Key for the collection (e.g., 'analytics')
        collection_name: Actual collection name (e.g., 'user_analytics')
        schema: Schema definition with fields and sample_data
    
    Returns:
        String with code to add to config.py
    
    Example:
        code = add_new_collection('analytics', 'user_analytics', {
            'fields': {'id': 'string', 'event': 'string', 'timestamp': 'timestamp'},
            'sample_data': {'id': 'analytics_001', 'event': 'page_view'}
        })
    """
    return f'''
# Add this to COLLECTIONS dict:
"{collection_key}": "{collection_name}",

# Add this to COLLECTION_SCHEMAS dict:
"{collection_key}": {schema},
'''

# FIRESTORE SIZE LIMITATIONS AND BEST PRACTICES
FIRESTORE_LIMITS = {
    "max_document_size": "1MB (1,048,576 bytes)",
    "max_collection_id_length": "1500 bytes",
    "max_document_id_length": "1500 bytes", 
    "max_field_name_length": "1500 bytes",
    "max_field_value_size": "1MB",
    "max_array_elements": 20000,
    "max_subcollections_per_document": "No limit",
    "max_writes_per_second": "10,000 (sustained), 50,000 (peak)"
}

# Strategies for handling large content
LARGE_CONTENT_STRATEGIES = {
    "chunking": {
        "description": "Split large content into smaller documents in subcollections",
        "example": "messages/{msg_id}/content_chunks/{chunk_id}",
        "use_case": "Long AI responses, large documents"
    },
    "cloud_storage": {
        "description": "Store large files in Cloud Storage, reference URLs in Firestore",
        "example": "Store file in GCS, save gs://bucket/file.pdf URL in Firestore",
        "use_case": "File attachments, images, large documents"
    },
    "pagination": {
        "description": "Split data across multiple documents with pagination",
        "example": "conversation_messages_page_1, conversation_messages_page_2",
        "use_case": "Long conversation histories"
    },
    "compression": {
        "description": "Compress text content before storing",
        "example": "Use gzip compression for large text fields",
        "use_case": "Large text content that compresses well"
    }
}

def get_collection_name(collection_key: str) -> str:
    """Get collection name from config."""
    return COLLECTIONS.get(collection_key, collection_key)

def get_all_collections() -> List[str]:
    """Get list of all collection names."""
    return list(COLLECTIONS.values())

def get_collection_schema(collection_key: str) -> Dict[str, Any]:
    """Get schema for a specific collection."""
    return COLLECTION_SCHEMAS.get(collection_key, {})

def get_sample_data(collection_key: str) -> Dict[str, Any]:
    """Get sample data for a specific collection."""
    schema = COLLECTION_SCHEMAS.get(collection_key, {})
    return schema.get("sample_data", {})

def validate_config() -> Dict[str, bool]:
    """Validate configuration settings."""
    validation = {
        "vertex_ai_project": bool(VERTEX_AI_CONFIG["project_id"]),
        "vertex_ai_credentials": bool(VERTEX_AI_CONFIG["credentials_path"] or VERTEX_AI_CONFIG["service_account_key"]),
        "google_api_key": bool(AI_CONFIG["google_api_key"]),
        "firestore_config": bool(FIRESTORE_CONFIG["emulator_host"]) or not FIRESTORE_CONFIG["use_emulator"]
    }
    return validation

def get_env_template() -> str:
    """Generate .env template with all required variables."""
    template = """# IntelliSurf AI Configuration Template

# Google Cloud & Vertex AI
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
GOOGLE_API_KEY=your-gemini-api-key

# Firestore Configuration
FIRESTORE_DATABASE_ID=(default)
USE_FIRESTORE_EMULATOR=false
FIRESTORE_EMULATOR_HOST=localhost:8080

# API Configuration
BACKEND_URL=http://localhost:8080
ADK_BASE_URL=http://localhost:8000
FRONTEND_PORT=8501
BACKEND_PORT=8080
ADK_PORT=8000

# AI Configuration
MAX_TOKENS=8192
TEMPERATURE=0.7

# File Upload
MAX_FILE_SIZE=10485760
UPLOAD_DIRECTORY=./uploads

# Session Management
ADK_SESSION_TIMEOUT=7200
CONVERSATION_TIMEOUT=86400
MEMORY_TIER_HOT=7200
MEMORY_TIER_WARM=86400
"""
    return template

# ================================
# EXPORT MAIN CONFIG
# ================================

# Main configuration object
CONFIG = {
    "collections": COLLECTIONS,
    "schemas": COLLECTION_SCHEMAS,
    "vertex_ai": VERTEX_AI_CONFIG,
    "api": API_CONFIG,
    "firestore": FIRESTORE_CONFIG,
    "ai": AI_CONFIG,
    "upload": UPLOAD_CONFIG,
    "session": SESSION_CONFIG
}
