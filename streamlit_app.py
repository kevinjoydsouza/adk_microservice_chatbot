import streamlit as st
import requests
import json
from datetime import datetime
import os

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
            print(f"Error fetching conversations: {response.status_code}")
            return []
    except Exception as e:
        print(f"Exception fetching conversations: {e}")
        return []

def upload_file(uploaded_file):
    """Upload file to backend"""
    try:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        response = requests.post(f"{BACKEND_URL}/upload", headers={"Authorization": f"Bearer {AUTH_TOKEN}"}, files=files)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Upload error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Upload error: {str(e)}")
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
            st.error(f"IntelliSurf Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"IntelliSurf Connection error: {str(e)}")
        return None

def get_conversation_details(conversation_id):
    """Get conversation with messages"""
    try:
        response = requests.get(f"{BACKEND_URL}/conversations/{conversation_id}", headers=headers)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

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

# Header
st.title("🧠 IntelliSurf AI")
st.subheader("Intelligent Knowledge Research & Document Generation Platform")

# AI Model Selection
col1, col2 = st.columns([3, 1])
with col2:
    ai_model = st.selectbox(
        "AI Agent",
        ["IntelliSurf Research Agent", "Gemini Direct"],
        index=0 if st.session_state.use_adk else 1,
        key="ai_model_select"
    )
    st.session_state.use_adk = (ai_model == "IntelliSurf Research Agent")
    
    if st.session_state.use_adk:
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
    
    # Load conversations
    conversations = get_conversations()
    
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
                # Load conversation messages
                conv_details = get_conversation_details(conv['id'])
                if conv_details and 'messages' in conv_details:
                    st.session_state.messages = []
                    for msg in conv_details['messages']:
                        st.session_state.messages.append({
                            "role": msg['role'],
                            "content": msg['content'],
                            "timestamp": msg['timestamp'],
                            "attachments": msg.get('metadata', {}).get('attachments', []) if msg.get('metadata') else []
                        })
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
        
        # Send to backend and get response
        with st.chat_message("assistant"):
            if st.session_state.use_adk:
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
                        st.caption(f"🕒 {response_timestamp} | 🎓 ADK Academic Research")
                        
                        # Add to session state
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": response_text,
                            "timestamp": response_timestamp,
                            "attachments": []
                        })
                        
                        # Clear attached files after sending
                        st.session_state.attached_files = []
                        st.session_state.file_clear_counter += 1  # Force file uploader reset
                        
                        # Force refresh to update conversation list
                        st.rerun()
                    else:
                        st.error("Failed to get response from ADK Academic Research Agent")
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
                        
                        # Clear attached files after sending
                        st.session_state.attached_files = []
                        st.session_state.file_clear_counter += 1  # Force file uploader reset
                        
                        # Force refresh to update conversation list
                        st.rerun()
                    else:
                        st.error("Failed to get response from Gemini Direct")

# Footer
st.markdown("---")
if st.session_state.use_adk:
    st.markdown("*Knowledge Surf - Powered by ADK Academic Research Agent*")
else:
    st.markdown("*Knowledge Surf - Powered by Google Gemini AI with Grounding*")
