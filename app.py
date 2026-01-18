import streamlit as st
import requests
import json
from datetime import datetime
import time
import pandas as pd
from io import StringIO
import base64

# ตั้งค่าหน้าเว็บ
st.set_page_config(
    page_title="AI Agent Chat with Database",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS ที่ปรับปรุงแล้ว รองรับ tables และ code blocks
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
        margin-left: 15%;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .bot-message {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        margin-right: 15%;
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
    .query-badge {
        background: #3b82f6;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.8rem;
        display: inline-block;
        margin-top: 0.5rem;
    }
    .data-badge {
        background: #10b981;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.8rem;
        display: inline-block;
        margin-top: 0.5rem;
    }
    .stDataFrame {
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ฟังก์ชันสำหรับ parse response จาก AI Agent
def parse_agent_response(response_data):
    """
    Parse response จาก AI Agent ที่อาจมี SQL queries และ data
    """
    parsed = {
        'text': '',
        'sql_query': None,
        'data': None,
        'metadata': {}
    }
    
    if isinstance(response_data, str):
        parsed['text'] = response_data
        return parsed
    
    if isinstance(response_data, dict):
        # ลำดับความสำคัญของ keys สำหรับข้อความ
        text_keys = ['response', 'message', 'output', 'reply', 'text', 'answer', 'result']
        
        for key in text_keys:
            if key in response_data:
                parsed['text'] = str(response_data[key])
                break
        
        # ดึง SQL query (ถ้ามี)
        sql_keys = ['sql', 'query', 'sql_query', 'generated_sql', 'executed_query']
        for key in sql_keys:
            if key in response_data and response_data[key]:
                parsed['sql_query'] = response_data[key]
                break
        
        # ดึงข้อมูล (ถ้ามี)
        data_keys = ['data', 'results', 'rows', 'records', 'query_results']
        for key in data_keys:
            if key in response_data and response_data[key]:
                parsed['data'] = response_data[key]
                break
        
        # ดึง metadata
        metadata_keys = ['metadata', 'info', 'stats', 'summary']
        for key in metadata_keys:
            if key in response_data and response_data[key]:
                parsed['metadata'] = response_data[key]
                break
        
        # ถ้าไม่เจอข้อความ ให้แสดงทั้งหมดเป็น JSON
        if not parsed['text']:
            parsed['text'] = json.dumps(response_data, indent=2, ensure_ascii=False)
    
    return parsed

# ฟังก์ชันส่งข้อความไปยัง AI Agent
def send_to_ai_agent(webhook_url, message, session_id=None, context=None):
    """
    ส่งข้อความไปยัง AI Agent พร้อม context
    """
    try:
        payload = {
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "SessionId": session_id or st.session_state.get('SessionId', 'default'),
        }
        
        # เพิ่ม context ถ้ามี (ประวัติการสนทนา, database schema, etc.)
        if context:
            payload["context"] = context
        
        # เพิ่มประวัติการสนทนา (5 ข้อความล่าสุด)
        if st.session_state.get('messages'):
            recent_messages = st.session_state.messages[-5:]
            payload["conversation_history"] = [
                {"role": msg['role'], "content": msg['content']}
                for msg in recent_messages
            ]
        
        headers = {
            "Content-Type": "application/json"
        }
        
        with st.spinner('🤖 AI Agent กำลังคิด...'):
            start_time = time.time()
            response = requests.post(
                webhook_url,
                json=payload,
                headers=headers,
                timeout=60  # เพิ่ม timeout สำหรับ database queries
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
                'error': f'HTTP {response.status_code}: {response.text[:500]}',
                'status_code': response.status_code,
                'response_time': round(response_time, 2)
            }
    
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'error': '⏱️ Request timeout - AI Agent ใช้เวลานานเกิน 60 วินาที (อาจเป็นเพราะ query ซับซ้อน)'
        }
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'error': '🔌 ไม่สามารถเชื่อมต่อกับ AI Agent - ตรวจสอบ URL และ network'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'❌ Error: {str(e)}'
        }

# ฟังก์ชันแสดงข้อความ
def display_message(role, content, timestamp, metadata=None):
    """แสดงข้อความรวมถึง SQL queries และ data tables"""
    message_class = "user-message" if role == "user" else "bot-message"
    role_name = "คุณ" if role == "user" else "🤖 AI Agent"
    icon = "👤" if role == "user" else "🤖"
    
    # เตรียม metadata text
    meta_text = ""
    if metadata:
        if 'response_time' in metadata:
            meta_text = f" • ⚡ {metadata['response_time']}s"
        if metadata.get('has_query'):
            meta_text += " • 🔍 SQL Query"
        if metadata.get('has_data'):
            meta_text += " • 📊 Data"
    
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

# ฟังก์ชันแสดง SQL Query
def display_sql_query(query):
    """แสดง SQL query ในรูปแบบ code block"""
    st.markdown("**🔍 SQL Query ที่ถูกสร้าง:**")
    st.code(query, language='sql')

# ฟังก์ชันแสดงข้อมูลในรูปแบบ DataFrame
def display_data_table(data, title="📊 ผลลัพธ์จาก Database"):
    """แสดงข้อมูลในรูปแบบตาราง"""
    st.markdown(f"**{title}**")
    
    try:
        if isinstance(data, list) and len(data) > 0:
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
            
            # เพิ่มปุ่ม download
            csv = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"query_results_{int(time.time())}.csv",
                mime="text/csv"
            )
        elif isinstance(data, dict):
            st.json(data)
        else:
            st.write(data)
    except Exception as e:
        st.error(f"ไม่สามารถแสดงข้อมูลได้: {str(e)}")
        st.json(data)

