import streamlit as st
import requests
import json
from datetime import datetime
import os
from dotenv import load_dotenv
from auth import require_auth, is_authenticated, logout

# Load environment variables from .env file
load_dotenv()

# Configure page
st.set_page_config(
    page_title="IntelliSurf AI - RFP Research Platform",
    page_icon="📋",
    layout="wide"
)

# Require authentication
require_auth()

# Backend API URL
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8080")
AUTH_TOKEN = "dev-token-123"

# Headers for API requests
headers = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json"
}

def get_conversations():
    """Get user conversations"""
    try:
        response = requests.get(f"{BACKEND_URL}/conversations", headers=headers)
        if response.status_code == 200:
            conversations = response.json()
            # Debug: print to see what we're getting
            print(f"Fetched {len(conversations)} conversations")
            return conversations
        else:
            print(f"Error fetching conversations: {response.status_code} - {response.text}")
            # If backend is not running, try to start it
            if response.status_code == 404 or "Connection" in str(response.text):
                st.error("Backend server not running. Please start with: python main.py")
            return []
    except requests.exceptions.ConnectionError as e:
        print(f"Backend connection error: {e}")
        st.error("Cannot connect to backend server. Please start with: python main.py")
        return []
    except Exception as e:
        print(f"Exception fetching conversations: {e}")
        return []

def upload_file(uploaded_file):
    """Upload file to backend or local storage as fallback"""
    try:
        # Try backend upload first
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        response = requests.post(f"{BACKEND_URL}/upload", headers={"Authorization": f"Bearer {AUTH_TOKEN}"}, files=files)
        if response.status_code == 200:
            return response.json()
        else:
            # Fallback to local storage
            return upload_file_locally(uploaded_file)
    except Exception as e:
        # Fallback to local storage if backend unavailable
        return upload_file_locally(uploaded_file)

def upload_file_locally(uploaded_file):
    """Upload file to local storage when backend unavailable"""
    try:
        import uuid
        # Create local uploads directory
        local_upload_dir = "local_uploads"
        os.makedirs(local_upload_dir, exist_ok=True)
        
        # Generate unique filename
        file_extension = os.path.splitext(uploaded_file.name)[1]
        unique_filename = f"{uuid.uuid4().hex[:12]}{file_extension}"
        file_path = os.path.join(local_upload_dir, unique_filename)
        
        # Save file locally
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getvalue())
        
        # Return local file URL
        return {
            "filename": uploaded_file.name,
            "file_url": f"/local_uploads/{unique_filename}",
            "file_size": len(uploaded_file.getvalue())
        }
    except Exception as e:
        st.error(f"Local upload error: {str(e)}")
        return None



def send_rfp_chat_message(user_input, conversation_id=None, session_id=None, streaming=False, attachments=None):
    """Send chat message to RFP Research Agent with optional streaming"""
    try:
        payload = {
            "user_input": user_input,
            "conversation_id": conversation_id,
            "session_id": session_id,
            "streaming": streaming,
            "attachments": attachments or []
        }
        
        if streaming:
            # Handle streaming response
            response = requests.post(f"{BACKEND_URL}/rfp-chat", headers=headers, json=payload, stream=True)
            if response.status_code == 200:
                return response
            else:
                return None
        else:
            # Handle regular response
            response = requests.post(f"{BACKEND_URL}/rfp-chat", headers=headers, json=payload)
            if response.status_code == 200:
                return response.json()
            else:
                return None
    except Exception as e:
        return None

def process_streaming_response(response, activity_placeholder):
    """Process streaming response and update activity display"""
    import json
    
    final_result = None
    current_step = "Connecting to RFP Research Agent..."
    
    try:
        for line in response.iter_lines():
            if line:
                line_text = line.decode('utf-8')
                if line_text.startswith('data: '):
                    try:
                        data = json.loads(line_text[6:])  # Remove 'data: ' prefix
                        
                        if data['type'] == 'thinking':
                            # Update thinking display with real step
                            current_step = data['step']
                            progress = data.get('progress', 50)
                            
                            with activity_placeholder.container():
                                st.write("**🤖 RFP Research Agent**")
                                st.write(f"🔄 {current_step}")
                                if progress:
                                    st.progress(progress / 100, text=f"{progress}%")
                        
                        elif data['type'] == 'response':
                            # Final response received
                            final_result = {
                                'response': data['content'],
                                'session_id': data['session_id'],
                                'conversation_id': data['conversation_id']
                            }
                            # Clear the thinking display
                            activity_placeholder.empty()
                            break
                        
                        elif data['type'] == 'error':
                            # Error occurred
                            final_result = {'error': True, 'response': data['message']}
                            activity_placeholder.empty()
                            break
                            
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        final_result = {'error': True, 'response': f"Streaming error: {str(e)}"}
        activity_placeholder.empty()
    
    return final_result

