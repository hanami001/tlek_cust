import streamlit as st
import requests
import json
from datetime import datetime
import time
import pandas as pd
from io import StringIO
import base64
import re

# ตั้งค่าหน้าเว็บ
st.set_page_config(
    page_title="AI Agent Chat with Database",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS ที่ปรับปรุงแล้ว พร้อม Noto Sans Thai และ UI ที่สวยงามขึ้น
st.markdown("""
<style>
    /* Import Noto Sans Thai */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@300;400;500;600;700&display=swap');
    
    /* Global Font */
    * {
        font-family: 'Noto Sans Thai', sans-serif !important;
    }
    
    .stTextArea textarea, .stTextInput input, .stSelectbox select {
        font-family: 'Noto Sans Thai', sans-serif !important;
    }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #888;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #555;
    }
    
    /* Chat Message Styling */
    .chat-message {
        padding: 1.2rem 1.5rem;
        border-radius: 1rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
        animation: fadeIn 0.3s ease-in;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .chat-message:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-left: 10%;
    }
    
    .bot-message {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        margin-right: 10%;
        border: 1px solid #e9ecef;
    }
    
    .message-header {
        font-weight: 600;
        margin-bottom: 0.75rem;
        font-size: 0.9rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .user-message .message-header {
        color: rgba(255,255,255,0.95);
    }
    
    .bot-message .message-header {
        color: #1a202c;
    }
    
    /* แก้ไขปัญหาการเว้นบรรทัดมากเกินไป */
    .message-content {
        font-size: 1rem;
        line-height: 1.7;
        word-wrap: break-word;
        color: #2d3748;
    }
    
    /* ลบช่องว่างที่มากเกินไป */
    .message-content p {
        margin: 0.5rem 0 !important;
    }
    
    .message-content br + br {
        display: none;
    }
    
    .user-message .message-content {
        color: white;
    }
    
    .timestamp {
        font-size: 0.75rem;
        margin-top: 0.75rem;
        opacity: 0.75;
        font-weight: 400;
    }
    
    /* Badges */
    .query-badge, .data-badge {
        padding: 0.3rem 0.8rem;
        border-radius: 1.5rem;
        font-size: 0.75rem;
        display: inline-block;
        margin-top: 0.5rem;
        font-weight: 500;
    }
    
    .query-badge {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
    }
    
    .data-badge {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        box-shadow: 0 2px 4px rgba(16, 185, 129, 0.3);
    }
    
    /* DataFrame Styling */
    .stDataFrame {
        margin: 1rem 0;
        border-radius: 0.5rem;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    
    /* Code Block Styling */
    .stCodeBlock {
        border-radius: 0.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    
    /* Button Improvements */
    .stButton > button {
        border-radius: 0.5rem;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    /* Form Styling */
    .stTextArea textarea {
        border-radius: 0.75rem;
        border: 2px solid #e2e8f0;
        font-size: 1rem;
        transition: border-color 0.2s ease;
    }
    
    .stTextArea textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Sidebar Improvements */
    .css-1d391kg {
        background: linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%);
    }
    
    /* Metric Card Styling */
    .stMetric {
        background: white;
        padding: 1rem;
        border-radius: 0.75rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Info/Warning/Success Boxes */
    .stAlert {
        border-radius: 0.75rem;
        border-left: 4px solid;
        font-weight: 400;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Divider */
    hr {
        margin: 1.5rem 0;
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #e2e8f0, transparent);
    }
</style>
""", unsafe_allow_html=True)

# ฟังก์ชันทำความสะอาดข้อความ (ลบบรรทัดว่างที่มากเกินไป)
def clean_text_spacing(text):
    """
    ทำความสะอาดข้อความโดยลดการเว้นบรรทัดที่มากเกินไป
    """
    if not text:
        return text
    
    # แทนที่บรรทัดว่างมากกว่า 2 บรรทัด ด้วย 1 บรรทัด
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    
    # ลบช่องว่างที่ตอนท้ายและต้นของแต่ละบรรทัด
    lines = [line.rstrip() for line in text.split('\n')]
    text = '\n'.join(lines)
    
    # ลบช่องว่างที่ตอนต้นและท้ายของข้อความทั้งหมด
    text = text.strip()
    
    return text

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
        parsed['text'] = clean_text_spacing(response_data)
        return parsed
    
    if isinstance(response_data, dict):
        # ลำดับความสำคัญของ keys สำหรับข้อความ
        text_keys = ['response', 'message', 'output', 'reply', 'text', 'answer', 'result']
        
        for key in text_keys:
            if key in response_data:
                parsed['text'] = clean_text_spacing(str(response_data[key]))
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
    
    # ทำความสะอาดเนื้อหาก่อนแสดงผล
    clean_content = clean_text_spacing(content)
    
    # แปลง newlines เป็น <br> สำหรับ HTML
    html_content = clean_content.replace('\n', '<br>')
    
    st.markdown(f"""
    <div class="chat-message {message_class}">
        <div class="message-header">
            <span>{icon}</span>
            <span>{role_name}</span>
        </div>
        <div class="message-content">{html_content}</div>
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
    """แสดงข้อมูลในรูปแบบตาราง"""
    try:
        if isinstance(data, list):
            if len(data) > 0:
                df = pd.DataFrame(data)
                st.markdown("**📊 ผลลัพธ์:**")
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True
                )
                st.caption(f"จำนวนแถว: {len(df)} แถว")
            else:
                st.info("ไม่พบข้อมูล")
        elif isinstance(data, dict):
            df = pd.DataFrame([data])
            st.markdown("**📊 ผลลัพธ์:**")
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info(f"ข้อมูล: {data}")
    except Exception as e:
        st.error(f"ไม่สามารถแสดงข้อมูลได้: {str(e)}")
        st.json(data)

# ฟังก์ชัน Export Chat History
def export_chat_history(messages):
    """Export ประวัติการสนทนาเป็น CSV"""
    data = []
    for msg in messages:
        row = {
            'Timestamp': msg['timestamp'],
            'Role': msg['role'],
            'Content': msg['content'],
            'SQL_Query': msg.get('sql_query', ''),
            'Has_Data': 'Yes' if msg.get('data') else 'No'
        }
        data.append(row)
    
    df = pd.DataFrame(data)
    return df.to_csv(index=False).encode('utf-8-sig')

# Initialize Session State
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'webhook_url' not in st.session_state:
    st.session_state.webhook_url = ""

if 'SessionId' not in st.session_state:
    st.session_state.SessionId = f"session_{int(time.time())}"

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
    st.markdown("## ⚙️ การตั้งค่า")
    
    # N8N Webhook URL
    webhook_url = st.text_input(
        "N8N Webhook URL",
        value=st.session_state.webhook_url,
        placeholder="https://your-n8n.app/webhook/...",
        help="URL ของ N8N webhook ที่เชื่อมต่อกับ AI Agent"
    )
    
    if webhook_url != st.session_state.webhook_url:
        st.session_state.webhook_url = webhook_url
        st.rerun()
    
    if st.session_state.webhook_url:
        st.success("✅ เชื่อมต่อแล้ว")
    
    st.markdown("---")
    
    # Database Context
    with st.expander("🗄️ Database Context", expanded=False):
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
<div style='text-align: center; color: #718096; padding: 1.5rem;'>
    <div style='margin-bottom: 0.5rem;'>
        <strong style='font-size: 1.1rem;'>🤖 AI Agent Chat with Database</strong>
    </div>
    <div style='font-size: 0.9rem;'>
        Powered by Streamlit + N8N + AI | Natural Language to SQL
    </div>
    <div style='margin-top: 0.75rem; font-size: 0.85rem; opacity: 0.8;'>
        ปรับปรุงโดย Senior Web Developer & Data Science Team
    </div>
</div>
""", unsafe_allow_html=True)
