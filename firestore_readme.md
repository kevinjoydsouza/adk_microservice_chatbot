# Firestore Setup and Operations Guide

## ⚠️ Important: Firestore Size Limitations
- **Maximum document size**: 1MB (1,048,576 bytes)
- **Recommended content limit**: 800KB (to allow metadata overhead)
- **Large content strategy**: Use subcollections, Cloud Storage references, or content chunking
- See `firestore_collection_management.md` for detailed handling strategies

## 🚀 Quick Start

### Prerequisites
1. **Google Cloud Project** with Firestore enabled
2. **Vertex AI API** enabled
3. **Service Account** with Firestore Admin permissions
4. **Python dependencies** installed

### Installation & Setup

```bash
# 1. Install dependencies
pip install google-cloud-firestore google-auth

# 2. Set up authentication
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"
# OR for Vertex AI Workbench
gcloud auth application-default login

# 3. Set project ID
export GOOGLE_CLOUD_PROJECT="your-project-id"
```

## 🔧 Using the Firestore Manager

### Initialize Collections
```bash
# Create all collections with sample data
python firestore_manager.py setup --project-id your-project-id

# Use emulator for development
python firestore_manager.py setup --emulator
```

### Basic Operations

#### **View Analytics**
```bash
# System-wide analytics
python firestore_manager.py analytics

# User-specific analytics  
python firestore_manager.py analytics --user-id dev-user-123
```

#### **Database Maintenance**
```bash
# Clean up expired sessions and archive old conversations
python firestore_manager.py cleanup

# Create JSON backup
python firestore_manager.py backup --output backup_2024.json
```

#### **Document Request Management**
```bash
# Update document generation status (typically called by Cloud Functions)
python firestore_manager.py update-doc req_abc123 in_progress --progress 50 --details "Generating content"
python firestore_manager.py update-doc req_abc123 completed --progress 100 --details "PDF generated successfully"
python firestore_manager.py update-doc req_abc123 failed --details "Template not found"
```

## 📊 Collection Management

### Creating New Collections

#### **1. Define Schema in `models_enhanced.py`**
```python
class NewAgentRequest(BaseModel):
    id: str
    user_id: str
    agent_type: str
    request_data: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.now)
    status: str = "pending"
```

#### **2. Add to FirestoreManager**
```python
# In firestore_manager.py __init__
self.collections = {
    'conversations': 'conversations',
    'messages': 'messages',
    'document_requests': 'document_requests',
    'adk_sessions': 'adk_sessions', 
    'user_profiles': 'user_profiles',
    'system_metadata': 'system_metadata',
    'new_agent_requests': 'new_agent_requests'  # Add new collection
}

# Add setup method
async def _create_sample_new_agent_request(self):
    """Create sample new agent request."""
    sample_data = {
        "id": str(uuid.uuid4()),
        "user_id": "dev-user-123",
        "agent_type": "custom-agent",
        "request_data": {"config": "sample"},
        "created_at": datetime.now().isoformat(),
        "status": "pending"
    }
    
    self.db.collection(self.collections['new_agent_requests']).document(sample_data["id"]).set(sample_data)
    print("🤖 Created sample new agent request")
```

#### **3. Update Setup Method**
```python
async def setup_collections(self):
    """Create all collections with sample data."""
    print("🏗️ Setting up Firestore collections...")
    
    await self._create_sample_user_profile()
    await self._create_sample_conversation()
    await self._create_sample_document_request()
    await self._create_sample_adk_session()
    await self._create_sample_new_agent_request()  # Add this line
    await self._create_system_metadata()
    
    print("✅ All collections created successfully!")
```

### Modifying Collection Schema