def generate_local_response(user_input, attachments=None):
    """Generate AI response using direct Gemini API when backend unavailable"""
    try:
        import google.generativeai as genai
        
        # Configure Gemini API
        GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        if not GOOGLE_API_KEY:
            return "Please set GOOGLE_API_KEY environment variable to use AI responses."
        
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Prepare message with attachments
        message_parts = [user_input]
        
        if attachments:
            for attachment_url in attachments:
                try:
                    # Handle local file paths
                    if attachment_url.startswith('/local_uploads/'):
                        file_path = attachment_url.replace('/local_uploads/', 'local_uploads/')
                    else:
                        file_path = attachment_url.replace('/uploads/', 'uploads/')
                    
                    if os.path.exists(file_path):
                        # Handle text files
                        if file_path.lower().endswith(('.txt', '.md', '.py', '.js', '.html', '.css')):
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            message_parts.append(f"\n\nFile content from {os.path.basename(file_path)}:\n{content}")
                        # Handle images and PDFs
                        elif file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.pdf')):
                            uploaded_file = genai.upload_file(file_path)
                            message_parts.append(uploaded_file)
                except Exception as e:
                    message_parts.append(f"\n\nNote: Could not process attachment {os.path.basename(attachment_url)}")
        
        # Generate response
        response = model.generate_content(message_parts)
        return response.text
        
    except Exception as e:
        return f"AI Error: {str(e)}. Please check your GOOGLE_API_KEY environment variable."

def get_conversation_details(conversation_id):
    """Get conversation with messages"""
    try:
        response = requests.get(f"{BACKEND_URL}/conversations/{conversation_id}", headers=headers)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

# Local conversation storage - persistent file-based
def load_local_conversations():
    """Load conversations from local storage directory"""
    conversations = {}
    local_conv_dir = "local_storage/conversations"
    os.makedirs(local_conv_dir, exist_ok=True)
    
    for filename in os.listdir(local_conv_dir):
        if filename.endswith('.json'):
            try:
                with open(f"{local_conv_dir}/{filename}", "r") as f:
                    conv_data = json.load(f)
                    # Ensure messages key exists
                    if "messages" not in conv_data:
                        conv_data["messages"] = []
                    conversations[conv_data["id"]] = conv_data
            except:
                continue
    return conversations

def save_local_conversation(conversation_data):
    """Save conversation to local storage directory"""
    local_conv_dir = "local_storage/conversations"
    os.makedirs(local_conv_dir, exist_ok=True)
    
    with open(f"{local_conv_dir}/{conversation_data['id']}.json", "w") as f:
        json.dump(conversation_data, f, indent=2)

def display_agent_activity(activity_tracker):
    """Display streaming agent activity like thinking models"""
    if not activity_tracker:
        return
    
    # Get current message and steps
    current_message = activity_tracker.get("message", "Processing...")
    steps = activity_tracker.get("steps", [])
    progress_percentage = activity_tracker.get("progress_percentage", 0)
    
    # Create a streaming display container
    with st.container():
        # Show current thinking step
        st.write("**🤖 RFP Research Agent**")
        
        # Stream completed and current steps
        for step in steps:
            status = step["status"]
            name = step["name"]
            description = step["description"]
            
            if status == "completed":
                st.write(f"✓ {name}")
            elif status == "in_progress":
                # Show streaming effect for current step
                st.write(f"🔄 {name}...")
                # Add a subtle progress indicator
                st.caption(f"*{description}*")
            elif status == "error":
                st.write(f"❌ {name}")
        
        # Show current status as streaming text
        if current_message:
            st.caption(f"💭 {current_message}")
        
        # Simple progress indicator
        if progress_percentage > 0:
            st.progress(progress_percentage / 100, text=f"{progress_percentage}%")

def stream_agent_steps(activity_placeholder, steps_to_show):
    """Stream agent steps one by one with delays"""
    import time
    
    for i, step_text in enumerate(steps_to_show):
        with activity_placeholder.container():
            st.write("**🤖 RFP Research Agent**")
            
            # Show all previous steps as completed
            for j in range(i):
                st.write(f"✓ {steps_to_show[j]}")
            
            # Show current step as in progress
            st.write(f"🔄 {step_text}...")
            
            # Add some thinking time
            time.sleep(1.0)
    
    # Final completion
    with activity_placeholder.container():
        st.write("**🤖 RFP Research Agent**")
        for step_text in steps_to_show:
            st.write(f"✓ {step_text}")
        st.success("Processing complete!")

