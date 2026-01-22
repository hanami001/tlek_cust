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

# CSS ที่ปรับปรุงแล้ว รองรับ tables และ code blocks
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Noto Sans Thai', sans-serif;
    }
    
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
        word-wrap: break-word;
        overflow-wrap: break-word;
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
    
    /* Markdown Styling for Bot Messages */
    .bot-message h1, .bot-message h2, .bot-message h3, .bot-message h4 {
        color: #1e40af;
        margin-top: 1.5rem;
        margin-bottom: 0.8rem;
        font-weight: 600;
        border-bottom: 2px solid #3b82f6;
        padding-bottom: 0.3rem;
    }
    
    .bot-message h2 {
        font-size: 1.4rem;
    }
    
    .bot-message h3 {
        font-size: 1.2rem;
        border-bottom: 1px solid #93c5fd;
    }
    
    .bot-message strong {
        color: #1e3a8a;
        font-weight: 600;
    }
    
    .bot-message ul, .bot-message ol {
        margin: 1rem 0;
        padding-left: 1.5rem;
    }
    
    .bot-message li {
        margin: 0.5rem 0;
        line-height: 1.8;
    }
    
    .bot-message li::marker {
        color: #3b82f6;
        font-weight: bold;
    }
    
    .bot-message code {
        background: #f1f5f9;
        padding: 0.2rem 0.4rem;
        border-radius: 0.25rem;
        font-family: 'Courier New', monospace;
        color: #dc2626;
        font-size: 0.9em;
    }
    
    .bot-message blockquote {
        border-left: 4px solid #3b82f6;
        margin: 1rem 0;
        padding: 0.5rem 1rem;
        background: #eff6ff;
        border-radius: 0.25rem;
    }
    
    .bot-message table {
        border-collapse: collapse;
        width: 100%;
        margin: 1rem 0;
        background: white;
        border-radius: 0.5rem;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .bot-message th {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        padding: 0.75rem;
        text-align: left;
        font-weight: 600;
    }
    
    .bot-message td {
        padding: 0.75rem;
        border-bottom: 1px solid #e5e7eb;
    }
    
    .bot-message tr:hover {
        background: #f9fafb;
    }
    
    /* Highlight boxes */
    .highlight-box {
        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
        border-left: 4px solid #3b82f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .warning-box {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border-left: 4px solid #f59e0b;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .success-box {
        background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
        border-left: 4px solid #10b981;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .stat-card {
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
        border-left: 4px solid #3b82f6;
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: 700;
        color: #1e40af;
        margin: 0.5rem 0;
    }
    
    .stat-label {
        font-size: 0.9rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
</style>
""", unsafe_allow_html=True)

# ฟังก์ชันทำความสะอาดข้อความ
def clean_text(text):
    """
    ทำความสะอาดข้อความโดยลบ line breaks ที่มากเกินไป
    และปรับให้แสดงผลสวยงาม
    """
    if not text:
        return ""
    
    # แปลงเป็น string ถ้ายังไม่ใช่
    text = str(text)
    
    # ลบ line breaks มากเกิน 2 ครั้งติดกัน (เหลือแค่ 2)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # ลบช่องว่างที่ต้นและท้ายบรรทัด
    lines = text.split('\n')
    lines = [line.rstrip() for line in lines]
    text = '\n'.join(lines)
    
    # ลบช่องว่างที่ต้นและท้ายข้อความทั้งหมด
    text = text.strip()
    
    return text

# ฟังก์ชันแปลง markdown เป็น HTML ที่สวยงาม
def format_markdown_content(text):
    """
    แปลง markdown text เป็น HTML พร้อม styling
    """
    if not text:
        return ""
    
    # ทำความสะอาดข้อความก่อน
    text = clean_text(text)
    
    # แปลง markdown tables เป็น HTML tables
    def convert_markdown_table(match):
        table_text = match.group(0)
        lines = [line.strip() for line in table_text.strip().split('\n') if line.strip()]
        
        if len(lines) < 2:
            return table_text
        
        # แยก header และ rows
        header_line = lines[0]
        separator_line = lines[1] if len(lines) > 1 else None
        data_lines = lines[2:] if len(lines) > 2 else []
        
        # ตรวจสอบว่าเป็น markdown table จริงหรือไม่
        if not separator_line or not re.match(r'\|[\s\-:]+\|', separator_line):
            return table_text
        
        # Parse header
        headers = [col.strip() for col in header_line.split('|') if col.strip()]
        
        # สร้าง HTML table
        html = '<table style="width:100%; border-collapse: collapse; margin: 1rem 0; background: white; border-radius: 0.5rem; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">'
        
        # Header
        html += '<thead><tr style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);">'
        for header in headers:
            html += f'<th style="color: white; padding: 0.75rem; text-align: left; font-weight: 600; font-family: \'Noto Sans Thai\', sans-serif;">{header}</th>'
        html += '</tr></thead>'
        
        # Body
        html += '<tbody>'
        for idx, line in enumerate(data_lines):
            cols = [col.strip() for col in line.split('|') if col.strip()]
            if not cols:
                continue
            
            bg_color = '#f9fafb' if idx % 2 == 1 else 'white'
            html += f'<tr style="background: {bg_color};">'
            for col in cols:
                html += f'<td style="padding: 0.75rem; border-bottom: 1px solid #e5e7eb; font-family: \'Noto Sans Thai\', sans-serif;">{col}</td>'
            html += '</tr>'
        html += '</tbody></table>'
        
        # เพิ่ม CSS สำหรับ hover
        html += '<style>table tbody tr:hover { background: #e5e7eb !important; transition: background 0.2s ease; }</style>'
        
        return html
    
    # จับ markdown table pattern (ต้องมีอย่างน้อย 2 บรรทัด และมี separator)
    text = re.sub(
        r'(?:^\|.+\|\s*$\n)+',
        convert_markdown_table,
        text,
        flags=re.MULTILINE
    )
    
    # จัดการกับ QuickChart URLs ที่ caption และ URL แยกคนละบรรทัด
    # รองรับ URL ที่ยาวหลายบรรทัด
    def convert_caption_and_url(match):
        caption = match.group(1).strip()
        url_parts = match.group(2).strip()
        
        # รวม URL ที่อาจถูกแบ่งเป็นหลายบรรทัด (ลบ newlines และ spaces)
        url_parts = re.sub(r'\s+', '', url_parts)
        
        # เติม URL ส่วนหน้า
        if not url_parts.startswith('http'):
            full_url = 'https://quickchart.io/chart?c=' + url_parts
        else:
            full_url = url_parts
        
        # ลบวงเล็บปิดท้าย ถ้ามี
        full_url = full_url.rstrip(')')
        
        return f'<div style="margin: 1.5rem 0; text-align: center;"><img src="{full_url}" alt="{caption}" style="max-width: 100%; height: auto; border-radius: 0.5rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);" onerror="this.style.display=\'none\'; this.nextElementSibling.innerHTML=\'⚠️ ไม่สามารถโหลดกราฟได้ กรุณาตรวจสอบข้อมูล\';" /><div style="margin-top: 0.5rem; font-size: 0.9rem; color: #64748b; font-style: italic;">{caption}</div></div>'
    
    # จับ pattern: บรรทัดข้อความ (caption) ตามด้วย encoded URL (อาจหลายบรรทัด)
    # Pattern นี้จะจับทุกอย่างที่เป็น encoded characters จนกว่าจะเจอบรรทัดว่างหรือจบข้อความ
    text = re.sub(
        r'^([^\n%\|#]+)\n+([%\w\d\-_\.\:\,\{\}\[\]\(\)]+(?:\n[%\w\d\-_\.\:\,\{\}\[\]\(\)]+)*)\)?$',
        convert_caption_and_url,
        text,
        flags=re.MULTILINE
    )
    
    # แปลง markdown images ![alt](url) เป็น HTML img tag
    # รองรับทั้ง QuickChart และ image URLs อื่นๆ
    def convert_image(match):
        alt_text = match.group(1)
        img_url = match.group(2)
        
        # แก้ไข URL ที่ไม่สมบูรณ์ (ขาดส่วนหน้า)
        if img_url.startswith('%') or (not img_url.startswith('http') and not img_url.startswith('//')):
            # ถ้าดูเหมือน QuickChart URL ที่ขาดส่วนหน้า
            if '%22' in img_url or '%3A' in img_url:
                img_url = 'https://quickchart.io/chart?c=' + img_url
        
        return f'<div style="margin: 1.5rem 0; text-align: center;"><img src="{img_url}" alt="{alt_text}" style="max-width: 100%; height: auto; border-radius: 0.5rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);" /><div style="margin-top: 0.5rem; font-size: 0.9rem; color: #64748b; font-style: italic;">{alt_text}</div></div>'
    
    text = re.sub(r'!\[([^\]]*)\]\(([^\)]+)\)', convert_image, text)
    
    # แปลง markdown headers (##, ###)
    text = re.sub(r'^### (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.+)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
    
    # แปลง **bold** text
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    
    # แปลง bullet lists (- หรือ *)
    def convert_list(match):
        items = match.group(0)
        lines = items.strip().split('\n')
        html_items = []
        for line in lines:
            item_text = re.sub(r'^[\-\*]\s+', '', line)
            html_items.append(f'<li>{item_text}</li>')
        return '<ul>' + ''.join(html_items) + '</ul>'
    
    # จับ bullet list ที่ติดกัน
    text = re.sub(r'(?:^[\-\*]\s+.+$\n?)+', convert_list, text, flags=re.MULTILINE)
    
    # แปลง numbered lists
    def convert_numbered_list(match):
        items = match.group(0)
        lines = items.strip().split('\n')
        html_items = []
        for line in lines:
            item_text = re.sub(r'^\d+\.\s+', '', line)
            html_items.append(f'<li>{item_text}</li>')
        return '<ol>' + ''.join(html_items) + '</ol>'
    
    text = re.sub(r'(?:^\d+\.\s+.+$\n?)+', convert_numbered_list, text, flags=re.MULTILINE)
    
    # แปลง emojis พิเศษเป็น styled boxes
    # ⚠️ warning
    text = re.sub(r'⚠️\s*(.+?)(?=\n|$)', r'<div class="warning-box">⚠️ \1</div>', text)
    # ✅ success
    text = re.sub(r'✅\s*(.+?)(?=\n|$)', r'<div class="success-box">✅ \1</div>', text)
    # 📊 info/stats
    text = re.sub(r'📊\s*(.+?)(?=\n|$)', r'<div class="highlight-box">📊 \1</div>', text)
    
    # แปลง code blocks
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    
    # แปลง line breaks ปกติเป็น <br>
    text = text.replace('\n', '<br>')
    
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
        parsed['text'] = clean_text(response_data)
        return parsed
    
    if isinstance(response_data, dict):
        # ลำดับความสำคัญของ keys สำหรับข้อความ
        text_keys = ['response', 'message', 'output', 'reply', 'text', 'answer', 'result']
        
        for key in text_keys:
            if key in response_data:
                parsed['text'] = clean_text(str(response_data[key]))
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
            parsed['text'] = clean_text(json.dumps(response_data, indent=2, ensure_ascii=False))
    
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
    
    # สำหรับ bot message ใช้ markdown formatting
    if role == "bot":
        html_content = format_markdown_content(content)
    else:
        # สำหรับ user message ใช้แค่ clean text
        clean_content = clean_text(content)
        html_content = clean_content.replace('\n', '<br>')
    
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
    """แสดงข้อมูลในรูปแบบ DataFrame พร้อม styling"""
    try:
        if isinstance(data, list) and len(data) > 0:
            df = pd.DataFrame(data)
            
            # สร้าง HTML table
            st.markdown("**📊 ผลลัพธ์จากฐานข้อมูล:**")
            
            # สร้าง HTML table header
            html_table = '<table style="width:100%; border-collapse: collapse; margin: 1rem 0; background: white; border-radius: 0.5rem; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">'
            
            # Header row
            html_table += '<thead><tr style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);">'
            for col in df.columns:
                html_table += f'<th style="color: white; padding: 0.75rem; text-align: left; font-weight: 600; font-family: \'Noto Sans Thai\', sans-serif;">{col}</th>'
            html_table += '</tr></thead>'
            
            # Body rows
            html_table += '<tbody>'
            for idx, row in df.iterrows():
                bg_color = '#f9fafb' if idx % 2 == 1 else 'white'
                html_table += f'<tr style="background: {bg_color};">'
                for val in row:
                    # จัดการค่า None/NaN
                    display_val = str(val) if pd.notna(val) else '-'
                    html_table += f'<td style="padding: 0.75rem; border-bottom: 1px solid #e5e7eb; font-family: \'Noto Sans Thai\', sans-serif;">{display_val}</td>'
                html_table += '</tr>'
            html_table += '</tbody></table>'
            
            # เพิ่ม CSS สำหรับ hover effect
            st.markdown("""
            <style>
            table tbody tr:hover {
                background: #e5e7eb !important;
                transition: background 0.2s ease;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # แสดง HTML table
            st.markdown(html_table, unsafe_allow_html=True)
            
            # แสดงสถิติพื้นฐานในรูปแบบ card
            st.markdown('<div style="margin-top: 1.5rem;">', unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-label">จำนวนแถว</div>
                    <div class="stat-number">{len(df):,}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-label">จำนวนคอลัมน์</div>
                    <div class="stat-number">{len(df.columns)}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                memory_kb = df.memory_usage(deep=True).sum() / 1024
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-label">ขนาดข้อมูล</div>
                    <div class="stat-number">{memory_kb:.1f} KB</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # เพิ่มปุ่ม download CSV
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 ดาวน์โหลด CSV",
                data=csv,
                file_name=f"data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )
                
        elif isinstance(data, dict):
            st.markdown("**📊 ผลลัพธ์:**")
            # แสดง dict ในรูป JSON ที่สวยงาม
            json_str = json.dumps(data, indent=2, ensure_ascii=False)
            st.markdown(f'<pre style="background: #f1f5f9; padding: 1rem; border-radius: 0.5rem; overflow-x: auto; font-family: \'Courier New\', monospace;">{json_str}</pre>', unsafe_allow_html=True)
        else:
            st.markdown("**📊 ผลลัพธ์:**")
            st.write(data)
            
    except Exception as e:
        st.error(f"ไม่สามารถแสดงข้อมูลได้: {str(e)}")
        st.json(data)

# ฟังก์ชัน Export Chat History
def export_chat_history(messages):
    """Export chat history เป็น CSV"""
    data = []
    for msg in messages:
        data.append({
            'Timestamp': msg['timestamp'],
            'Role': msg['role'],
            'Content': msg['content'],
            'SQL Query': msg.get('sql_query', ''),
            'Has Data': msg.get('has_data', False)
        })
    
    df = pd.DataFrame(data)
    return df.to_csv(index=False).encode('utf-8-sig')

# Initialize Session State
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'webhook_url' not in st.session_state:
    st.session_state.webhook_url = ""

if 'SessionId' not in st.session_state:
    st.session_state.SessionId = f"session_{int(time.time())}"

if 'is_processing' not in st.session_state:
    st.session_state.is_processing = False

if 'total_requests' not in st.session_state:
    st.session_state.total_requests = 0

if 'successful_requests' not in st.session_state:
    st.session_state.successful_requests = 0

if 'total_queries' not in st.session_state:
    st.session_state.total_queries = 0

if 'database_context' not in st.session_state:
    st.session_state.database_context = None

# Sidebar
with st.sidebar:
    st.title("⚙️ การตั้งค่า")
    
    # Webhook Configuration
    st.markdown("### 🔗 N8N Webhook URL")
    webhook_input = st.text_input(
        "Webhook URL",
        value=st.session_state.webhook_url,
        placeholder="https://your-n8n.app.n8n.cloud/webhook/...",
        label_visibility="collapsed"
    )
    
    if webhook_input != st.session_state.webhook_url:
        st.session_state.webhook_url = webhook_input
        st.success("✅ อัพเดท Webhook URL สำเร็จ!")
    
    st.markdown("---")
    
    # Database Context
    st.markdown("### 🗄️ Database Context")
    
    with st.expander("ตั้งค่า Database Info"):
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