#### **Adding New Fields**
```python
# Add new field to existing documents
async def add_field_to_collection(self, collection_name: str, field_name: str, default_value: Any):
    """Add new field to all documents in collection."""
    docs = self.db.collection(collection_name).stream()
    batch = self.db.batch()
    count = 0
    
    for doc in docs:
        batch.update(doc.reference, {field_name: default_value})
        count += 1
        
        if count % 500 == 0:  # Firestore batch limit
            batch.commit()
            batch = self.db.batch()
    
    if count % 500 != 0:
        batch.commit()
    
    print(f"✅ Added field '{field_name}' to {count} documents in {collection_name}")

# Usage
await manager.add_field_to_collection("conversations", "priority_level", "normal")
```

#### **Renaming Fields**
```python
async def rename_field(self, collection_name: str, old_field: str, new_field: str):
    """Rename field in all documents."""
    docs = self.db.collection(collection_name).stream()
    batch = self.db.batch()
    count = 0
    
    for doc in docs:
        data = doc.to_dict()
        if old_field in data:
            batch.update(doc.reference, {
                new_field: data[old_field],
                old_field: firestore.DELETE_FIELD
            })
            count += 1
            
            if count % 500 == 0:
                batch.commit()
                batch = self.db.batch()
    
    if count % 500 != 0:
        batch.commit()
    
    print(f"✅ Renamed '{old_field}' to '{new_field}' in {count} documents")
```

### Deleting Collections

#### **Safe Collection Deletion**
```python
async def delete_collection(self, collection_name: str, confirm: bool = False):
    """Safely delete a collection with confirmation."""
    if not confirm:
        print(f"⚠️ This will delete ALL data in '{collection_name}' collection!")
        print("Add --confirm flag to proceed")
        return
    
    docs = self.db.collection(collection_name).stream()
    batch = self.db.batch()
    count = 0
    
    for doc in docs:
        batch.delete(doc.reference)
        count += 1
        
        if count % 500 == 0:
            batch.commit()
            batch = self.db.batch()
    
    if count % 500 != 0:
        batch.commit()
    
    print(f"🗑️ Deleted {count} documents from '{collection_name}'")

# CLI usage
python firestore_manager.py delete-collection conversations --confirm
```

## 🔐 Vertex AI Credentials Setup

### **Option 1: Service Account (Recommended for Production)**

#### **1. Create Service Account**
```bash
# Create service account
gcloud iam service-accounts create firestore-chatbot \
    --display-name="Firestore Chatbot Service Account"

# Grant Firestore permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:firestore-chatbot@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/datastore.user"

# Create and download key
gcloud iam service-accounts keys create firestore-key.json \
    --iam-account=firestore-chatbot@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

#### **2. Configure Environment**
```bash
# Set credentials path
export GOOGLE_APPLICATION_CREDENTIALS="./firestore-key.json"
export GOOGLE_CLOUD_PROJECT="your-project-id"
```

### **Option 2: Application Default Credentials (Development)**
```bash
# Authenticate with your user account
gcloud auth application-default login

# Set project
gcloud config set project YOUR_PROJECT_ID
```

### **Option 3: Vertex AI Workbench (Cloud Environment)**
```python
# Credentials automatically available in Vertex AI
# No additional setup required
```

## 📋 Collection Configuration Guide

### **conversations** Collection

#### **Required Indexes:**
```javascript
// Create these indexes in Firestore Console
[
  {
    "collectionGroup": "conversations",
    "queryScope": "COLLECTION",
    "fields": [
      {"fieldPath": "user_id", "order": "ASCENDING"},
      {"fieldPath": "updated_at", "order": "DESCENDING"}
    ]
  },
  {
    "collectionGroup": "conversations", 
    "queryScope": "COLLECTION",
    "fields": [
      {"fieldPath": "agent_type", "order": "ASCENDING"},
      {"fieldPath": "status", "order": "ASCENDING"},
      {"fieldPath": "updated_at", "order": "DESCENDING"}
    ]
  }
]
```

#### **Security Rules:**
```javascript
// Firestore Security Rules
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Conversations - users can only access their own
    match /conversations/{conversationId} {
      allow read, write: if request.auth != null && 
                         resource.data.user_id == request.auth.uid;
    }
    
    // Messages - linked to conversation access
    match /messages/{messageId} {
      allow read, write: if request.auth != null &&
                         exists(/databases/$(database)/documents/conversations/$(resource.data.conversation_id)) &&
                         get(/databases/$(database)/documents/conversations/$(resource.data.conversation_id)).data.user_id == request.auth.uid;
    }
    
    // Document requests - user-scoped
    match /document_requests/{requestId} {
      allow read, write: if request.auth != null &&
                         resource.data.user_id == request.auth.uid;
    }
  }
}
```

### **document_requests** Collection

#### **Webhook Integration for Status Updates:**
```python
# Cloud Function example for document processing webhook
import functions_framework
from google.cloud import firestore