# Initialize session state
if "local_conversations" not in st.session_state:
    st.session_state.local_conversations = load_local_conversations()
if "conversation_counter" not in st.session_state:
    st.session_state.conversation_counter = len(st.session_state.local_conversations) + 1

# Initialize session state
if "current_conversation_id" not in st.session_state:
    st.session_state.current_conversation_id = None
if "adk_session_id" not in st.session_state:
    st.session_state.adk_session_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []
# Always use RFP agent
st.session_state.use_rfp = True

# Header with logout
col1, col2 = st.columns([4, 1])
with col1:
    st.title("📋 IntelliSurf AI - RFP Research Platform")
    st.subheader("Intelligent RFP Research & Proposal Generation")
with col2:
    if st.button("🚪 Logout", key="logout_btn"):
        logout()

# Show current user and RFP agent info
col1, col2 = st.columns([3, 1])
with col2:
    st.info(f"👤 Logged in as: **{st.session_state.username}**")
    st.success("📋 RFP Research Agent Active")

# Sidebar for conversations
with st.sidebar:
    st.markdown("### 💬 Conversations")
    
    if st.button("➕ New Conversation"):
        st.session_state.current_conversation_id = None
        st.session_state.adk_session_id = None  # Reset ADK session
        st.session_state.messages = []
        st.session_state.attached_files = []  # Clear attachments for new conversation
        st.rerun()
    
    # Load conversations (use local storage directly, skip backend for now)
    conversations = list(st.session_state.local_conversations.values())
    
    # Sort by created_at descending (newest first)
    conversations.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    if conversations:
        st.markdown(f"**{len(conversations)} conversation(s)**")
        for conv in conversations:
            # Display conversation title with better formatting like ChatGPT
            title = conv['title'] if conv['title'] != "New Conversation" else f"Chat {conv['id'][:8]}..."
            if st.button(
                f"💬 {title[:35]}..." if len(title) > 35 else f"💬 {title}",
                key=conv['id'],
                use_container_width=True
            ):
                st.session_state.current_conversation_id = conv['id']
                st.session_state.adk_session_id = None  # Reset ADK session when switching
                st.session_state.attached_files = []  # Clear attachments when switching conversations
                
                # Load conversation messages from local storage first
                if conv['id'] in st.session_state.local_conversations:
                    conv_data = st.session_state.local_conversations[conv['id']]
                    st.session_state.messages = conv_data.get('messages', [])
                else:
                    # Try to fetch from backend API if not in local storage
                    conversation_details = get_conversation_details(conv['id'])
                    if conversation_details and 'messages' in conversation_details:
                        st.session_state.messages = conversation_details['messages']
                    else:
                        st.session_state.messages = []
                st.rerun()
    else:
        st.markdown("*No conversations yet. Start chatting to create your first conversation!*")
    
    st.markdown("---")
    st.markdown("### 📋 RFP Research Capabilities")
    st.markdown("**RFP Management:**")
    st.markdown("📋 RFP Analysis • Opportunity Management • Document Processing")
    st.markdown("📝 Proposal Generation • Requirement Analysis • Compliance Check")
    st.markdown("🔍 **Expertise Areas:** Government RFPs, Corporate Tenders, Technical Proposals")
    st.markdown("📄 **Document Types:** RFPs, Proposals, Technical Responses, Compliance Matrices")
    st.markdown("🎯 **Specialized:** RFP-to-Proposal Pipeline Management")

# Main chat area
if st.session_state.current_conversation_id:
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"💬 Conversation ID: {st.session_state.current_conversation_id}")
    with col2:
        if st.session_state.adk_session_id:
            st.info(f"📋 RFP Session: {st.session_state.adk_session_id[:8]}...")

# Display messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Display attachments if any
        if "attachments" in message and message["attachments"]:
            st.markdown("**📎 Attachments:**")
            for attachment in message["attachments"]:
                st.markdown(f"- [{os.path.basename(attachment)}]({BACKEND_URL}{attachment})")
        
        if "timestamp" in message:
            st.caption(f"🕒 {message['timestamp']}")

# Initialize file upload state
if 'attached_files' not in st.session_state:
    st.session_state.attached_files = []