# ฟังก์ชัน export ประวัติ
def export_chat_history(messages):
    """Export ประวัติการสนทนาเป็น CSV"""
    export_data = []
    for msg in messages:
        export_data.append({
            'timestamp': msg['timestamp'],
            'role': msg['role'],
            'content': msg['content'],
            'sql_query': msg.get('sql_query', ''),
            'has_data': msg.get('has_data', False)
        })
    df = pd.DataFrame(export_data)
    return df.to_csv(index=False, encoding='utf-8-sig')

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'SessionId' not in st.session_state:
    st.session_state.SessionId = f"session_{int(time.time())}"

if 'webhook_url' not in st.session_state:
    st.session_state.webhook_url = ""

if 'total_requests' not in st.session_state:
    st.session_state.total_requests = 0

if 'successful_requests' not in st.session_state:
    st.session_state.successful_requests = 0

if 'total_queries' not in st.session_state:
    st.session_state.total_queries = 0

if 'is_processing' not in st.session_state:
    st.session_state.is_processing = False

if 'database_context' not in st.session_state:
    st.session_state.database_context = {}

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ AI Agent Configuration")
    
    # Webhook URL
    webhook_url_input = st.text_input(
        "N8N Webhook URL",
        value=st.session_state.webhook_url,
        placeholder="https://your-n8n.com/webhook/ai-agent",
        help="URL ของ AI Agent endpoint จาก n8n"
    )
    
    if webhook_url_input != st.session_state.webhook_url:
        st.session_state.webhook_url = webhook_url_input
    
    st.markdown("---")
    
    # Database Context Configuration
    st.markdown("### 🗄️ Database Context")
    
    with st.expander("⚙️ ตั้งค่า Database Context"):
        db_type = st.selectbox(
            "ประเภท Database",
            ["PostgreSQL", "MySQL", "SQLite", "MongoDB", "SQL Server", "Other"]
        )
        
        db_schema = st.text_area(
            "Database Schema (Optional)",
            placeholder="ตัวอย่าง:\nCustomers: id, name, email\nOrders: id, customer_id, total",
            help="ข้อมูลโครงสร้าง database เพื่อช่วย AI ทำความเข้าใจ"
        )
        
        special_instructions = st.text_area(
            "คำแนะนำพิเศษ (Optional)",
            placeholder="เช่น: ใช้ชื่อตารางเป็นพหูพจน์, ไม่ใช้ DELETE commands",
            help="ข้อกำหนดพิเศษสำหรับ AI Agent"
        )
        
        if st.button("💾 บันทึก Context"):
            st.session_state.database_context = {
                'db_type': db_type,
                'schema': db_schema,
                'instructions': special_instructions
            }
            st.success("✅ บันทึก Context สำเร็จ!")
    
    if st.session_state.database_context:
        st.info(f"📊 Database: {st.session_state.database_context.get('db_type', 'Not set')}")
    
    st.markdown("---")
    
    # Session Management
    st.markdown("### 🔑 Session Management")
    
    st.text_input(
        "Session ID",
        value=st.session_state.SessionId,
        disabled=True
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 New Session", use_container_width=True):
            st.session_state.SessionId = f"session_{int(time.time())}"
            st.session_state.messages = []
            st.session_state.total_requests = 0
            st.session_state.successful_requests = 0
            st.session_state.total_queries = 0
            st.rerun()
    
    with col2:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    
    st.markdown("---")
    
    # Statistics
    st.markdown("### 📊 สถิติ")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("ข้อความ", len(st.session_state.messages))
        st.metric("SQL Queries", st.session_state.total_queries)
    with col2:
        st.metric("API Calls", st.session_state.total_requests)
        if st.session_state.total_requests > 0:
            success_rate = (st.session_state.successful_requests / st.session_state.total_requests) * 100
            st.metric("Success Rate", f"{success_rate:.0f}%")
    
    st.markdown("---")
    
    # Export
    st.markdown("### 💾 Export")
    
    if st.session_state.messages:
        csv_data = export_chat_history(st.session_state.messages)
        st.download_button(
            label="📥 Download History (CSV)",
            data=csv_data,
            file_name=f"ai_agent_chat_{st.session_state.SessionId}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    st.markdown("---")
    
    # Quick Examples
    with st.expander("💡 ตัวอย่างคำถาม"):
        st.markdown("""
        **สำหรับ Database Queries:**
        - แสดงลูกค้าทั้งหมด
        - หายอดขายรวมของเดือนนี้
        - ใครซื้อสินค้ามากที่สุด 10 อันดับ
        - แสดงกราฟยอดขายรายเดือน
        
        **สำหรับ Data Analysis:**
        - วิเคราะห์แนวโน้มยอดขาย
        - หาลูกค้าที่ไม่ active
        - คำนวณ customer lifetime value
        - สรุปประสิทธิภาพสินค้า
        """)

# Main Area
st.title("🤖 AI Agent: Chat with Database")
st.markdown("ระบบ AI Agent ที่ช่วยคุณสนทนากับ Database ผ่านภาษาธรรมชาติ")

# Warning
if not st.session_state.webhook_url:
    st.warning("⚠️ กรุณาใส่ N8N Webhook URL ในแถบด้านซ้าย")
    st.info("""
    **การตั้งค่า AI Agent:**
    1. สร้าง n8n workflow สำหรับ AI Agent
    2. เชื่อมต่อกับ Database (PostgreSQL, MySQL, etc.)
    3. เพิ่ม AI Model (OpenAI, Claude, etc.)
    4. คัดลอก Webhook URL มาใส่ที่นี่
    """)

# Chat Container
chat_container = st.container()
with chat_container:
    if not st.session_state.messages:
        st.info("""
        👋 **ยินดีต้อนรับสู่ AI Agent Chat!**
        
        ฉันสามารถช่วยคุณ:
        - 🔍 Query ข้อมูลจาก Database ด้วยภาษาธรรมชาติ
        - 📊 วิเคราะห์และสรุปข้อมูล
        - 📈 สร้างรายงานและ insights
        - 💡 แนะนำ optimizations
        
        เริ่มต้นโดยพิมพ์คำถามของคุณด้านล่าง!
        """)
    else:
        for msg in st.session_state.messages:
            # แสดงข้อความ
            metadata = msg.get('metadata', {})
            display_message(
                msg['role'],
                msg['content'],
                msg['timestamp'],
                metadata
            )
            
            # แสดง SQL query ถ้ามี
            if msg.get('sql_query'):
                display_sql_query(msg['sql_query'])
            
            # แสดง data table ถ้ามี
            if msg.get('data'):
                display_data_table(msg['data'])
            
            st.markdown("---")

# Input Area
st.markdown("### 💬 พิมพ์คำถามของคุณ")

with st.form(key="chat_form", clear_on_submit=True):
    col1, col2 = st.columns([5, 1])
    
    with col1:
        user_input = st.text_area(
            "คำถาม",
            placeholder="เช่น: แสดงลูกค้าที่ซื้อสินค้าในเดือนนี้",
            label_visibility="collapsed",
            height=100,
            disabled=st.session_state.is_processing
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        send_button = st.form_submit_button(
            "📤 ส่ง", 
            use_container_width=True, 
            type="primary",
            disabled=st.session_state.is_processing
        )

# Process Input
if send_button and user_input.strip():
    if not st.session_state.webhook_url:
        st.error("❌ กรุณาใส่ N8N Webhook URL ก่อน")
    else:
        st.session_state.is_processing = True
        
        # เพิ่มข้อความผู้ใช้
        user_message = {
            'role': 'user',
            'content': user_input,
            'timestamp': datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }
        st.session_state.messages.append(user_message)
        
        # ส่งไปยัง AI Agent พร้อม context
        st.session_state.total_requests += 1
        response = send_to_ai_agent(
            st.session_state.webhook_url,
            user_input,
            st.session_state.SessionId,
            st.session_state.database_context
        )
        
        # ประมวลผลคำตอบ
        if response['success']:
            st.session_state.successful_requests += 1
            
            # Parse response
            parsed = parse_agent_response(response['data'])
            
            # สร้างข้อความตอบกลับ
            bot_message = {
                'role': 'bot',
                'content': parsed['text'],
                'timestamp': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                'metadata': {
                    'response_time': response.get('response_time', 0),
                    'has_query': parsed['sql_query'] is not None,
                    'has_data': parsed['data'] is not None
                }
            }
            
            # เพิ่ม SQL query ถ้ามี
            if parsed['sql_query']:
                bot_message['sql_query'] = parsed['sql_query']
                st.session_state.total_queries += 1
            
            # เพิ่ม data ถ้ามี
            if parsed['data']:
                bot_message['data'] = parsed['data']
                bot_message['has_data'] = True
            
            st.session_state.messages.append(bot_message)
            
        else:
            # Error message
            error_message = {
                'role': 'bot',
                'content': f"❌ เกิดข้อผิดพลาด:\n{response['error']}",
                'timestamp': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                'metadata': {'error': True}
            }
            st.session_state.messages.append(error_message)
        
        st.session_state.is_processing = False
        st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <small>
        🤖 <strong>AI Agent Chat with Database</strong> | 
        Powered by Streamlit + N8N + AI | 
        Natural Language to SQL
    </small>
</div>
""", unsafe_allow_html=True)