@functions_framework.http
def update_document_status(request):
    """Cloud Function to update document request status."""
    data = request.get_json()
    
    request_id = data.get('request_id')
    status = data.get('status')
    progress = data.get('progress', 0)
    document_url = data.get('document_url')
    
    db = firestore.Client()
    
    updates = {
        'processing_status.status': status,
        'processing_status.last_updated': datetime.now().isoformat(),
        'processing_status.progress_percentage': progress
    }
    
    if status == 'completed' and document_url:
        updates['output_details.document_url'] = document_url
        updates['processing_status.completed_at'] = datetime.now().isoformat()
    
    # Add webhook log
    webhook_log = {
        'timestamp': datetime.now().isoformat(),
        'status': status,
        'details': data.get('details', f'Status updated to {status}'),
        'source': 'document_service'
    }
    
    doc_ref = db.collection('document_requests').document(request_id)
    doc = doc_ref.get()
    
    if doc.exists:
        current_logs = doc.to_dict().get('webhook_logs', [])
        current_logs.append(webhook_log)
        updates['webhook_logs'] = current_logs
        
        doc_ref.update(updates)
        return {'success': True}
    
    return {'error': 'Request not found'}, 404
```

## 🛠️ Advanced Operations

### **Batch Operations**

#### **Bulk Data Import**
```python
async def import_conversations_from_json(self, json_file_path: str):
    """Import conversations from JSON backup."""
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    
    batch = self.db.batch()
    count = 0
    
    for collection_name, documents in data.items():
        for doc_id, doc_data in documents.items():
            doc_ref = self.db.collection(collection_name).document(doc_id)
            batch.set(doc_ref, doc_data)
            count += 1
            
            if count % 500 == 0:
                batch.commit()
                batch = self.db.batch()
    
    if count % 500 != 0:
        batch.commit()
    
    print(f"📥 Imported {count} documents")
```

#### **Data Migration**
```python
async def migrate_schema_v1_to_v2(self):
    """Migrate from old schema to new enhanced schema."""
    # Get all conversations with old schema
    docs = self.db.collection('conversations').stream()
    
    for doc in docs:
        data = doc.to_dict()
        
        # Add new fields with defaults
        updates = {}
        
        if 'agent_type' not in data:
            updates['agent_type'] = 'academic-research'
        
        if 'session_metadata' not in data:
            updates['session_metadata'] = {
                'adk_session_id': None,
                'last_activity': data.get('updated_at'),
                'total_tokens_used': 0,
                'agent_transitions': 0
            }
        
        if 'tags' not in data:
            updates['tags'] = []
        
        if 'status' not in data:
            updates['status'] = 'active'
        
        if updates:
            doc.reference.update(updates)
    
    print("🔄 Schema migration completed")