# CSS for file chips styling
st.markdown("""
<style>
.file-chip {
    display: inline-flex;
    align-items: center;
    background-color: #f0f2f6;
    border: 1px solid #d1d5db;
    border-radius: 20px;
    padding: 8px 12px;
    margin: 4px;
    font-size: 14px;
}
.file-chip .remove-btn {
    margin-left: 8px;
    cursor: pointer;
    color: #6b7280;
}
.file-chip .remove-btn:hover {
    color: #ef4444;
}

/* Activity Tracker Styles */
.activity-tracker {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
    padding: 20px;
    margin: 10px 0;
    color: white;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

.activity-header {
    display: flex;
    align-items: center;
    margin-bottom: 15px;
}

.activity-title {
    font-size: 18px;
    font-weight: bold;
    margin-left: 10px;
}

.progress-container {
    background: rgba(255,255,255,0.2);
    border-radius: 10px;
    padding: 3px;
    margin: 10px 0;
}

.progress-bar {
    background: linear-gradient(90deg, #4CAF50, #45a049);
    height: 8px;
    border-radius: 8px;
    transition: width 0.3s ease;
}

.step-container {
    display: flex;
    justify-content: space-between;
    margin-top: 20px;
    flex-wrap: wrap;
}

.step-item {
    flex: 1;
    min-width: 120px;
    margin: 5px;
    padding: 12px;
    border-radius: 8px;
    text-align: center;
    transition: all 0.3s ease;
}

.step-completed {
    background: rgba(76, 175, 80, 0.3);
    border: 2px solid #4CAF50;
}

.step-in-progress {
    background: rgba(33, 150, 243, 0.3);
    border: 2px solid #2196F3;
    animation: pulse 2s infinite;
}

.step-pending {
    background: rgba(158, 158, 158, 0.3);
    border: 2px solid #9E9E9E;
}

.step-error {
    background: rgba(244, 67, 54, 0.3);
    border: 2px solid #F44336;
}

@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.7; }
    100% { opacity: 1; }
}

.step-icon {
    font-size: 24px;
    margin-bottom: 8px;
}

.step-name {
    font-weight: bold;
    margin-bottom: 4px;
}

.step-description {
    font-size: 11px;
    opacity: 0.8;
}
</style>
""", unsafe_allow_html=True)

# Initialize file clearing counter if not exists
if 'file_clear_counter' not in st.session_state:
    st.session_state.file_clear_counter = 0

