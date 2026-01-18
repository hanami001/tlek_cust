import streamlit as st
import requests
import json
from datetime import datetime
import time
import pandas as pd
from io import StringIO

# ตั้งค่าหน้าเว็บ
st.set_page_config(
    page_title="N8N Chat Interface Pro",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS ที่ปรับปรุงแล้ว
st.markdown("""
<style>
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.8rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
        animation: fadeIn 0.3s ease-in;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-left: 20%;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .bot-message {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        margin-right: 20%;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .message-header {
        font-weight: bold;
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .user-message .message-header {
        color: rgba(255,255,255,0.9);
    }
    .bot-message .message-header {
        color: #333;
    }
    .message-content {
        font-size: 1rem;
        line-height: 1.6;
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    .user-message .message-content {
        color: white;
    }
    .timestamp {
        font-size: 0.75rem;
        margin-top: 0.5rem;
        opacity: 0.7;
    }
    .stTextInput > div > div > input {
        border-radius: 20px;
        border: 2px solid #667eea;
    }
    .stat-card {
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .success-badge {
        background: #10b981;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.8rem;
        display: inline-block;
    }
    .error-badge {
        background: #ef4444;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.8rem;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# ฟังก์ชันสำหรับ parse response
def parse_bot_response(response_data):
    """
    Parse response จาก n8n ให้เป็นข้อความที่อ่านง่าย
    """
    if isinstance(response_data, str):
        return response_data
    
    if isinstance(response_data, dict):
        # ลำดับความสำคัญของ keys ที่จะค้นหา
        priority_keys = ['response', 'message', 'output', 'reply', 'text', 'answer', 'result']
        
        for key in priority_keys:
            if key in response_data:
                value = response_data[key]
                if isinstance(value, str):
                    return value
                elif isinstance(value, dict) or isinstance(value, list):
                    return json.dumps(value, indent=2, ensure_ascii=False)
        
        # ถ้าไม่เจอ key ที่ต้องการ ให้แสดงทั้งหมดในรูปแบบ JSON
        return json.dumps(response_data, indent=2, ensure_ascii=False)
    
    return str(response_data)

# ฟังก์ชันส่งข้อความ
def send_to_n8n(webhook_url, message, session_id=None, additional_data=None):
    """
    ส่งข้อความไปยัง n8n webhook พร้อม error handling ที่ดีขึ้น
    """
    try:
        payload = {
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id or st.session_state.get('session_id', 'default')
        }
        
        # เพิ่มข้อมูลเสริม (ถ้ามี)
        if additional_data:
            payload.update(additional_data)
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # แสดง spinner พร้อมข้อความ
        with st.spinner('🔄 กำลังส่งข้อความไปยัง n8n...'):
            start_time = time.time()
            response = requests.post(
                webhook_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            response_time = time.time() - start_time
        
        if response.status_code == 200:
            try:
                data = response.json() if response.text else {'message': 'Success'}
            except json.JSONDecodeError:
                data = {'message': response.text}
            
            return {
                'success': True,
                'data': data,
                'status_code': response.status_code,
                'response_time': round(response_time, 2)
            }
        else:
            return {
                'success': False,
                'error': f'HTTP {response.status_code}: {response.text[:200]}',
                'status_code': response.status_code,
                'response_time': round(response_time, 2)
            }
    
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'error': '⏱️ Request timeout - n8n ใช้เวลานานเกิน 30 วินาที'
        }
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'error': '🔌 ไม่สามารถเชื่อมต่อกับ n8n webhook - ตรวจสอบ URL และ network'
        }
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'🚫 Request error: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'❌ Unexpected error: {str(e)}'
        }

# ฟังก์ชันแสดงข้อความ
def display_message(role, content, timestamp, metadata=None):
    """แสดงข้อความในรูปแบบ chat bubble พร้อม metadata"""
    message_class = "user-message" if role == "user" else "bot-message"
    role_name = "คุณ" if role == "user" else "AI Assistant"
    icon = "👤" if role == "user" else "🤖"
    
    # เตรียม metadata text
    meta_text = ""
    if metadata:
        if 'response_time' in metadata:
            meta_text = f" • ⚡ {metadata['response_time']}s"
    
    st.markdown(f"""
    <div class="chat-message {message_class}">
        <div class="message-header">
            <span>{icon}</span>
            <span>{role_name}</span>
        </div>
        <div class="message-content">{content}</div>
        <div class="timestamp">{timestamp}{meta_text}</div>
    </div>
    """, unsafe_allow_html=True)

# ฟังก์ชัน export ประวัติ
def export_chat_history(messages):
    """Export ประวัติการสนทนาเป็น CSV"""
    df = pd.DataFrame(messages)
    csv = df.to_csv(index=False, encoding='utf-8-sig')
    return csv

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'session_id' not in st.session_state:
    st.session_state.session_id = f"session_{int(time.time())}"

if 'webhook_url' not in st.session_state:
    st.session_state.webhook_url = ""

if 'total_requests' not in st.session_state:
    st.session_state.total_requests = 0

if 'successful_requests' not in st.session_state:
    st.session_state.successful_requests = 0

if 'webhook_status' not in st.session_state:
    st.session_state.webhook_status = "unknown"

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ การตั้งค่า N8N")
    
    # Webhook URL
    webhook_url_input = st.text_input(
        "N8N Webhook URL",
        value=st.session_state.webhook_url,
        placeholder="https://your-n8n.com/webhook/chat",
        help="URL ของ webhook endpoint จาก n8n workflow"
    )
    
    if webhook_url_input != st.session_state.webhook_url:
        st.session_state.webhook_url = webhook_url_input
        st.session_state.webhook_status = "unknown"
    
    # Test Connection
    if st.session_state.webhook_url:
        col1, col2 = st.columns([2, 1])
        with col1:
            if st.button("🔍 ทดสอบการเชื่อมต่อ", use_container_width=True):
                with st.spinner("กำลังทดสอบ..."):
                    test_response = send_to_n8n(
                        st.session_state.webhook_url,
                        "test_connection",
                        st.session_state.session_id
                    )
                    if test_response['success']:
                        st.session_state.webhook_status = "connected"
                        st.success("✅ เชื่อมต่อสำเร็จ!")
                    else:
                        st.session_state.webhook_status = "error"
                        st.error(f"❌ {test_response['error']}")
        
        with col2:
            if st.session_state.webhook_status == "connected":
                st.markdown('<div class="success-badge">🟢 Online</div>', unsafe_allow_html=True)
            elif st.session_state.webhook_status == "error":
                st.markdown('<div class="error-badge">🔴 Error</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Session Management
    st.markdown("### 🔑 Session Management")
    
    st.text_input(
        "Session ID",
        value=st.session_state.session_id,
        disabled=True,
        help="ID เฉพาะของเซสชันปัจจุบัน"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Session ใหม่", use_container_width=True):
            st.session_state.session_id = f"session_{int(time.time())}"
            st.session_state.messages = []
            st.rerun()
    
    with col2:
        if st.button("🗑️ ล้างประวัติ", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    
    st.markdown("---")
    
    # Statistics
    st.markdown("### 📊 สถิติการใช้งาน")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("ข้อความทั้งหมด", len(st.session_state.messages))
    with col2:
        st.metric("คำขอ API", st.session_state.total_requests)
    
    if st.session_state.total_requests > 0:
        success_rate = (st.session_state.successful_requests / st.session_state.total_requests) * 100
        st.metric("อัตราสำเร็จ", f"{success_rate:.1f}%")
    
    st.markdown("---")
    
    # Export
    st.markdown("### 💾 Export ข้อมูล")
    
    if st.session_state.messages:
        csv_data = export_chat_history(st.session_state.messages)
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=f"chat_history_{st.session_state.session_id}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        json_data = json.dumps(st.session_state.messages, indent=2, ensure_ascii=False)
        st.download_button(
            label="📥 Download JSON",
            data=json_data,
            file_name=f"chat_history_{st.session_state.session_id}.json",
            mime="application/json",
            use_container_width=True
        )
    else:
        st.info("ไม่มีประวัติการสนทนา")
    
    st.markdown("---")
    
    # Help
    with st.expander("💡 คู่มือการใช้งาน"):
        st.markdown("""
        **วิธีใช้งาน:**
        1. ใส่ N8N Webhook URL
        2. กดทดสอบการเชื่อมต่อ
        3. เริ่มพิมพ์ข้อความ
        4. กด Enter หรือปุ่มส่ง
        
        **Payload Format:**
        ```json
        {
          "message": "text",
          "timestamp": "ISO-8601",
          "session_id": "session_xxx"
        }
        ```
        
        **Expected Response:**
        - ใช้ key: `response`, `message`, `output`, หรือ `reply`
        - Format: JSON object
        """)

# Main Area
st.title("💬 N8N Chat Interface Pro")
st.markdown("ระบบ Chat ขั้นสูงที่เชื่อมต่อกับ n8n Automation Workflow")

# Warning
if not st.session_state.webhook_url:
    st.warning("⚠️ กรุณาใส่ N8N Webhook URL ในแถบด้านซ้ายก่อนเริ่มใช้งาน")
    st.info("""
    **ขั้นตอนเริ่มต้น:**
    1. เปิด n8n workflow ของคุณ
    2. เพิ่ม Webhook node
    3. คัดลอก Webhook URL
    4. วาง URL ในช่องด้านซ้าย
    5. กดทดสอบการเชื่อมต่อ
    """)

# Chat Container
chat_container = st.container()
with chat_container:
    if not st.session_state.messages:
        st.info("👋 สวัสดีครับ! เริ่มต้นการสนทนาโดยพิมพ์ข้อความด้านล่าง")
    else:
        for msg in st.session_state.messages:
            metadata = msg.get('metadata', {})
            display_message(
                msg['role'],
                msg['content'],
                msg['timestamp'],
                metadata
            )

# Input Area
st.markdown("---")

col1, col2 = st.columns([5, 1])

with col1:
    user_input = st.text_input(
        "พิมพ์ข้อความ...",
        key="user_input",
        placeholder="พิมพ์ข้อความของคุณที่นี่...",
        label_visibility="collapsed"
    )

with col2:
    send_button = st.button("📤 ส่ง", use_container_width=True, type="primary")

# Process Input
if (send_button or user_input) and user_input.strip():
    if not st.session_state.webhook_url:
        st.error("❌ กรุณาใส่ N8N Webhook URL ก่อนส่งข้อความ")
    else:
        # บันทึกข้อความผู้ใช้
        user_message = {
            'role': 'user',
            'content': user_input,
            'timestamp': datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }
        st.session_state.messages.append(user_message)
        
        # ส่งไปยัง n8n
        st.session_state.total_requests += 1
        response = send_to_n8n(
            st.session_state.webhook_url,
            user_input,
            st.session_state.session_id
        )
        
        # ประมวลผลคำตอบ
        if response['success']:
            st.session_state.successful_requests += 1
            
            # Parse response
            bot_content = parse_bot_response(response['data'])
            
            bot_message = {
                'role': 'bot',
                'content': bot_content,
                'timestamp': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                'metadata': {
                    'response_time': response.get('response_time', 0),
                    'status_code': response.get('status_code', 200)
                }
            }
            st.session_state.messages.append(bot_message)
            st.session_state.webhook_status = "connected"
            
        else:
            # Error message
            error_message = {
                'role': 'bot',
                'content': f"❌ เกิดข้อผิดพลาด:\n{response['error']}",
                'timestamp': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                'metadata': {'error': True}
            }
            st.session_state.messages.append(error_message)
            st.session_state.webhook_status = "error"
        
        # Rerun
        st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <small>
        🚀 <strong>N8N Chat Interface Pro</strong> | 
        Built with Streamlit + N8N | 
        Made with ❤️ for Automation
    </small>
</div>
""", unsafe_allow_html=True)