```

### **Performance Monitoring**

#### **Query Performance Analysis**
```python
async def analyze_query_performance(self):
    """Analyze query performance and suggest optimizations."""
    import time
    
    queries = [
        ("User conversations", lambda: self.db.collection('conversations')
         .where(filter=FieldFilter("user_id", "==", "dev-user-123"))
         .order_by("updated_at", direction=firestore.Query.DESCENDING)
         .limit(10)),
        
        ("Pending documents", lambda: self.db.collection('document_requests')
         .where(filter=FieldFilter("processing_status.status", "==", "pending"))),
        
        ("Active sessions", lambda: self.db.collection('adk_sessions')
         .where(filter=FieldFilter("status", "==", "active")))
    ]
    
    for query_name, query_func in queries:
        start_time = time.time()
        list(query_func().stream())
        end_time = time.time()
        
        print(f"⏱️ {query_name}: {(end_time - start_time)*1000:.2f}ms")
```

## 🔍 Collection-Specific Operations

### **conversations** Collection

#### **Create New Conversation**
```python
from enhanced_firestore_service import EnhancedFirestoreService
from models_enhanced import ConversationCreate, AgentType

service = EnhancedFirestoreService()

# Create conversation
conv_data = ConversationCreate(
    title="My Research Project",
    agent_type=AgentType.ACADEMIC_RESEARCH,
    tags=["machine-learning", "research"]
)

conversation_id = await service.create_conversation("user-123", conv_data)
print(f"Created conversation: {conversation_id}")
```

#### **Search Conversations**
```python
# Search by title/tags
results = await service.search_conversations(
    user_id="user-123",
    query="machine learning",
    agent_type=AgentType.ACADEMIC_RESEARCH,
    limit=5
)

for conv in results:
    print(f"📝 {conv.title} - {len(conv.messages)} messages")
```

### **document_requests** Collection

#### **Create Document Request**
```python
from models_enhanced import DocumentRequestCreate, DocumentRequestType, ProjectDetails, DocumentConfig

# Create RFP request
request_data = DocumentRequestCreate(
    request_type=DocumentRequestType.RFP,
    project_details=ProjectDetails(
        project_name="AI Research Platform",
        opportunity_id="opp_12345",
        client_email="client@company.com",
        deadline=datetime.now() + timedelta(days=30)
    ),
    document_config=DocumentConfig(
        template_type="technical_rfp",
        sections=["executive_summary", "technical_approach", "timeline"],
        format="pdf",
        length="detailed"
    ),
    conversation_id="conv_abc123",
    message_id="msg_xyz789"
)

request_id = await service.create_document_request("user-123", request_data)
print(f"Document request created: {request_id}")
```

#### **Monitor Document Processing**
```python
# Get user's document requests
pending_docs = await service.get_user_document_requests(
    user_id="user-123",
    status=DocumentStatus.PENDING
)

for doc_req in pending_docs:
    print(f"📄 {doc_req.project_details.project_name} - {doc_req.processing_status.status}")
    print(f"   Progress: {doc_req.processing_status.progress_percentage}%")
```

### **adk_sessions** Collection

#### **Backup ADK Session**
```python
# Backup active ADK session
session_state = {
    "context_history": [...],
    "agent_memory": {
        "research_focus": "machine_learning",
        "user_expertise": "intermediate"
    },
    "total_tokens": 1500
}

success = await service.backup_adk_session(
    session_id="adk_session_123",
    user_id="user-123", 
    agent_name="academic-research",
    session_state=session_state,
    conversation_id="conv_abc123"
)

if success:
    print("💾 Session backed up successfully")
```

#### **Restore ADK Session**
```python
# Restore hibernated session
restored_state = await service.restore_adk_session("adk_session_123", "user-123")

if restored_state:
    print("🔄 Session restored successfully")
    print(f"Context messages: {len(restored_state.get('context_history', []))}")
else:
    print("❌ Session not found or expired")
