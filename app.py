import streamlit as st
import requests
import json
from datetime import datetime
import time
import pandas as pd
import re  # เพิ่ม regex เพื่อจัดการ whitespace
from io import StringIO
import base64

# -----------------------------------------------------------------------------
# 1. Configuration & Setup
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="TLEK Customer Data Intelligence Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 2. Modern UI & CSS Styling (Noto Sans Thai & Spacing Fixes)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    /* Import Font: Noto Sans Thai */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@300;400;500;600;700&display=swap');

    /* Global Font Settings */
    html, body, [class*="css"], .stTextInput, .stTextArea, .stButton {
        font-family: 'Noto Sans Thai', sans-serif !important;
    }

    /* Chat Container Structure */
    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 1rem;
        padding: 1rem 0;
    }

    /* Message Bubbles Common Style */
    .chat-message {
        padding: 1.25rem;
        border-radius: 12px;
        position: relative;
        max-width: 85%;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        animation: fadeIn 0.3s ease-in-out;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(5px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Bot Message (Left) */
    .bot-message {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        color: #1f2937;
        margin-right: auto;
        border-top-left-radius: 2px;
    }

    /* User Message (Right) */
    .user-message {
        background-color: #2563EB; /* Modern Blue */
        color: #ffffff;
        margin-left: auto;
        border-top-right-radius: 2px;
    }

    /* Header in Message */
    .message-header {
        font-size: 0.75rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        opacity: 0.8;
    }
    
    .bot-message .message-header { color: #6b7280; }
    .user-message .message-header { color: #e0e7ff; justify-content: flex-end; }

    /* Content Typography & Spacing Fixes */
    .message-content {
        font-size: 0.95rem;
        line-height: 1.6;
        word-wrap: break-word;
    }

    /* Fix Excessive Markdown Spacing */
    .message-content p { margin-bottom: 0.6em; }
    .message-content p:last-child { margin-bottom: 0; }
    .message-content ul, .message-content ol { margin-bottom: 0.6em; padding-left: 1.5rem; }
    .message-content pre { margin: 0.5rem 0; border-radius: 8px; }
    
    /* Tables in Chat */
    .stDataFrame { margin-top: 0.5rem; border-radius: 8px; overflow: hidden; }

    /* Footer Metadata */
    .timestamp {
        font-size: 0.7rem;
        margin-top: 0.5rem;
        opacity: 0.6;
        text-align: right;
    }
    
    /* Custom Scrollbar for better aesthetics */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #f1f1f1; }
    ::-webkit-scrollbar-thumb { background: #c1c1c1; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #a8a8a8; }

</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. Helper Functions
# -----------------------------------------------------------------------------

def clean_text_spacing(text):
    """
    Utility function to clean excessive newlines from AI response.
    Reduces 3+ newlines to 2, and trims surrounding whitespace.
    """
    if not text:
        return ""
    # Normalize line endings
    text = text.replace('\r\n', '\n')
    # Replace 3 or more newlines with 2 (preserve paragraph break but remove huge gaps)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def parse_agent_response(response_data):
    """Parse response from AI Agent handling various JSON structures."""
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
        # Text extraction
        text_keys = ['response', 'message', 'output', 'reply', 'text', 'answer', 'result']
        for key in text_keys:
            if key in response_data:
                parsed['text'] = clean_text_spacing(str(response_data[key]))
                break
        
        # SQL extraction
        sql_keys = ['sql', 'query', 'sql_query', 'generated_sql', 'executed_query']
        for key in sql_keys:
            if key in response_data and response_data[key]:
                parsed['sql_query'] = response_data[key]
                break
        
        # Data extraction
        data_keys = ['data', 'results', 'rows', 'records', 'query_results']
        for key in data_keys:
            if key in response_data and response_data[key]:
                parsed['data'] = response_data[key]
                break
        
        # Metadata extraction
        metadata_keys = ['metadata', 'info', 'stats', 'summary']
        for key in metadata_keys:
            if key in response_data and response_data[key]:
                parsed['metadata'] = response_data[key]
                break
        
        # Fallback
        if not parsed['text']:
            parsed['text'] = json.dumps(response_data, indent=2, ensure_ascii=False)
    
    return parsed

def send_to_ai_agent(webhook_url, message, session_id=None, context=None):
    """Send message to n8n webhook with robust error handling."""
    try:
        payload = {
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "SessionId": session_id or st.session_state.get('SessionId', 'default'),
        }
        
        if context:
            payload["context"] = context
        
        if st.session_state.get('messages'):
            recent_messages = st.session_state.messages[-5:]
            payload["conversation_history"] = [
                {"role": msg['role'], "content": msg['content']}
                for msg in recent_messages
            ]
        
        headers = {"Content-Type": "application/json"}
        
        with st.spinner('Waiting for Agent...'):
            start_time = time.time()
            response = requests.post(webhook_url, json=payload, headers=headers, timeout=60)
            response_time = time.time() - start_time
        
        if response.status_code == 200:
            try:
                data = response.json() if response.text else {'message': 'Error (Timeout), Please Try Again'}
            except json.JSONDecodeError:
                data = {'message': response.text}
            
            return {'success': True, 'data': data, 'status_code': response.status_code, 'response_time': round(response_time, 2)}
        else:
            return {'success': False, 'error': f'HTTP {response.status_code}: {response.text[:500]}', 'status_code': response.status_code, 'response_time': round(response_time, 2)}
    
    except requests.exceptions.Timeout:
        return {'success': False, 'error': '⏱️ Request timeout - Query is taking too long.'}
    except requests.exceptions.ConnectionError:
        return {'success': False, 'error': '🔌 Connection Error - Check webhook URL.'}
    except Exception as e:
        return {'success': False, 'error': f'❌ System Error: {str(e)}'}

def display_message(role, content, timestamp, metadata=None):
    """Render chat message with updated CSS classes."""
    message_class = "user-message" if role == "user" else "bot-message"
    role_label = "You" if role == "user" else "AI Agent"
    icon = "👤" if role == "user" else "🤖"
    
    # Metadata badges
    meta_html = ""
    if metadata:
        badges = []
        if 'response_time' in metadata:
            badges.append(f"⚡ {metadata['response_time']}s")
        if metadata.get('has_query'):
            badges.append("🔍 SQL")
        if metadata.get('has_data'):
            badges.append("📊 Data")
        
        if badges:
            meta_html = f"<span>{' • '.join(badges)}</span>"

    st.markdown(f"""
    <div class="chat-message {message_class}">
        <div class="message-header">
            <span>{icon} {role_label}</span>
        </div>
        <div class="message-content">{content}</div>
        <div class="timestamp">{timestamp} {f'• {meta_html}' if meta_html else ''}</div>
    </div>
    """, unsafe_allow_html=True)

def display_sql_query(query):
    with st.expander("🔍 View Generated SQL", expanded=False):
        st.code(query, language='sql')

def display_data_table(data):
    if isinstance(data, list) and len(data) > 0:
        df = pd.DataFrame(data)
        st.markdown(f"**📊 Query Results ({len(df)} rows)**")
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"data_export_{int(time.time())}.csv",
            mime="text/csv",
            key=f"dl_{int(time.time())}"
        )
    elif isinstance(data, dict):
        st.json(data)
    else:
        st.write(data)

# -----------------------------------------------------------------------------
# 4. State Initialization
# -----------------------------------------------------------------------------
if 'messages' not in st.session_state: st.session_state.messages = []
if 'SessionId' not in st.session_state: st.session_state.SessionId = f"sess_{int(time.time())}"
if 'webhook_url' not in st.session_state: st.session_state.webhook_url = ""
if 'stats' not in st.session_state: st.session_state.stats = {'total': 0, 'success': 0, 'queries': 0}
if 'database_context' not in st.session_state: st.session_state.database_context = {}

# -----------------------------------------------------------------------------
# 5. Sidebar Layout
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=60)
    st.title("Settings")
    
    st.subheader("🔌 Connection")
    webhook_url_input = st.text_input(
        "N8N Webhook URL",
        value=st.session_state.webhook_url,
        placeholder="https://n8n.example.com/webhook/...",
        type="password" # Hide for cleaner UI unless focused
    )
    if webhook_url_input != st.session_state.webhook_url:
        st.session_state.webhook_url = webhook_url_input

    st.divider()

    with st.expander("🗄️ Database Context", expanded=False):
        db_type = st.selectbox("Database Type", ["PostgreSQL", "MySQL", "SQL Server", "MongoDB", "Other"])
        db_schema = st.text_area("Schema Definition", placeholder="Table: users\nColumns: id, name, email", height=150)
        instructions = st.text_area("Custom Instructions", placeholder="e.g. Always limit to 10 rows")
        
        if st.button("Update Context", use_container_width=True):
            st.session_state.database_context = {'db_type': db_type, 'schema': db_schema, 'instructions': instructions}
            st.success("Context Updated!")

    st.divider()
    
    # Session Info
    st.caption(f"Session ID: {st.session_state.SessionId}")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    with col2:
        if st.button("🔄 New", use_container_width=True):
            st.session_state.SessionId = f"sess_{int(time.time())}"
            st.session_state.messages = []
            st.rerun()

# -----------------------------------------------------------------------------
# 6. Main Content
# -----------------------------------------------------------------------------
st.title("🤖 TLEK Customer Intelligence Agent")
st.caption("Chat with your database using natural language • Powered by N8N")

# Chat History Display
chat_container = st.container()
with chat_container:
    if not st.session_state.messages:
        st.markdown("""
        <div style='text-align: center; padding: 3rem 1rem; color: #6b7280; background: #f9fafb; border-radius: 12px; border: 1px dashed #e5e7eb;'>
            <h3>👋 Welcome!</h3>
            <p>I can help you query data, analyze trends, and generate insights.</p>
            <p style='font-size: 0.9rem;'>Try asking: <em>"Show me total sales for last month"</em></p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in st.session_state.messages:
            metadata = msg.get('metadata', {})
            display_message(msg['role'], msg['content'], msg['timestamp'], metadata)
            
            if msg.get('sql_query'):
                display_sql_query(msg['sql_query'])
            
            if msg.get('data'):
                display_data_table(msg['data'])

st.markdown("---")

# Input Area (Sticky-like feel via container)
with st.container():
    with st.form(key="chat_form", clear_on_submit=True):
        col_in, col_btn = st.columns([6, 1], gap="small")
        with col_in:
            user_input = st.text_input(
                "Query", 
                placeholder="พิมพ์คำถามของคุณที่นี่... (e.g. สรุปยอดขายสินค้าตามหมวดหมู่)", 
                label_visibility="collapsed"
            )
        with col_btn:
            submit_btn = st.form_submit_button("ส่งข้อความ", use_container_width=True, type="primary")

# Logic Implementation
if submit_btn and user_input.strip():
    if not st.session_state.webhook_url:
        st.error("⚠️ Please configure the Webhook URL in the sidebar.")
    else:
        # Add User Message
        user_msg = {
            'role': 'user',
            'content': user_input,
            'timestamp': datetime.now().strftime("%H:%M")
        }
        st.session_state.messages.append(user_msg)
        st.session_state.stats['total'] += 1
        
        # Get Response
        response = send_to_ai_agent(
            st.session_state.webhook_url, 
            user_input, 
            st.session_state.SessionId, 
            st.session_state.database_context
        )
        
        if response['success']:
            st.session_state.stats['success'] += 1
            parsed = parse_agent_response(response['data'])
            
            bot_msg = {
                'role': 'bot',
                'content': parsed['text'],
                'timestamp': datetime.now().strftime("%H:%M"),
                'metadata': {
                    'response_time': response.get('response_time', 0),
                    'has_query': bool(parsed['sql_query']),
                    'has_data': bool(parsed['data'])
                }
            }
            if parsed['sql_query']: bot_msg['sql_query'] = parsed['sql_query']
            if parsed['data']: bot_msg['data'] = parsed['data']
            
            st.session_state.messages.append(bot_msg)
        else:
            err_msg = {
                'role': 'bot',
                'content': f"❌ Error: {response['error']}",
                'timestamp': datetime.now().strftime("%H:%M"),
                'metadata': {'error': True}
            }
            st.session_state.messages.append(err_msg)
            
        st.rerun()
