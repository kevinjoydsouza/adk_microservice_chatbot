#!/usr/bin/env python3
"""
Firestore Setup Script for ADK Chatbot
Quick setup script for Vertex AI credentials and database initialization.
"""

import os
import json
import asyncio
from pathlib import Path
from firestore_manager import FirestoreManager


def setup_vertex_ai_credentials():
    """Setup Vertex AI credentials interactively."""
    print("🔐 Vertex AI Credentials Setup")
    print("=" * 50)
    
    # Check if credentials already exist
    creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if creds_path and os.path.exists(creds_path):
        print(f"✅ Credentials already configured: {creds_path}")
        return True
    
    print("\nChoose authentication method:")
    print("1. Service Account Key File (Recommended for production)")
    print("2. Application Default Credentials (Development)")
    print("3. Vertex AI Workbench (Already authenticated)")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        return setup_service_account()
    elif choice == "2":
        return setup_adc()
    elif choice == "3":
        print("✅ Using Vertex AI Workbench credentials")
        return True
    else:
        print("❌ Invalid choice")
        return False


def setup_service_account():
    """Setup service account credentials."""
    print("\n📋 Service Account Setup")
    print("1. Go to Google Cloud Console > IAM & Admin > Service Accounts")
    print("2. Create new service account: 'firestore-chatbot'")
    print("3. Grant roles: 'Firestore User' and 'Firestore Service Agent'")
    print("4. Create and download JSON key file")
    
    key_path = input("\nEnter path to service account key file: ").strip()
    
    if not os.path.exists(key_path):
        print(f"❌ File not found: {key_path}")
        return False
    
    # Validate JSON format
    try:
        with open(key_path, 'r') as f:
            key_data = json.load(f)
        
        if 'project_id' not in key_data:
            print("❌ Invalid service account key file")
            return False
        
        # Set environment variable
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = key_path
        
        # Create .env file
        env_content = f"""# Firestore Configuration
GOOGLE_APPLICATION_CREDENTIALS={key_path}
GOOGLE_CLOUD_PROJECT={key_data['project_id']}
ADK_BASE_URL=http://localhost:8000
BACKEND_URL=http://localhost:8080
"""
        
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print(f"✅ Credentials configured for project: {key_data['project_id']}")
        print(f"✅ Created .env file")
        return True
        
    except json.JSONDecodeError:
        print("❌ Invalid JSON file")
        return False