```

## 🔧 Database Maintenance Scripts

### **Daily Maintenance**
```python
# Add to firestore_manager.py
async def daily_maintenance(self):
    """Run daily maintenance tasks."""
    print("🔧 Starting daily maintenance...")
    
    # 1. Clean up expired sessions
    expired_count = await self.cleanup_expired_sessions()
    
    # 2. Compress old messages
    compressed_count = await self.compress_old_messages(days_old=7)
    
    # 3. Archive old conversations
    await self.archive_old_conversations(days_old=30)
    
    # 4. Update system analytics
    analytics = await self.get_system_analytics()
    
    self.db.collection('system_metadata').document('daily_stats').set({
        'date': datetime.now().isoformat(),
        'expired_sessions_cleaned': expired_count,
        'messages_compressed': compressed_count,
        'system_analytics': analytics
    })
    
    print("✅ Daily maintenance completed")

# CLI command
python firestore_manager.py maintenance --daily
```

### **Weekly Reports**
```python
async def generate_weekly_report(self):
    """Generate weekly usage report."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    # Query conversations created this week
    weekly_conversations = list(
        self.db.collection('conversations')
        .where(filter=FieldFilter("created_at", ">=", start_date.isoformat()))
        .where(filter=FieldFilter("created_at", "<=", end_date.isoformat()))
        .stream()
    )
    
    # Query document requests this week
    weekly_docs = list(
        self.db.collection('document_requests')
        .where(filter=FieldFilter("processing_status.created_at", ">=", start_date.isoformat()))
        .stream()
    )
    
    report = {
        'week_ending': end_date.isoformat(),
        'new_conversations': len(weekly_conversations),
        'document_requests': len(weekly_docs),
        'active_users': len(set(doc.to_dict()['user_id'] for doc in weekly_conversations))
    }
    
    print("📊 Weekly Report:")
    for key, value in report.items():
        print(f"  {key}: {value}")
    
    return report
```

## 🚨 Error Handling & Recovery

### **Connection Issues**
```python
async def test_firestore_connection(self):
    """Test Firestore connectivity."""
    try:
        # Try to read system metadata
        doc = self.db.collection('system_metadata').document('config').get()
        
        if doc.exists:
            print("✅ Firestore connection successful")
            return True
        else:
            print("⚠️ Connected but no system metadata found")
            print("Run 'python firestore_manager.py setup' to initialize")
            return False
            
    except Exception as e:
        print(f"❌ Firestore connection failed: {e}")
        print("Check your credentials and project ID")
        return False

# CLI command
python firestore_manager.py test-connection
```

### **Data Recovery**
```python
async def recover_corrupted_data(self):
    """Recover from data corruption."""
    print("🔧 Starting data recovery...")
    
    # 1. Validate all conversations have required fields
    conversations = self.db.collection('conversations').stream()
    fixed_count = 0
    
    for doc in conversations:
        data = doc.to_dict()
        updates = {}
        
        # Check required fields
        required_fields = {
            'status': 'active',
            'agent_type': 'academic-research',
            'tags': [],
            'session_metadata': {
                'adk_session_id': None,
                'last_activity': data.get('updated_at'),
                'total_tokens_used': 0
            }
        }
        
        for field, default_value in required_fields.items():
            if field not in data:
                updates[field] = default_value
        
        if updates:
            doc.reference.update(updates)
            fixed_count += 1
    
    print(f"🔧 Fixed {fixed_count} corrupted conversations")
```

## 📈 Monitoring & Alerts

### **Usage Monitoring**
```python
async def check_usage_limits(self, user_id: str):
    """Check if user is approaching limits."""
    profile = await self.get_or_create_user_profile(user_id, f"{user_id}@example.com")
    
    warnings = []
    
    # Check token usage
    token_usage_pct = (profile.subscription.tokens_used_this_month / 
                      profile.subscription.token_limit) * 100
    
    if token_usage_pct > 80:
        warnings.append(f"Token usage: {token_usage_pct:.1f}% of limit")
    
    # Check document requests
    doc_usage_pct = (profile.subscription.document_requests_this_month / 
                    profile.subscription.document_limit) * 100
    
    if doc_usage_pct > 80:
        warnings.append(f"Document requests: {doc_usage_pct:.1f}% of limit")
    
    return warnings
```

## 🎯 CLI Command Reference

### **Setup Commands**
```bash
# Initialize database
python firestore_manager.py setup --project-id your-project-id

# Test connection
python firestore_manager.py test-connection

# Setup with emulator
python firestore_manager.py setup --emulator
```

### **Collection Management**

### Adding New Collections
1. **Update config.py**: Add collection name to `COLLECTIONS` dict and schema to `COLLECTION_SCHEMAS`
2. **Run setup script**: `python create_firestore_database.py --project-id your-project --action create`
3. **See detailed guide**: `firestore_collection_management.md`

### Create Collections
```bash
python firestore_manager.py create-collection --name analytics --fields "event_id:string,user_id:string,timestamp:timestamp"
```

### List Collections
```bash
python firestore_manager.py list-collections
```

### **Data Operations**
```bash
# View analytics
python firestore_manager.py analytics
python firestore_manager.py analytics --user-id user-123

# Backup database
python firestore_manager.py backup --output backup.json

# Import from backup
python firestore_manager.py import --file backup.json

# Clean up old data
python firestore_manager.py cleanup
```

### **Collection Management**
```bash
# Add field to collection
python firestore_manager.py add-field conversations priority_level normal

# Rename field
python firestore_manager.py rename-field conversations model_config model_settings

# Delete collection (with confirmation)
python firestore_manager.py delete-collection old_collection --confirm
```

### **Document Processing**
```bash
# Update document status
python firestore_manager.py update-doc req_123 in_progress --progress 50
python firestore_manager.py update-doc req_123 completed --progress 100

# List pending documents
python firestore_manager.py list-pending-docs

# Generate weekly report
python firestore_manager.py weekly-report
```

### **Maintenance**
```bash
# Daily maintenance
python firestore_manager.py maintenance --daily

# Compress old data
python firestore_manager.py compress --days-old 7

# Migrate schema
python firestore_manager.py migrate --from-version 1 --to-version 2
```

## 🔄 Integration with Your Backend

### **Using Enhanced Service in FastAPI**
```python
# In main.py
from services.enhanced_firestore_service import EnhancedFirestoreService

# Initialize service
enhanced_firestore = EnhancedFirestoreService(
    use_emulator=os.getenv("FIRESTORE_EMULATOR_HOST") is not None,
    project_id=os.getenv("GOOGLE_CLOUD_PROJECT")
)

# Create document request endpoint
@app.post("/create-document-request")
async def create_document_request(request: DocumentRequestCreate, user = Depends(get_current_user)):
    request_id = await enhanced_firestore.create_document_request(user.id, request)
    
    # Trigger document generation service
    # ... call external document service with request_id
    
    return {"request_id": request_id, "status": "pending"}
```

### **Webhook Endpoint for Status Updates**
```python
@app.post("/webhook/document-status")
async def document_status_webhook(request: DocumentStatusUpdate, request_id: str):
    """Webhook endpoint for document processing updates."""
    await enhanced_firestore.update_document_status(request_id, request)
    return {"success": True}
```

## 🎯 Best Practices

### **Performance**
- Use composite indexes for complex queries
- Batch operations for bulk updates
- Implement pagination for large result sets
- Cache frequently accessed data

### **Security**
- Never expose service account keys in code
- Use Firestore security rules for data isolation
- Validate all user inputs
- Implement rate limiting

### **Scalability**
- Design for horizontal scaling
- Use subcollections for hierarchical data
- Implement data archiving strategies
- Monitor storage costs

### **Reliability**
- Implement retry logic for transient failures
- Use transactions for critical operations
- Regular backups and disaster recovery
- Monitor query performance

This guide provides everything you need to manage your Firestore database effectively, from basic setup to advanced operations and monitoring.
