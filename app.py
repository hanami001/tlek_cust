import streamlit as st
import requests
import json
from datetime import datetime
import time

# ตั้งค่าหน้าเว็บ
st.set_page_config(
    page_title="N8N Chat Interface",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS สำหรับปรับแต่งหน้าตา
st.markdown("""
<style>
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .user-message {
        background-color: #e3f2fd;
        margin-left: 20%;
    }
    .bot-message {
        background-color: #f5f5f5;
        margin-right: 20%;
    }
    .message-header {
        font-weight: bold;
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
        color: #666;
    }
    .message-content {
        font-size: 1rem;
        line-height: 1.5;
    }
    .timestamp {
        font-size: 0.75rem;
        color: #999;
        margin-top: 0.5rem;
    }
    .stTextInput > div > div > input {
        border-radius: 20px;
    }
    .sidebar-content {
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ฟังก์ชันสำหรับเรียก n8n webhook
def send_to_n8n(webhook_url, message, session_id=None):
    """
    ส่งข้อความไปยัง n8n webhook
    
    Args:
        webhook_url: URL ของ n8n webhook
        message: ข้อความที่จะส่ง
        session_id: ID ของเซสชัน (ถ้ามี)
    
    Returns:
        dict: Response จาก webhook
    """
    try:
        payload = {
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id or st.session_state.get('session_id', 'default')
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        with st.spinner('กำลังประมวลผล...'):
            response = requests.post(
                webhook_url,
                json=payload,
                headers=headers,
                timeout=30
            )
        
        if response.status_code == 200:
            return {
                'success': True,
                'data': response.json() if response.text else {'message': 'Success'},
                'status_code': response.status_code
            }
        else:
            return {
                'success': False,
                'error': f'HTTP {response.status_code}: {response.text}',
                'status_code': response.status_code
            }
    
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'error': 'Request timeout - n8n ใช้เวลานานเกินไป'
        }
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'error': 'ไม่สามารถเชื่อมต่อกับ n8n webhook ได้'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'เกิดข้อผิดพลาด: {str(e)}'
        }

# ฟังก์ชันแสดงข้อความใน chat
def display_message(role, content, timestamp):
    """แสดงข้อความในรูปแบบ chat bubble"""
    message_class = "user-message" if role == "user" else "bot-message"
    role_name = "คุณ" if role == "user" else "Bot"
    icon = "👤" if role == "user" else "🤖"
    
    st.markdown(f"""
    <div class="chat-message {message_class}">
        <div class="message-header">{icon} {role_name}</div>
        <div class="message-content">{content}</div>
        <div class="timestamp">{timestamp}</div>
    </div>
    """, unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'session_id' not in st.session_state:
    st.session_state.session_id = f"session_{int(time.time())}"

if 'webhook_url' not in st.session_state:
    st.session_state.webhook_url = ""

# Sidebar สำหรับการตั้งค่า
with st.sidebar:
    st.markdown("### ⚙️ การตั้งค่า")
    
    # กรอก Webhook URL
    webhook_url_input = st.text_input(
        "N8N Webhook URL",
        value=st.session_state.webhook_url,
        placeholder="https://your-n8n-instance.com/webhook/...",
        help="ใส่ URL ของ webhook จาก n8n"
    )
    
    if webhook_url_input != st.session_state.webhook_url:
        st.session_state.webhook_url = webhook_url_input
    
    # Session ID
    st.text_input(
        "Session ID",
        value=st.session_state.session_id,
        disabled=True,
        help="ID เฉพาะของเซสชันนี้"
    )
    
    st.markdown("---")
    
    # ปุ่มล้างประวัติ
    if st.button("🗑️ ล้างประวัติการสนทนา", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    # ปุ่มสร้าง Session ใหม่
    if st.button("🔄 เริ่ม Session ใหม่", use_container_width=True):
        st.session_state.session_id = f"session_{int(time.time())}"
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 📊 สถิติ")
    st.metric("จำนวนข้อความ", len(st.session_state.messages))
    
    st.markdown("---")
    st.markdown("""
    ### 💡 วิธีใช้งาน
    1. ใส่ N8N Webhook URL ในช่องด้านบน
    2. พิมพ์ข้อความในช่อง chat
    3. กด Enter หรือคลิกปุ่มส่ง
    4. รอการตอบกลับจาก n8n
    
    ### 🔧 รูปแบบ Payload
    ```json
    {
        "message": "ข้อความของคุณ",
        "timestamp": "ISO timestamp",
        "session_id": "session_xxx"
    }
    ```
    """)

# Main content area
st.title("💬 N8N Chat Interface")
st.markdown("ระบบ Chat ที่เชื่อมต่อกับ n8n Workflow")

# แสดงคำเตือนถ้ายังไม่ได้ตั้งค่า webhook URL
if not st.session_state.webhook_url:
    st.warning("⚠️ กรุณาใส่ N8N Webhook URL ในแถบด้านซ้ายก่อนเริ่มใช้งาน")

# แสดงประวัติการสนทนา
chat_container = st.container()
with chat_container:
    for msg in st.session_state.messages:
        display_message(
            msg['role'],
            msg['content'],
            msg['timestamp']
        )

# Input area
st.markdown("---")
col1, col2 = st.columns([6, 1])

with col1:
    user_input = st.text_input(
        "พิมพ์ข้อความ...",
        key="user_input",
        placeholder="พิมพ์ข้อความที่นี่...",
        label_visibility="collapsed"
    )

with col2:
    send_button = st.button("📤 ส่ง", use_container_width=True, type="primary")

# ประมวลผลเมื่อกดส่ง
if (send_button or user_input) and user_input.strip():
    if not st.session_state.webhook_url:
        st.error("❌ กรุณาใส่ N8N Webhook URL ก่อน")
    else:
        # เพิ่มข้อความของผู้ใช้
        user_message = {
            'role': 'user',
            'content': user_input,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        st.session_state.messages.append(user_message)
        
        # ส่งไปยัง n8n
        response = send_to_n8n(
            st.session_state.webhook_url,
            user_input,
            st.session_state.session_id
        )
        
        # ประมวลผลการตอบกลับ
        if response['success']:
            # พยายามดึงข้อความจาก response
            bot_content = ""
            
            if isinstance(response['data'], dict):
                # ลองหาข้อความจาก key ต่างๆ ที่อาจมี
                bot_content = (
                    response['data'].get('response') or
                    response['data'].get('message') or
                    response['data'].get('output') or
                    response['data'].get('reply') or
                    json.dumps(response['data'], indent=2, ensure_ascii=False)
                )
            else:
                bot_content = str(response['data'])
            
            bot_message = {
                'role': 'bot',
                'content': bot_content,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            st.session_state.messages.append(bot_message)
            
            # แสดงสถานะสำเร็จ
            st.success("✅ ส่งข้อความสำเร็จ")
        else:
            # แสดง error
            error_message = {
                'role': 'bot',
                'content': f"❌ เกิดข้อผิดพลาด: {response['error']}",
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            st.session_state.messages.append(error_message)
            st.error(f"❌ {response['error']}")
        
        # Rerun เพื่อแสดงข้อความใหม่
        st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <small>Powered by Streamlit + N8N | Built for seamless workflow automation</small>
</div>
""", unsafe_allow_html=True)