def setup_adc():
    """Setup Application Default Credentials."""
    print("\n🔧 Application Default Credentials Setup")
    print("Run these commands in your terminal:")
    print()
    print("gcloud auth application-default login")
    print("gcloud config set project YOUR_PROJECT_ID")
    print()
    
    project_id = input("Enter your Google Cloud Project ID: ").strip()
    
    if not project_id:
        print("❌ Project ID is required")
        return False
    
    # Create .env file
    env_content = f"""# Firestore Configuration
GOOGLE_CLOUD_PROJECT={project_id}
ADK_BASE_URL=http://localhost:8000
BACKEND_URL=http://localhost:8080
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print(f"✅ Created .env file for project: {project_id}")
    print("⚠️ Make sure to run 'gcloud auth application-default login' before using")
    return True


async def setup_firestore_database():
    """Setup Firestore database with collections."""
    print("\n🗄️ Firestore Database Setup")
    print("=" * 50)
    
    # Check connection first
    manager = FirestoreManager(use_emulator=False)
    
    print("Testing Firestore connection...")
    if not await manager.test_connection():
        print("❌ Cannot connect to Firestore. Check your credentials.")
        return False
    
    print("\nSetting up collections...")
    await manager.setup_collections()
    
    print("\nCreating indexes (you may need to create these manually in Console)...")
    print_index_commands()
    
    return True


def print_index_commands():
    """Print Firestore index creation commands."""
    print("\n📊 Required Firestore Indexes")
    print("Run these commands in Google Cloud Console or CLI:")
    print()
    
    indexes = [
        {
            "collection": "conversations",
            "fields": [
                {"field": "user_id", "order": "ASCENDING"},
                {"field": "updated_at", "order": "DESCENDING"}
            ]
        },
        {
            "collection": "conversations", 
            "fields": [
                {"field": "agent_type", "order": "ASCENDING"},
                {"field": "status", "order": "ASCENDING"},
                {"field": "updated_at", "order": "DESCENDING"}
            ]
        },
        {
            "collection": "messages",
            "fields": [
                {"field": "conversation_id", "order": "ASCENDING"},
                {"field": "timestamp", "order": "ASCENDING"}
            ]
        },
        {
            "collection": "document_requests",
            "fields": [
                {"field": "user_id", "order": "ASCENDING"},
                {"field": "processing_status.created_at", "order": "DESCENDING"}
            ]
        },
        {
            "collection": "adk_sessions",
            "fields": [
                {"field": "user_id", "order": "ASCENDING"},
                {"field": "last_accessed", "order": "DESCENDING"}
            ]
        }
    ]
    
    for i, index in enumerate(indexes, 1):
        print(f"{i}. Collection: {index['collection']}")
        for field in index['fields']:
            print(f"   Field: {field['field']} ({field['order']})")
        print()


def create_sample_schemas():
    """Create sample schema files for new collections."""
    print("\n📝 Creating sample schema templates...")
    
    # RFP Agent schema
    rfp_schema = {
        "id": "rfp_req_sample",
        "user_id": "user_123",
        "agent_type": "rfp-generation",
        "project_details": {
            "project_name": "Sample AI Project",
            "opportunity_id": "opp_sample",
            "client_email": "client@example.com",
            "deadline": "2024-12-31T23:59:59Z"
        },
        "rfp_config": {
            "sections": ["executive_summary", "technical_approach"],
            "format": "pdf",
            "length": "detailed"
        },
        "created_at": "2024-01-01T00:00:00Z",
        "status": "pending"
    }
    
    # Custom agent schema
    custom_agent_schema = {
        "id": "custom_agent_sample",
        "user_id": "user_123", 
        "agent_name": "custom-research-agent",
        "agent_config": {
            "model": "gemini-2.5-pro",
            "temperature": 0.7,
            "system_prompt": "You are a specialized research assistant..."
        },
        "created_at": "2024-01-01T00:00:00Z",
        "status": "active"
    }
    
    # Save schema templates
    schemas_dir = Path("firestore_schemas")
    schemas_dir.mkdir(exist_ok=True)
    
    with open(schemas_dir / "rfp_requests.json", 'w') as f:
        json.dump(rfp_schema, f, indent=2)
    
    with open(schemas_dir / "custom_agents.json", 'w') as f:
        json.dump(custom_agent_schema, f, indent=2)
    
    print(f"✅ Created schema templates in {schemas_dir}/")


def main():
    """Main setup flow."""
    print("🚀 ADK Chatbot Firestore Setup")
    print("=" * 50)
    
    # Step 1: Setup credentials
    print("\nStep 1: Authentication Setup")
    if not setup_vertex_ai_credentials():
        print("❌ Credentials setup failed")
        return
    
    # Step 2: Setup database
    print("\nStep 2: Database Setup")
    try:
        success = asyncio.run(setup_firestore_database())
        if not success:
            print("❌ Database setup failed")
            return
    except Exception as e:
        print(f"❌ Database setup error: {e}")
        return
    
    # Step 3: Create schema templates
    print("\nStep 3: Schema Templates")
    create_sample_schemas()
    
    print("\n🎉 Setup Complete!")
    print("\nNext steps:")
    print("1. Review firestore_readme.md for detailed operations")
    print("2. Create indexes in Google Cloud Console (commands shown above)")
    print("3. Test with: python firestore_manager.py analytics")
    print("4. Start your application: python main.py")


if __name__ == "__main__":
    main()
