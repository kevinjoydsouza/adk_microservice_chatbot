import streamlit as st
import requests
import json
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env file in academic-research folder
load_dotenv("academic-research/.env")

# Configure page
st.set_page_config(
    page_title="IntelliSurf AI - Intelligent Knowledge & Document Solutions",
    page_icon="🧠",
    layout="wide"
)

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

def send_chat_message(user_input, conversation_id=None, attachments=None):
    """Send chat message to backend (legacy Gemini endpoint)"""
    try:
        payload = {
            "user_input": user_input,
            "conversation_id": conversation_id,
            "attachments": attachments or []
        }
        response = requests.post(f"{BACKEND_URL}/chat", headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        return None

def send_adk_chat_message(user_input, conversation_id=None, session_id=None, streaming=False, attachments=None):
    """Send chat message to IntelliSurf Research Agent"""
    try:
        payload = {
            "user_input": user_input,
            "conversation_id": conversation_id,
            "session_id": session_id,
            "streaming": streaming,
            "attachments": attachments or []
        }
        response = requests.post(f"{BACKEND_URL}/adk-chat", headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        return None

def send_rfp_chat_message(user_input, conversation_id=None, session_id=None, streaming=False, attachments=None):
    """Send chat message to RFP Research Agent"""
    try:
        payload = {
            "user_input": user_input,
            "conversation_id": conversation_id,
            "session_id": session_id,
            "streaming": streaming,
            "attachments": attachments or []
        }
        response = requests.post(f"{BACKEND_URL}/rfp-chat", headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        return None

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
if "use_adk" not in st.session_state:
    st.session_state.use_adk = True  # Default to ADK
if "use_rfp" not in st.session_state:
    st.session_state.use_rfp = False  # Default to academic research

# Header
st.title("🧠 IntelliSurf AI")
st.subheader("Intelligent Knowledge Research & Document Generation Platform")

# AI Model Selection
col1, col2 = st.columns([3, 1])
with col2:
    ai_model = st.selectbox(
        "AI Agent",
        ["RFP Research Agent", "IntelliSurf Research Agent", "Gemini Direct"],
        index=0 if st.session_state.use_adk else 2,
        key="ai_model_select"
    )
    st.session_state.use_adk = (ai_model in ["RFP Research Agent", "IntelliSurf Research Agent"])
    st.session_state.use_rfp = (ai_model == "RFP Research Agent")
    
    if ai_model == "RFP Research Agent":
        st.info("📋 Using RFP Research Agent")
    elif ai_model == "IntelliSurf Research Agent":
        st.info("🧠 Using IntelliSurf Research Agent")
    else:
        st.info("🤖 Using Direct Gemini API")

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
    st.markdown("### 🧠 IntelliSurf Capabilities")
    st.markdown("**Research & Analysis:**")
    st.markdown("📊 Academic Research • Market Analysis • Competitive Intelligence")
    st.markdown("📈 Strategic Planning • Document Generation • Trend Analysis")
    st.markdown("🔍 **Expertise Areas:** Technology, Business, Science, Healthcare, Finance")
    st.markdown("📝 **Document Types:** RFPs, Proposals, Reports, Strategic Plans")
    st.markdown("🌐 **Multi-Domain:** Cross-industry insights and analysis")

# Main chat area
if st.session_state.current_conversation_id:
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"💬 Conversation ID: {st.session_state.current_conversation_id}")
    with col2:
        if st.session_state.use_adk and st.session_state.adk_session_id:
            st.info(f"🎓 ADK Session: {st.session_state.adk_session_id[:8]}...")

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
if prompt := st.chat_input("Ask me anything - research, analysis, document generation, strategic insights..."):
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
        
        # Send to backend and get response
        with st.chat_message("assistant"):
            if st.session_state.use_adk:
                if st.session_state.use_rfp:
                    # Use RFP Research Agent
                    with st.spinner("📋 RFP Research Agent processing..."):
                        result = send_rfp_chat_message(
                            prompt, 
                            st.session_state.current_conversation_id,
                            st.session_state.adk_session_id,
                            attachments=attachment_urls
                        )
                else:
                    # Use ADK Academic Research Agent
                    with st.spinner("🎓 ADK Academic Research Agent thinking..."):
                        result = send_adk_chat_message(
                            prompt, 
                            st.session_state.current_conversation_id,
                            st.session_state.adk_session_id,
                            attachments=attachment_urls
                        )
                    
                
                if result:
                    response_text = result["response"]
                    st.session_state.current_conversation_id = result["conversation_id"]
                    st.session_state.adk_session_id = result["session_id"]
                    
                    # Display response
                    st.markdown(response_text)
                    response_timestamp = datetime.now().strftime("%I:%M %p")
                    
                    if st.session_state.use_rfp:
                        st.caption(f"🕒 {response_timestamp} | 📋 RFP Research Agent")
                    else:
                        st.caption(f"🕒 {response_timestamp} | 🎓 ADK Academic Research")
                    
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
                    st.markdown(response_text)
                    response_timestamp = datetime.now().strftime("%I:%M %p")
                    st.caption(f"🕒 {response_timestamp} | 📱 Local Mode")
                    
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
            else:
                # Use legacy Gemini endpoint
                with st.spinner("🤖 Gemini thinking..."):
                    result = send_chat_message(prompt, st.session_state.current_conversation_id, attachment_urls)
                    
                    if result:
                        response_text = result["response"]
                        st.session_state.current_conversation_id = result["conversation_id"]
                        
                        # Display response
                        st.markdown(response_text)
                        response_timestamp = datetime.now().strftime("%I:%M %p")
                        st.caption(f"🕒 {response_timestamp} | 🤖 Gemini Direct")
                        
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
                    st.markdown(response_text)
                    response_timestamp = datetime.now().strftime("%I:%M %p")
                    st.caption(f"🕒 {response_timestamp} | 📱 Local Mode")
                    
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
if st.session_state.use_adk:
    st.markdown("*Knowledge Surf - Powered by ADK Academic Research Agent*")
else:
    st.markdown("*Knowledge Surf - Powered by Google Gemini AI with Grounding*")
