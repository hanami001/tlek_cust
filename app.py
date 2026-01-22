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

# CSS ที่ปรับปรุงแล้วพร้อม Noto Sans Thai และ UI สวยงาม
st.markdown("""
<style>
    /* Import Google Font - Noto Sans Thai */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@300;400;500;600;700&display=swap');
    
    /* Global Font Settings */
    * {
        font-family: 'Noto Sans Thai', sans-serif !important;
    }
    
    html, body, [class*="css"] {
        font-family: 'Noto Sans Thai', sans-serif !important;
    }
    
    /* Main Container Styling */
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #e8eef5 100%);
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3a8a 0%, #1e40af 100%);
        box-shadow: 2px 0 10px rgba(0,0,0,0.1);
    }
    
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: white !important;
    }
    
    /* Chat Message Styles */
    .chat-message {
        padding: 1.5rem;
        border-radius: 1rem;
        margin-bottom: 1.5rem;
        display: flex;
        flex-direction: column;
        animation: slideIn 0.4s ease-out;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        backdrop-filter: blur(10px);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .chat-message:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.12);
    }
    
    @keyframes slideIn {
        from { 
            opacity: 0; 
            transform: translateX(-20px);
        }
        to { 
            opacity: 1; 
            transform: translateX(0);
        }
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-left: 10%;
        border-bottom-right-radius: 0.3rem;
    }
    
    .bot-message {
        background: white;
        margin-right: 10%;
        border-bottom-left-radius: 0.3rem;
        border-left: 4px solid #667eea;
    }
    
    .message-header {
        font-weight: 600;
        margin-bottom: 0.75rem;
        font-size: 0.95rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        letter-spacing: 0.3px;
    }
    
    .user-message .message-header {
        color: rgba(255,255,255,0.95);
    }
    
    .bot-message .message-header {
        color: #1e3a8a;
    }
    
    .message-content {
        font-size: 1.05rem;
        line-height: 1.8;
        white-space: pre-wrap;
        word-wrap: break-word;
        font-weight: 400;
    }
    
    .user-message .message-content {
        color: white;
    }
    
    .bot-message .message-content {
        color: #334155;
    }
    
    .timestamp {
        font-size: 0.8rem;
        margin-top: 0.75rem;
        opacity: 0.75;
        font-weight: 300;
    }
    
    /* Badge Styles */
    .query-badge {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        padding: 0.4rem 1rem;
        border-radius: 1.5rem;
        font-size: 0.85rem;
        display: inline-block;
        margin-top: 0.75rem;
        font-weight: 500;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
    }
    
    .data-badge {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 0.4rem 1rem;
        border-radius: 1.5rem;
        font-size: 0.85rem;
        display: inline-block;
        margin-top: 0.75rem;
        font-weight: 500;
        box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
    }
    
    /* DataFrame Styling */
    .stDataFrame {
        margin-top: 1.5rem;
        border-radius: 0.75rem;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    
    /* Button Styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 0.75rem;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
    }
    
    /* Input Styling */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 0.75rem;
        border: 2px solid #e2e8f0;
        padding: 1rem;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Metric Styling */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: #1e3a8a;
    }
    
    [data-testid="stMetricLabel"] {
        font-weight: 600;
        color: #64748b;
        font-size: 0.95rem;
    }
    
    /* Code Block Styling */
    code {
        background: #f1f5f9;
        padding: 0.25rem 0.5rem;
        border-radius: 0.375rem;
        font-family: 'Courier New', monospace !important;
    }
    
    pre {
        background: #1e293b;
        border-radius: 0.75rem;
        padding: 1.5rem;
        overflow-x: auto;
    }
    
    /* Title Styling */
    h1 {
        color: #1e3a8a;
        font-weight: 700;
        margin-bottom: 0.5rem;
        letter-spacing: -0.5px;
    }
    
    h2 {
        color: #1e40af;
        font-weight: 600;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    
    h3 {
        color: #3730a3;
        font-weight: 600;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
    }
    
    /* Info Box Styling */
    .stAlert {
        border-radius: 0.75rem;
        border: none;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    /* Expander Styling */
    .streamlit-expanderHeader {
        background: white;
        border-radius: 0.75rem;
        font-weight: 600;
        color: #1e3a8a;
    }
    
    /* Select Box Styling */
    .stSelectbox > div > div {
        border-radius: 0.75rem;
        border: 2px solid #e2e8f0;
    }
    
    /* Download Button Styling */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        border-radius: 0.75rem;
        font-weight: 600;
        border: none;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    }
    
    .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(16, 185, 129, 0.4);
    }
    
    /* Spinner Styling */
    .stSpinner > div {
        border-color: #667eea !important;
    }
    
    /* Divider Styling */
    hr {
        margin: 2rem 0;
        border: none;
        border-top: 2px solid #e2e8f0;
        opacity: 0.5;
    }
    
    /* Card Effect for Containers */
    .element-container {
        transition: all 0.3s ease;
    }
    
    /* Footer Styling */
    .footer {
        background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
        color: white;
        padding: 2rem;
        border-radius: 1rem;
        text-align: center;
        margin-top: 3rem;
        box-shadow: 0 4px 20px rgba(30, 58, 138, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'webhook_url' not in st.session_state:
    st.session_state.webhook_url = ""

if 'SessionId' not in st.session_state:
    st.session_state.SessionId = f"session_{int(time.time())}"

if 'is_processing' not in st.session_state:
    st.session_state.is_processing = False

if 'database_context' not in st.session_state:
    st.session_state.database_context = {}

if 'total_requests' not in st.session_state:
    st.session_state.total_requests = 0

if 'successful_requests' not in st.session_state:
    st.session_state.successful_requests = 0

if 'total_queries' not in st.session_state:
    st.session_state.total_queries = 0

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
                data = response.json() if response.text else {'message': 'Error (Timeout), Please Try Again'}
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
    role_name = "คุณ" if role == "user" else "AI Agent"
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
def display_data_table(data):
    """แสดงข้อมูลในรูปแบบ DataFrame"""
    try:
        if isinstance(data, list) and len(data) > 0:
            df = pd.DataFrame(data)
            st.markdown("**📊 ข้อมูลที่ได้:**")
            st.dataframe(df, use_container_width=True)
            
            # แสดงสถิติเพิ่มเติม
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("จำนวนแถว", len(df))
            with col2:
                st.metric("จำนวนคอลัมน์", len(df.columns))
            with col3:
                st.metric("ขนาดข้อมูล", f"{df.memory_usage(deep=True).sum() / 1024:.2f} KB")
        elif isinstance(data, dict):
            st.markdown("**📊 ข้อมูลที่ได้:**")
            st.json(data)
        else:
            st.markdown("**📊 ข้อมูลที่ได้:**")
            st.write(data)
    except Exception as e:
        st.warning(f"⚠️ ไม่สามารถแสดงข้อมูลในรูปแบบตารางได้: {str(e)}")
        st.json(data)

# ฟังก์ชัน export ประวัติการสนทนา
def export_chat_history(messages):
    """Export ประวัติการสนทนาเป็น CSV"""
    data = []
    for msg in messages:
        data.append({
            'Timestamp': msg['timestamp'],
            'Role': msg['role'],
            'Content': msg['content'],
            'Has_SQL': 'Yes' if msg.get('sql_query') else 'No',
            'Has_Data': 'Yes' if msg.get('data') else 'No'
        })
    
    df = pd.DataFrame(data)
    return df.to_csv(index=False, encoding='utf-8-sig')

# ========================================
# SIDEBAR
# ========================================
with st.sidebar:
    st.markdown("## ⚙️ การตั้งค่า")
    st.markdown("---")
    
    # Webhook URL
    st.markdown("### 🔗 N8N Webhook")
    
    webhook_url = st.text_input(
        "Webhook URL",
        value=st.session_state.webhook_url,
        placeholder="https://your-n8n-instance.com/webhook/...",
        help="URL ของ N8N Webhook ที่เชื่อมต่อกับ AI Agent"
    )
    
    if webhook_url != st.session_state.webhook_url:
        st.session_state.webhook_url = webhook_url
        if webhook_url:
            st.success("✅ บันทึก Webhook URL แล้ว")
    
    st.markdown("---")
    
    # Database Context
    st.markdown("### 🗄️ Database Context")
    
    with st.expander("📝 ตั้งค่า Database", expanded=False):
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
        
        if st.button("💾 บันทึก Context", use_container_width=True):
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

# ========================================
# MAIN AREA
# ========================================
st.title("🤖 AI Agent: Chat with Database")
st.markdown("### ระบบ AI Agent ที่ช่วยคุณสนทนากับ Database ผ่านภาษาธรรมชาติ")

# Warning
if not st.session_state.webhook_url:
    st.warning("⚠️ กรุณาใส่ N8N Webhook URL ในแถบด้านซ้าย")
    
    st.info("""
    **📝 การตั้งค่า AI Agent:**
    
    1. สร้าง n8n workflow สำหรับ AI Agent
    2. เชื่อมต่อกับ Database (PostgreSQL, MySQL, etc.)
    3. เพิ่ม AI Model (OpenAI, Claude, etc.)
    4. คัดลอก Webhook URL มาใส่ที่นี่
    """)

# Chat Container
chat_container = st.container()
with chat_container:
    if not st.session_state.messages:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 2rem; border-radius: 1rem; color: white; 
                    box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);'>
            <h2 style='color: white; margin-top: 0;'>👋 ยินดีต้อนรับสู่ AI Agent Chat!</h2>
            <p style='font-size: 1.1rem; line-height: 1.8; color: rgba(255,255,255,0.95);'>
                ฉันสามารถช่วยคุณ:<br><br>
                🔍 Query ข้อมูลจาก Database ด้วยภาษาธรรมชาติ<br>
                📊 วิเคราะห์และสรุปข้อมูล<br>
                📈 สร้างรายงานและ insights<br>
                💡 แนะนำ optimizations<br><br>
                <strong>เริ่มต้นโดยพิมพ์คำถามของคุณด้านล่าง! 👇</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)
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
            
            st.markdown("<div style='margin: 1rem 0;'></div>", unsafe_allow_html=True)

# Input Area
st.markdown("---")
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
<div class='footer'>
    <h3 style='color: white; margin-top: 0;'>🤖 AI Agent Chat with Database</h3>
    <p style='color: rgba(255,255,255,0.9); margin-bottom: 0;'>
        Powered by Streamlit + N8N + AI | Natural Language to SQL
    </p>
    <p style='color: rgba(255,255,255,0.7); font-size: 0.9rem; margin-top: 0.5rem;'>
        สร้างด้วย ❤️ และ AI Technology
    </p>
</div>
""", unsafe_allow_html=True)
