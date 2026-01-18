import streamlit as st
import requests
import json
from datetime import datetime
import time

# กำหนดค่า Page Config
st.set_page_config(
    page_title="AI Chat Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        background-color: #f5f5f5;
    }
    .stTextInput > div > div > input {
        background-color: white;
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .chat-message.user {
        background-color: #e3f2fd;
        border-left: 5px solid #2196f3;
    }
    .chat-message.assistant {
        background-color: #f1f8e9;
        border-left: 5px solid #4caf50;
    }
    .chat-message .message-content {
        margin-top: 0.5rem;
        color: #333;
    }
    .chat-message .message-time {
        font-size: 0.75rem;
        color: #666;
        margin-top: 0.5rem;
    }
    .sidebar .sidebar-content {
        background-color: #fafafa;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'webhook_url' not in st.session_state:
    st.session_state.webhook_url = ""

# ฟังก์ชันส่งข้อความไป n8n webhook
def send_to_n8n(message, webhook_url):
    """Send message to n8n webhook and get response"""
    try:
        payload = {
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "session_id": st.session_state.get('session_id', 'default')
        }
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            webhook_url,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        response.raise_for_status()
        
        # รับ response จาก n8n
        result = response.json()
        
        # ปรับตามโครงสร้างของ n8n response
        if isinstance(result, dict):
            return result.get('response', result.get('output', str(result)))
        else:
            return str(result)
            
    except requests.exceptions.Timeout:
        return "❌ เกิดข้อผิดพลาด: Request timeout"
    except requests.exceptions.RequestException as e:
        return f"❌ เกิดข้อผิดพลาด: {str(e)}"
    except Exception as e:
        return f"❌ เกิดข้อผิดพลาดที่ไม่คาดคิด: {str(e)}"

# ฟังก์ชันแสดง chat message
def display_message(role, content, timestamp=None):
    """Display a chat message"""
    message_class = "user" if role == "user" else "assistant"
    icon = "👤" if role == "user" else "🤖"
    
    timestamp_str = ""
    if timestamp:
        timestamp_str = f'<div class="message-time">🕐 {timestamp}</div>'
    
    st.markdown(f"""
    <div class="chat-message {message_class}">
        <div><strong>{icon} {role.upper()}</strong></div>
        <div class="message-content">{content}</div>
        {timestamp_str}
    </div>
    """, unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("⚙️ การตั้งค่า")
    
    # Webhook URL input
    webhook_url = st.text_input(
        "n8n Webhook URL",
        value=st.session_state.webhook_url,
        type="password",
        help="ใส่ webhook URL จาก n8n"
    )
    
    if webhook_url:
        st.session_state.webhook_url = webhook_url
        st.success("✅ Webhook URL ถูกบันทึกแล้ว")
    
    st.divider()
    
    # Session ID
    if 'session_id' not in st.session_state:
        st.session_state.session_id = f"session_{int(time.time())}"
    
    st.text_input("Session ID", value=st.session_state.session_id, disabled=True)
    
    st.divider()
    
    # Statistics
    st.subheader("📊 สถิติ")
    st.metric("จำนวนข้อความ", len(st.session_state.messages))
    
    # Clear chat button
    if st.button("🗑️ ล้างประวัติการสนทนา", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    
    # Export chat
    if st.button("💾 Export Chat", use_container_width=True):
        if st.session_state.messages:
            chat_export = json.dumps(st.session_state.messages, indent=2, ensure_ascii=False)
            st.download_button(
                label="⬇️ ดาวน์โหลด JSON",
                data=chat_export,
                file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )

# Main chat interface
st.title("🤖 AI Chat Assistant")
st.caption("Powered by n8n Webhook")

# Check if webhook URL is set
if not st.session_state.webhook_url:
    st.warning("⚠️ กรุณาใส่ n8n Webhook URL ในแถบด้านข้าง")
    st.info("""
    ### วิธีการใช้งาน:
    1. สร้าง Webhook ใน n8n
    2. คัดลอก Webhook URL
    3. วาง URL ในช่อง "n8n Webhook URL" ที่แถบด้านข้าง
    4. เริ่มแชทได้เลย!
    """)
else:
    # Display chat messages
    chat_container = st.container()
    
    with chat_container:
        if st.session_state.messages:
            for message in st.session_state.messages:
                display_message(
                    message["role"],
                    message["content"],
                    message.get("timestamp")
                )
        else:
            st.info("👋 สวัสดีครับ! เริ่มต้นการสนทนาได้เลย")
    
    # Chat input
    user_input = st.chat_input("พิมพ์ข้อความของคุณที่นี่...")
    
    if user_input:
        # Add user message
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.messages.append({
            "role": "user",
            "content": user_input,
            "timestamp": timestamp
        })
        
        # Display user message
        with chat_container:
            display_message("user", user_input, timestamp)
        
        # Show loading
        with st.spinner("🤔 กำลังคิด..."):
            # Send to n8n and get response
            response = send_to_n8n(user_input, st.session_state.webhook_url)
            
            # Add assistant message
            response_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.messages.append({
                "role": "assistant",
                "content": response,
                "timestamp": response_timestamp
            })
        
        # Rerun to update chat
        st.rerun()

# Footer
st.divider()
st.caption("Made with ❤️ using Streamlit and n8n")