# File uploader with dynamic key to reset when files are cleared
uploader_key = f"file_uploader_{st.session_state.current_conversation_id or 'new'}_{st.session_state.file_clear_counter}"
uploaded_files = st.file_uploader(
    "Attach files",
    accept_multiple_files=True,
    type=['txt', 'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'gif'],
    key=uploader_key
)

# Update attached files when new files are uploaded
if uploaded_files:
    st.session_state.attached_files = uploaded_files
else:
    # Clear attached files if uploader is empty
    if not st.session_state.get('attached_files'):
        st.session_state.attached_files = []

# Show attached files as chips above the input
if st.session_state.attached_files:
    st.markdown("**Attached files:**")
    
    # Create file chips
    chip_cols = st.columns(min(len(st.session_state.attached_files), 4))  # Max 4 per row
    for i, file in enumerate(st.session_state.attached_files):
        col_idx = i % 4
        with chip_cols[col_idx]:
            # File type icon
            if file.type.startswith('image/'):
                icon = "🖼️"
            elif file.type == 'application/pdf':
                icon = "📄"
            elif file.type.startswith('text/'):
                icon = "📝"
            else:
                icon = "📁"
            
            # Create chip with file info and remove button
            chip_col1, chip_col2 = st.columns([5, 1])
            with chip_col1:
                st.markdown(f"""
                <div class="file-chip">
                    {icon} {file.name[:20]}{'...' if len(file.name) > 20 else ''}
                </div>
                """, unsafe_allow_html=True)
                st.caption(f"{file.size} bytes")
            
            with chip_col2:
                if st.button("✕", key=f"remove_{i}", help=f"Remove {file.name}"):
                    # Remove this file
                    st.session_state.attached_files = [
                        f for j, f in enumerate(st.session_state.attached_files) if j != i
                    ]
                    st.rerun()
    
    st.markdown("---")

# Chat input
if prompt := st.chat_input("Ask about RFP analysis, proposal generation, opportunity management, document processing..."):
        # Handle file uploads first
        attachment_urls = []
        if st.session_state.attached_files:
            with st.spinner("📤 Uploading files..."):
                for file in st.session_state.attached_files:
                    upload_result = upload_file(file)
                    if upload_result:
                        attachment_urls.append(upload_result["file_url"])
        
        # Add user message to display
        timestamp = datetime.now().strftime("%I:%M %p")
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "timestamp": timestamp,
            "attachments": attachment_urls
        })
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
            
            # Display attachments if any
            if attachment_urls:
                st.markdown("**📎 Attachments:**")
                for attachment in attachment_urls:
                    st.markdown(f"- [{os.path.basename(attachment)}]({BACKEND_URL}{attachment})")
            
            st.caption(f"🕒 {timestamp}")
        
        # Create conversation locally if none exists
        if not st.session_state.current_conversation_id:
            title_words = prompt.split()[:4]
            title = " ".join(title_words) + ("..." if len(prompt.split()) > 4 else "")
            
            st.session_state.current_conversation_id = f"conv_{st.session_state.conversation_counter:04d}"
            st.session_state.conversation_counter += 1
            
            # Store conversation locally (persistent)
            conv_data = {
                "id": st.session_state.current_conversation_id,
                "title": title,
                "user_id": "local-user",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "messages": [],
                "message_count": 0
            }
            st.session_state.local_conversations[st.session_state.current_conversation_id] = conv_data
            save_local_conversation(conv_data)
        
        # Send to RFP Research Agent
        with st.chat_message("assistant"):
            # Create placeholder for activity tracking
            activity_placeholder = st.empty()
            response_placeholder = st.empty()
            
            # Define the thinking steps to stream
            thinking_steps = [
                "Initializing RFP session",
                "Analyzing user request", 
                "Coordinating sub-agents",
                "Processing information",
                "Generating response"
            ]
            
            # Stream the thinking steps
            stream_agent_steps(activity_placeholder, thinking_steps)
            
            # Use RFP Research Agent
            with st.spinner("📋 Finalizing response..."):
                result = send_rfp_chat_message(
                    prompt, 
                    st.session_state.current_conversation_id,
                    st.session_state.adk_session_id,
                    streaming=True,
                    attachments=attachment_urls
                )
            
            # Clear the thinking display
            activity_placeholder.empty()
            
            if result:
                final_result = process_streaming_response(result, activity_placeholder)
                
                if final_result:
                    response_text = final_result.get('response', '')
                    st.session_state.current_conversation_id = final_result.get('conversation_id', st.session_state.current_conversation_id)
                    st.session_state.adk_session_id = final_result.get('session_id', st.session_state.adk_session_id)
                    
                    # Display response in the response placeholder
                    with response_placeholder.container():
                        st.markdown(response_text)
                        response_timestamp = datetime.now().strftime("%I:%M %p")
                        st.caption(f"🕒 {response_timestamp} | 📋 RFP Research Agent")
                    
                    # Add to session state
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response_text,
                        "timestamp": response_timestamp,
                        "attachments": []
                    })
                    
                    # Update local conversation storage
                    if st.session_state.current_conversation_id in st.session_state.local_conversations:
                        st.session_state.local_conversations[st.session_state.current_conversation_id]["messages"] = st.session_state.messages.copy()
                    
                    # Clear attached files after sending
                    st.session_state.attached_files = []
                    st.session_state.file_clear_counter += 1  # Force file uploader reset
                    
                    # Force refresh to update conversation list
                    st.rerun()
                else:
                    # Fallback to local-only mode if backend fails
                    response_text = generate_local_response(prompt, attachment_urls)
                    
                    # Display response
                    with response_placeholder.container():
                        st.markdown(response_text)
                        response_timestamp = datetime.now().strftime("%I:%M %p")
                        st.caption(f"🕒 {response_timestamp} | 📱 Local Mode (RFP Backend Unavailable)")
                    
                    # Add to session state
                    st.session_state.messages.append({
                            "role": "assistant",
                            "content": response_text,
                            "timestamp": response_timestamp,
                            "attachments": []
                    })
                    
                    # Update local conversation storage
                    if st.session_state.current_conversation_id in st.session_state.local_conversations:
                        st.session_state.local_conversations[st.session_state.current_conversation_id]["messages"] = st.session_state.messages.copy()
                    
                    # Clear attached files
                    st.session_state.attached_files = []
                    st.session_state.file_clear_counter += 1
                    
                    st.rerun()

# Footer
st.markdown("---")
st.markdown("*IntelliSurf AI - Powered by RFP Research Agent | Specialized for RFP Management & Proposal Generation*")
