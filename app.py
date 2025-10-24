# Page config - MUST be first Streamlit command
import streamlit as st
st.set_page_config(
    page_title="Hospital Management Dashboard",
    page_icon="●",
    layout="wide",
    initial_sidebar_state="expanded"
)

import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import os
from dotenv import load_dotenv
import openai
import asyncio
import threading
import time

# Import speech libraries with fallback for deployment environments
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

# Detect deployment environment
import platform
import sys

# Enable voice features in local development environment
IS_LOCAL_ENV = (
    platform.system() == "Darwin" or  # macOS
    "localhost" in str(sys.argv) or
    "streamlit" in str(sys.argv) and "run" in str(sys.argv)
)

# Enable voice features for all environments (using Web Speech API for cloud)
SHOW_VOICE_FEATURES = True
import json

# Import RAG system
try:
    from rag_system import RAGSystem
    rag_system = RAGSystem()
    RAG_AVAILABLE = rag_system.is_available()
    print(f"RAG System - Database path: {rag_system.db_path}")
    print(f"RAG System - Available: {RAG_AVAILABLE}")
    if not RAG_AVAILABLE:
        print("RAG system loaded but database not available")
except ImportError as e:
    RAG_AVAILABLE = False
    rag_system = None
    print(f"RAG system not available - import failed: {e}")
except Exception as e:
    RAG_AVAILABLE = False
    rag_system = None
    print(f"RAG system error: {e}")

# Load environment variables
load_dotenv()

# Handle OpenAI API Key configuration
def setup_openai_api():
    """设置OpenAI API密钥"""
    # 检查多个来源的API密钥
    api_key = None

    # 1. 检查Streamlit session state
    if 'openai_api_key' in st.session_state and st.session_state.openai_api_key:
        api_key = st.session_state.openai_api_key

    # 2. 检查Streamlit secrets (安全处理)
    elif api_key is None:
        try:
            if hasattr(st, 'secrets') and "OPENAI_API_KEY" in st.secrets:
                api_key = st.secrets["OPENAI_API_KEY"]
        except FileNotFoundError:
            # secrets文件不存在，跳过
            pass
        except Exception:
            # 其他secrets相关错误，跳过
            pass

    # 3. 检查环境变量
    if api_key is None:
        api_key = os.getenv('OPENAI_API_KEY')

    if api_key:
        os.environ['OPENAI_API_KEY'] = api_key
        return True
    return False

# 设置API密钥
setup_openai_api()

# Nordic color palette - Ultra minimal
COLORS = {
    'primary': '#334155',      # Slate gray
    'secondary': '#64748B',    # Medium slate
    'accent': '#94A3B8',       # Light slate
    'light': '#F8FAFC',        # Almost white
    'white': '#FFFFFF',        # Pure white
    'success': '#10B981',      # Clean green
    'warning': '#F59E0B',      # Clean amber
    'danger': '#EF4444',       # Clean red
    'text': '#0F172A',         # Deep slate
    'text_light': '#64748B'    # Medium slate
}

# Custom CSS for Nordic design
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@200;300;400;500;600&display=swap');
    
    /* Global styles with Nordic aesthetics */
    .main {
        background: linear-gradient(180deg, #FDFEFF 0%, #F8FAFC 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #1A202C;
    }
    
    .stApp {
        background: linear-gradient(180deg, #FDFEFF 0%, #F8FAFC 100%);
    }
    
    /* Typography - Nordic minimalism */
    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        font-family: 'Inter', sans-serif !important;
        font-weight: 300 !important;
        letter-spacing: -0.025em !important;
        color: #1A202C !important;
        line-height: 1.2 !important;
    }
    
    /* Header styling - Clean and minimal */
    .main-header {
        background: linear-gradient(135deg, #334155 0%, #475569 100%);
        padding: 3rem 2rem;
        margin: -1rem -1rem 3rem -1rem;
        border-radius: 0 0 2rem 2rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05);
    }
    
    .main-title {
        font-size: 3rem;
        font-weight: 200;
        margin-bottom: 0.5rem;
        letter-spacing: -0.04em;
    }
    
    .main-subtitle {
        font-size: 1.2rem;
        opacity: 0.85;
        font-weight: 300;
        letter-spacing: 0.01em;
    }
    
    /* Cards - Ultra clean design */
    .kpi-card {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        padding: 2rem;
        border-radius: 1rem;
        border: 1px solid rgba(226, 232, 240, 0.3);
        margin-bottom: 1.5rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }
    
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.06);
        border-color: rgba(148, 163, 184, 0.2);
    }
    
    .kpi-value {
        font-size: 2.25rem;
        font-weight: 200;
        color: #334155;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }
    
    .kpi-label {
        font-size: 0.875rem;
        color: #64748B;
        font-weight: 400;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    
    /* Section headers - Minimal elegance */
    .section-header {
        font-size: 1.5rem;
        font-weight: 300;
        color: #1E293B;
        margin: 3rem 0 1.5rem 0;
        position: relative;
        padding-bottom: 0.75rem;
    }
    
    .section-header::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        width: 3rem;
        height: 2px;
        background: linear-gradient(90deg, #334155, transparent);
    }
    
    /* Sidebar - Clean and minimal */
    .css-1d391kg, .css-12oz5g7 {
        background: rgba(248, 250, 252, 0.8) !important;
        backdrop-filter: blur(10px) !important;
    }
    
    /* Filter panels - Glass morphism */
    .filter-panel {
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(15px);
        padding: 1.5rem;
        border-radius: 1rem;
        border: 1px solid rgba(226, 232, 240, 0.3);
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
    }
    
    .filter-title {
        font-size: 1rem;
        font-weight: 500;
        color: #1E293B;
        margin-bottom: 1rem;
        letter-spacing: 0.025em;
    }
    
    /* Input styling - Modern and clean */
    .stDateInput > div > div > input,
    .stMultiSelect > div > div > div,
    .stSelectbox > div > div > div,
    .stTextInput > div > div > input {
        border-radius: 0.75rem !important;
        border: 1px solid rgba(203, 213, 225, 0.4) !important;
        background: rgba(255, 255, 255, 0.9) !important;
        font-size: 0.9rem !important;
        transition: all 0.2s ease !important;
    }
    
    .stDateInput > div > div > input:focus,
    .stMultiSelect > div > div > div:focus,
    .stSelectbox > div > div > div:focus,
    .stTextInput > div > div > input:focus {
        border-color: #334155 !important;
        box-shadow: 0 0 0 3px rgba(51, 65, 85, 0.1) !important;
    }
    
    /* Labels - Minimal typography */
    .stDateInput > label,
    .stMultiSelect > label,
    .stSelectbox > label,
    .stTextInput > label {
        font-size: 0.8rem !important;
        font-weight: 500 !important;
        color: #475569 !important;
        margin-bottom: 0.5rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }
    
    /* Tags - Nordic blue accents */
    .stMultiSelect [data-baseweb="tag"] {
        background-color: #334155 !important;
        border-color: #334155 !important;
        border-radius: 0.5rem !important;
    }
    
    .stMultiSelect [data-baseweb="tag"] span {
        color: white !important;
        font-weight: 400 !important;
    }
    
    /* Buttons - Minimal design */
    .stButton > button {
        background: linear-gradient(135deg, #334155 0%, #475569 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 0.75rem !important;
        padding: 0.5rem 1.5rem !important;
        font-weight: 400 !important;
        transition: all 0.2s ease !important;
        letter-spacing: 0.025em !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(51, 65, 85, 0.3) !important;
    }
    
    /* Expander - Clean design */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.8) !important;
        border-radius: 0.75rem !important;
        border: 1px solid rgba(226, 232, 240, 0.3) !important;
        font-weight: 400 !important;
        color: #1E293B !important;
    }
    
    .streamlit-expanderContent {
        background: rgba(255, 255, 255, 0.6) !important;
        border: 1px solid rgba(226, 232, 240, 0.2) !important;
        border-top: none !important;
        border-radius: 0 0 0.75rem 0.75rem !important;
    }
    .stMultiSelect [data-baseweb="tag"] [data-testid="stSelectboxClearIcon"] {
        color: rgba(255, 255, 255, 0.7) !important;
    }
    
    .stMultiSelect [data-baseweb="tag"] [data-testid="stSelectboxClearIcon"]:hover {
        color: white !important;
        background-color: rgba(255, 255, 255, 0.1) !important;
        border-radius: 50% !important;
    }
    
    /* Remove default margins */
    .block-container {
        padding-top: 1rem;
    }
    
    /* Metric containers */
    [data-testid="metric-container"] {
        background-color: white;
        border: 1px solid #E2E8F0;
        padding: 1rem;
        border-radius: 0.75rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    [data-testid="metric-container"]:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        transform: translateY(-1px);
        transition: all 0.2s ease;
    }
    
    /* Chat button styling */
    .chat-button {
        position: fixed !important;
        bottom: 2rem !important;
        right: 2rem !important;
        width: 60px;
        height: 60px;
        background: linear-gradient(135deg, #2E5266 0%, #6C7B7F 100%);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 16px rgba(46, 82, 102, 0.3);
        cursor: pointer;
        z-index: 9999 !important;
        transition: all 0.3s ease;
        border: none;
    }
    
    .chat-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(46, 82, 102, 0.4);
    }
    
    .chat-button span {
        color: white;
        font-size: 1.2rem;
        font-weight: 500;
    }
    
    /* Chat modal styling */
    .chat-modal {
        position: fixed !important;
        bottom: 6rem !important;
        right: 2rem !important;
        width: 350px;
        height: 500px;
        background: white;
        border-radius: 1rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
        z-index: 10000 !important;
        display: none;
        flex-direction: column;
        overflow: hidden;
        border: 1px solid #E2E8F0;
    }
    
    .chat-modal.active {
        display: flex;
    }
    
    .chat-header {
        background: linear-gradient(135deg, #2E5266 0%, #6C7B7F 100%);
        color: white;
        padding: 1rem;
        font-weight: 500;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .chat-close {
        background: none;
        border: none;
        color: white;
        font-size: 1.2rem;
        cursor: pointer;
        padding: 0;
        width: 24px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .chat-messages {
        flex: 1;
        padding: 1rem;
        overflow-y: auto;
        background: #FAFBFC;
    }
    
    .chat-input-area {
        padding: 1rem;
        border-top: 1px solid #E2E8F0;
        background: white;
    }
    
    .message {
        margin-bottom: 1rem;
        padding: 0.75rem;
        border-radius: 0.75rem;
        max-width: 85%;
        word-wrap: break-word;
    }
    
    .message.user {
        background: #2E5266;
        color: white;
        margin-left: auto;
    }
    
    .message.assistant {
        background: #F1F5F9;
        color: #2D3748;
        margin-right: auto;
    }
    
    .chat-input {
        width: 100%;
        padding: 0.75rem;
        border: 1px solid #E2E8F0;
        border-radius: 0.5rem;
        font-size: 0.9rem;
        resize: none;
        font-family: Inter, sans-serif;
    }
    
    .chat-input:focus {
        outline: none;
        border-color: #2E5266;
        box-shadow: 0 0 0 2px rgba(46, 82, 102, 0.1);
    }
    
    .send-button {
        background: #2E5266;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 0.4rem;
        font-size: 0.9rem;
        cursor: pointer;
        margin-top: 0.5rem;
        width: 100%;
        font-family: Inter, sans-serif;
    }
    
    .send-button:hover {
        background: #1a3b4a;
    }
    
    .send-button:disabled {
        background: #9CA3AF;
        cursor: not-allowed;
    }
    
    /* Simplified layout - keep default Streamlit layout */
    
    /* Keep responsive design simple */
    @media (max-width: 768px) {
        .main-title {
            font-size: 1.8rem;
        }
        .main-subtitle {
            font-size: 0.9rem;
        }
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Load and preprocess data"""
    df = pd.read_csv("data/LengthOfStay.csv")
    
    # Convert dates
    df['vdate'] = pd.to_datetime(df['vdate'])
    df['discharged'] = pd.to_datetime(df['discharged'])
    df['Date_of_Birth'] = pd.to_datetime(df['Date_of_Birth'])
    
    # Create derived features
    df['month'] = df['vdate'].dt.to_period('M').astype(str)
    df['is_long_stay'] = (df['lengthofstay'] > df['lengthofstay'].quantile(0.75)).astype(int)
    df['readmit_flag'] = (df['rcount'] != '0').astype(int)
    
    # Calculate age at admission
    df['age_at_admission'] = (df['vdate'] - df['Date_of_Birth']).dt.days / 365.25
    df['age_group'] = pd.cut(df['age_at_admission'], 
                            bins=[0, 18, 35, 50, 65, 80, 100], 
                            labels=['0-18', '19-35', '36-50', '51-65', '66-80', '80+'])
    
    # Create full name for patient identification
    df['full_name'] = df['First_Name'] + ' ' + df['Last_Name']
    
    # Create risk level categorization
    df['risk_level'] = 'Standard Risk'
    high_risk_mask = (
        (df['lengthofstay'] > df['lengthofstay'].quantile(0.9)) |
        (df['readmit_flag'] == 1)
    )
    df.loc[high_risk_mask, 'risk_level'] = 'High Risk'
    
    # Disease columns for analysis
    disease_cols = ['dialysisrenalendstage', 'asthma', 'irondef', 'pneum', 
                   'substancedependence', 'psychologicaldisordermajor', 
                   'depress', 'psychother', 'fibrosisandother', 'malnutrition']
    
    return df, disease_cols

# Patient Notes Management Functions
NOTES_FILE = "data/patient_notes.json"

def load_patient_notes():
    """Load all patient notes from JSON file"""
    if os.path.exists(NOTES_FILE):
        try:
            with open(NOTES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading notes: {e}")
            return {}
    return {}

def save_patient_notes(notes_dict):
    """Save all patient notes to JSON file"""
    try:
        os.makedirs(os.path.dirname(NOTES_FILE), exist_ok=True)
        with open(NOTES_FILE, 'w', encoding='utf-8') as f:
            json.dump(notes_dict, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving notes: {e}")
        return False

def get_patient_notes(patient_id):
    """Get notes for a specific patient"""
    notes = load_patient_notes()
    return notes.get(str(patient_id), "")

def update_patient_notes(patient_id, note_text):
    """Update notes for a specific patient"""
    notes = load_patient_notes()
    notes[str(patient_id)] = note_text
    return save_patient_notes(notes)

def create_chart_template():
    """Create a consistent chart template with Nordic styling"""
    template = {
        'layout': {
            'font': {'family': 'Inter, sans-serif', 'size': 11, 'color': COLORS['text']},
            'paper_bgcolor': 'rgba(255,255,255,0.9)',
            'plot_bgcolor': 'rgba(248,250,252,0.5)',
            'margin': {'l': 60, 'r': 60, 't': 80, 'b': 60},
            'xaxis': {
                'gridcolor': 'rgba(226,232,240,0.3)',
                'linecolor': 'rgba(148,163,184,0.2)',
                'tickcolor': 'rgba(148,163,184,0.2)',
                'tickfont': {'color': COLORS['text_light'], 'size': 10}
            },
            'yaxis': {
                'gridcolor': 'rgba(226,232,240,0.3)',
                'linecolor': 'rgba(148,163,184,0.2)',
                'tickcolor': '#E2E8F0',
                'tickfont': {'color': COLORS['text_light']}
            },
            'title': {
                'font': {'size': 16, 'color': COLORS['text']},
                'x': 0.02,
                'xanchor': 'left'
            }
        }
    }
    return template

def generate_patient_response(patient, user_question):
    """Generate AI response using RAG system or fallback to basic OpenAI API"""

    try:
        # Get API key from session state or environment
        api_key = None
        if 'openai_api_key' in st.session_state and st.session_state.openai_api_key:
            api_key = st.session_state.openai_api_key
        else:
            api_key = os.getenv('OPENAI_API_KEY')

        if not api_key:
            return "Please enter your OpenAI API key in the sidebar to enable AI responses."

        # Try RAG system first if available
        if RAG_AVAILABLE and rag_system:
            # Update RAG system with current API key
            rag_system.update_api_key(api_key)
            rag_response, relevant_papers, diagnostic_info = rag_system.get_rag_response_for_patient(patient, user_question)
            if rag_response:
                # Check if response is an error message
                if rag_response.startswith("❌"):
                    return rag_response
                else:
                    return rag_response

        # Fallback to basic OpenAI response
        client = openai.OpenAI(api_key=api_key)
        
        # Extract comprehensive patient information
        patient_data = {
            'name': patient['full_name'],
            'id': patient['eid'],
            'age_group': patient['age_group'],
            'gender': patient['gender'],
            'department': patient['facid'],
            'length_of_stay': patient['lengthofstay'],
            'risk_level': patient['risk_level'],
            'glucose': patient['glucose'],
            'creatinine': patient['creatinine'],
            'hematocrit': patient['hematocrit'],
            'pulse': patient['pulse'],
            'respiration': patient['respiration'],
            'bmi': patient['bmi'],
            'sodium': patient['sodium'],
            'neutrophils': patient['neutrophils'],
            'blood_urea_nitrogen': patient['bloodureanitro']
        }

        # Get patient notes
        patient_notes = get_patient_notes(patient_data['id'])
        notes_section = f"\n\nAdditional Clinical Notes:\n{patient_notes}" if patient_notes else ""

        # Get uploaded file info
        file_key = f"uploaded_file_{patient_data['id']}"
        file_section = ""
        if file_key in st.session_state:
            file_info = st.session_state[file_key]
            file_section = f"\n\nUploaded File:\n- Filename: {file_info['name']}\n- Type: {file_info['type']}"
            if 'summary' in file_info and file_info['summary']:
                file_section += f"\n- AI Analysis: {file_info['summary']}"
            if 'content_preview' in file_info and file_info['content_preview']:
                file_section += f"\n- Content Preview: {file_info['content_preview']}"

        # Create detailed system prompt with enhanced medical context
        system_prompt = f"""You are a senior medical AI assistant with expertise in clinical medicine, diagnostics, and patient care. Provide comprehensive, evidence-based medical responses.

Patient Profile:
- Name: {patient_data['name']}
- ID: {patient_data['id']}
- Age Group: {patient_data['age_group']}
- Gender: {patient_data['gender']}
- Department: {patient_data['department']}
- Length of Stay: {patient_data['length_of_stay']} days
- Risk Level: {patient_data['risk_level']}

Laboratory Results & Vitals:
- Glucose: {patient_data['glucose']:.1f} mg/dL (normal: 70-140)
- Creatinine: {patient_data['creatinine']:.3f} mg/dL (normal: 0.6-1.2)
- Hematocrit: {patient_data['hematocrit']:.1f} g/dL (normal: 12-16)
- Pulse: {patient_data['pulse']} bpm (normal: 60-100)
- Respiration: {patient_data['respiration']} /min (normal: 12-20)
- BMI: {patient_data['bmi']:.1f}
- Sodium: {patient_data['sodium']:.1f} mEq/L (normal: 136-145)
- Neutrophils: {patient_data['neutrophils']:.1f}% (normal: 50-70)
- Blood Urea Nitrogen: {patient_data['blood_urea_nitrogen']:.1f} mg/dL (normal: 7-20){notes_section}{file_section}

Clinical Guidelines:
1. Provide detailed, professional medical analysis
2. Interpret lab values in clinical context
3. Suggest differential diagnoses when relevant
4. Recommend appropriate diagnostic workup or monitoring
5. Explain medical reasoning clearly
6. Address patient-specific risk factors
7. Consider department-specific protocols and standards
8. Pay special attention to any additional clinical notes and uploaded files provided"""

        # Make API call to OpenAI with enhanced parameters
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_question}
            ],
            max_tokens=600,  # Increased for detailed medical responses
            temperature=0.6,  # Slightly lower for more consistent medical advice
            presence_penalty=0.1  # Encourage varied terminology
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        # Check for specific API key errors
        error_str = str(e)
        if "401" in error_str or "invalid_request_error" in error_str or "Incorrect API key" in error_str:
            return "❌ **API密钥无效** - 请在侧边栏检查并重新输入正确的OpenAI API密钥"
        elif "403" in error_str or "insufficient_quota" in error_str:
            return "❌ **API配额不足** - 您的OpenAI账户余额不足或已达到使用限制"
        elif "429" in error_str or "rate_limit" in error_str:
            return "❌ **请求过于频繁** - 请稍等片刻后重试"
        else:
            # General error fallback
            st.error(f"API Error: {str(e)}")

            # Simplified fallback response
            name = patient['full_name']
        glucose = patient['glucose']
        creatinine = patient['creatinine']
        risk_level = patient['risk_level']
        
        if 'risk' in user_question.lower():
            return f"Patient has {risk_level} classification with {patient['rcount']} risk factors. Length of stay: {patient['lengthofstay']} days."
        elif 'glucose' in user_question.lower() or 'blood sugar' in user_question.lower():
            if glucose > 140:
                return f"Glucose level is elevated at {glucose:.1f} mg/dL (normal: 70-140). Consider glucose management."
            else:
                return f"Glucose level is {glucose:.1f} mg/dL - within normal range."
        elif 'kidney' in user_question.lower() or 'creatinine' in user_question.lower():
            if creatinine > 1.2:
                return f"Creatinine is elevated at {creatinine:.3f} mg/dL (normal: 0.6-1.2). Monitor kidney function."
            else:
                return f"Creatinine is {creatinine:.3f} mg/dL - within normal range."
        elif 'discharge' in user_question.lower():
            days = patient['lengthofstay']
            if days > 7:
                return f"Extended stay ({days} days). Review case for discharge readiness and potential barriers."
            else:
                return "Monitor for 24-48 hours. If stable, consider discharge planning."
        else:
            return f"I can help you analyze {name}'s case. Ask about risk factors, lab values, or treatment plans."

# Voice functionality
def init_speech_components():
    """Initialize speech recognition and text-to-speech components"""
    if not SPEECH_RECOGNITION_AVAILABLE:
        return None, None

    try:
        recognizer = sr.Recognizer()
    except Exception:
        return None, None

    tts_engine = None
    if TTS_AVAILABLE:
        try:
            # Try to initialize TTS engine
            tts_engine = pyttsx3.init()
            # Configure TTS settings
            tts_engine.setProperty('rate', 150)  # Speed of speech
            tts_engine.setProperty('volume', 0.8)  # Volume level
        except Exception:
            tts_engine = None

    return recognizer, tts_engine

def listen_once():
    """Listen for voice input and return transcribed text"""
    if not SPEECH_RECOGNITION_AVAILABLE:
        return None, "Speech recognition not available in this environment"

    recognizer, _ = init_speech_components()
    if recognizer is None:
        return None, "Could not initialize speech recognition"

    try:
        with sr.Microphone() as source:
            # Adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source, duration=0.5)

            # Listen for audio with timeout
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=8)

            # Recognize speech using Google's service
            text = recognizer.recognize_google(audio)
            return text, None

    except sr.WaitTimeoutError:
        return None, "Listening timeout. Please try again."
    except sr.UnknownValueError:
        return None, "Could not understand the audio. Please speak clearly."
    except sr.RequestError as e:
        return None, f"Speech recognition service error: {e}"
    except Exception as e:
        return None, f"Microphone error: {e}"

def speak_text(text):
    """Convert text to speech"""
    if not TTS_AVAILABLE:
        return False

    try:
        _, tts_engine = init_speech_components()

        if tts_engine is None:
            # Fallback to macOS system 'say' command (only works locally)
            try:
                import subprocess
                import platform
                if platform.system() == "Darwin":  # macOS
                    def _speak_system():
                        subprocess.run(['say', text], check=True, capture_output=True)

                    speech_thread = threading.Thread(target=_speak_system, daemon=True)
                    speech_thread.start()
                    return True
                else:
                    return False
            except Exception:
                return False

        # Run TTS in a separate thread to prevent blocking
        def _speak():
            tts_engine.say(text)
            tts_engine.runAndWait()

        speech_thread = threading.Thread(target=_speak, daemon=True)
        speech_thread.start()
        return True
    except Exception:
        return False

# Web Speech API functions for cloud deployment
def create_web_speech_html(unique_id):
    """Create HTML component for Web Speech API"""
    html_code = f"""
    <div id="voice-container-{unique_id}" style="margin: 10px 0;">
        <button id="startRecording-{unique_id}"
                style="background: #ff4b4b; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; margin-right: 10px;">
            🎤 Start Recording
        </button>
        <button id="stopRecording-{unique_id}"
                style="background: #gray; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; margin-right: 10px;"
                disabled>
            ⏹️ Stop Recording
        </button>
        <span id="status-{unique_id}" style="font-size: 14px; color: #666;">Ready to record</span>
        <div id="result-{unique_id}" style="margin-top: 10px; padding: 10px; background: #f0f2f6; border-radius: 4px; display: none;">
            <strong>Recognized Text:</strong> <span id="transcription-{unique_id}"></span>
        </div>
    </div>

    <script>
    (function() {{
        const startBtn = document.getElementById('startRecording-{unique_id}');
        const stopBtn = document.getElementById('stopRecording-{unique_id}');
        const status = document.getElementById('status-{unique_id}');
        const result = document.getElementById('result-{unique_id}');
        const transcription = document.getElementById('transcription-{unique_id}');

        let recognition = null;

        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {{
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();

            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'en-US';

            recognition.onstart = function() {{
                startBtn.disabled = true;
                stopBtn.disabled = false;
                status.textContent = '🎧 Listening... Please speak now!';
                status.style.color = '#ff4b4b';
            }};

            recognition.onresult = function(event) {{
                const text = event.results[0][0].transcript;
                transcription.textContent = text;
                result.style.display = 'block';
                status.textContent = '✅ Speech recognized! Transcript shown below.';
                status.style.color = '#00c851';

                // Send result back to Streamlit
                window.parent.postMessage({{
                    type: 'speechResult',
                    text: text,
                    uniqueId: '{unique_id}'
                }}, '*');
            }};

            recognition.onerror = function(event) {{
                status.textContent = '❌ Error: ' + event.error;
                status.style.color = '#ff4444';
                startBtn.disabled = false;
                stopBtn.disabled = true;
            }};

            recognition.onend = function() {{
                startBtn.disabled = false;
                stopBtn.disabled = true;
                if (status.textContent.includes('Listening')) {{
                    status.textContent = 'Ready to record';
                    status.style.color = '#666';
                }}
            }};
        }} else {{
            status.textContent = '❌ Speech recognition not supported in this browser';
            status.style.color = '#ff4444';
            startBtn.disabled = true;
        }}

        startBtn.onclick = function() {{
            if (recognition) {{
                result.style.display = 'none';
                recognition.start();
            }}
        }};

        stopBtn.onclick = function() {{
            if (recognition) {{
                recognition.stop();
            }}
        }};
    }})();
    </script>
    """
    return html_code

def speak_text_web(text, unique_id):
    """Use Web Speech API for text-to-speech in browser - simple and reliable"""
    if not text:
        return ""

    # Escape text properly for JavaScript
    safe_text = text.replace('"', '\\"').replace('\n', ' ').replace('\r', ' ')

    html_code = f"""
    <div id="tts-container-{unique_id}">
        <script>
        if ('speechSynthesis' in window) {{
            const utterance = new SpeechSynthesisUtterance("{safe_text}");
            utterance.rate = 0.9;
            utterance.volume = 0.8;
            speechSynthesis.speak(utterance);
        }}
        </script>
    </div>
    """
    return html_code

def show_patient_detail(patient_id, df):
    """Show detailed patient information with sidebar showing patient history"""
    patient = df[df['eid'] == patient_id].iloc[0]

    # Sidebar with patient history
    with st.sidebar:
        st.markdown("### Patient History")
        st.markdown(f"**Patient:** {patient['full_name']}")
        st.markdown("---")

        # Get all records for this patient (by name)
        patient_name = patient['full_name']
        patient_history = df[df['full_name'] == patient_name].sort_values('vdate')

        if len(patient_history) > 1:
            st.markdown(f"**Total Admissions:** {len(patient_history)}")
            st.markdown(f"**Total Length of Stay:** {patient_history['lengthofstay'].sum()} days")
            st.markdown("---")

            # Display each admission
            for idx, (_, record) in enumerate(patient_history.iterrows(), 1):
                is_current = record['eid'] == patient_id

                # Highlight current record
                if is_current:
                    st.markdown(f"**📍 Admission #{idx} (Current)**")
                else:
                    st.markdown(f"**Admission #{idx}**")

                st.markdown(f"• **Admission Date:** {record['vdate']}")
                st.markdown(f"• **Discharge Date:** {record['discharged']}")
                st.markdown(f"• **Length of Stay:** {record['lengthofstay']} days")
                st.markdown(f"• **Facility:** {record['facid']}")
                if pd.notna(record.get('admission_reason')):
                    st.markdown(f"• **Reason:** {record['admission_reason']}")

                # Show key medical indicators
                if pd.notna(record['glucose']):
                    st.markdown(f"• **Glucose:** {record['glucose']:.1f}")
                if pd.notna(record['creatinine']):
                    st.markdown(f"• **Creatinine:** {record['creatinine']:.2f}")

                # Add button to view this record (if not current)
                if not is_current:
                    if st.button(f"View Admission #{idx}", key=f"history_{record['eid']}"):
                        st.session_state.selected_patient = record['eid']
                        st.rerun()

                st.markdown("---")
        else:
            st.markdown("**First Admission**")
            st.info("This is the patient's first admission record")

    # Main content area
    # Back button
    if st.button("← Back to Dashboard"):
        st.session_state.current_page = "dashboard"
        st.session_state.selected_patient = None
        st.rerun()
    
    # Patient header
    st.markdown(f"""
    <div class="main-header">
        <div class="main-title">Patient Details: {patient['full_name']}</div>
        <div class="main-subtitle">Comprehensive Medical Record</div>
    </div>
    """, unsafe_allow_html=True)

    # Auto-generated AI Summary
    st.markdown("### 🤖 AI Patient Summary")
    summary_container = st.container()

    with summary_container:
        # Generate automatic summary using GPT
        if 'openai_api_key' in st.session_state and st.session_state.openai_api_key:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=st.session_state.openai_api_key)

                # Build patient context
                patient_context = f"""Patient: {patient['full_name']}
Age: {patient['age_at_admission']} years ({patient['age_group']})
Gender: {'Male' if patient['gender'] == 'M' else 'Female'}
Department: {patient['facid']}
Length of Stay: {patient['lengthofstay']} days
Admission Date: {patient['vdate']}
Discharge Date: {patient['discharged']}

Lab Results:
- Glucose: {patient['glucose']:.1f} mg/dL (normal: 70-100)
- Creatinine: {patient['creatinine']:.2f} mg/dL (normal: 0.6-1.2)
- Hematocrit: {patient['hematocrit']:.1f}% (normal: 38-46% female, 42-54% male)
- Sodium: {patient['sodium']:.1f} mEq/L (normal: 135-145)
- Blood Urea Nitrogen: {patient['bloodureanitro']:.1f} mg/dL (normal: 7-20)

Risk Level: {patient['risk_level']}
Readmission Flag: {'Yes' if patient['readmit_flag'] == 1 else 'No'}"""

                # Get patient notes if available
                patient_notes = get_patient_notes(patient['eid'])
                if patient_notes:
                    patient_context += f"\n\nAdditional Notes:\n{patient_notes}"

                with st.spinner("Generating summary..."):
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {
                                "role": "system",
                                "content": "You are an experienced hospital administrator. Provide a concise executive summary of the patient's current status. Focus on: 1) Key abnormal findings that need attention, 2) Clinical significance, 3) Immediate recommendations. Be brief and actionable. Skip normal values unless specifically relevant."
                            },
                            {
                                "role": "user",
                                "content": f"Provide an executive summary for this patient:\n\n{patient_context}"
                            }
                        ],
                        max_tokens=200,
                        temperature=0.7
                    )

                    summary = response.choices[0].message.content.strip()

                    # Display summary in a nice box
                    st.markdown(f"""
                    <div style="background-color: #f0f7ff; padding: 15px; border-radius: 8px; border-left: 4px solid #2E5266; margin-bottom: 20px;">
                        {summary}
                    </div>
                    """, unsafe_allow_html=True)

            except Exception as e:
                st.info("💡 Auto-summary unavailable. Configure OpenAI API key in Settings.")
        else:
            st.info("💡 Configure OpenAI API key in Settings to enable automatic patient summaries.")

    st.markdown("---")

    # AI-Based Clinical Summary Section - Only show if patient has identifiable conditions
    if RAG_AVAILABLE:
        # Check if patient has detectable symptoms/conditions
        detected_symptoms, diagnostic_info = rag_system.extract_symptoms_from_patient(patient)
        
        # Only show if we detect specific medical conditions (not just generic terms)
        specific_conditions = [s for s in detected_symptoms if s not in ['length of stay', 'hospital admission', 'medical care']]
        
        if specific_conditions:
            with st.expander("Clinical Summary & Evidence-Based Insights", expanded=True):
                # Get RAG analysis for this patient
                try:
                    rag_response, relevant_papers, diagnostic_details = rag_system.get_rag_response_for_patient(patient)
                    
                    if rag_response and relevant_papers:
                        # Display detected conditions with diagnostic reasoning
                        condition_list = ", ".join(specific_conditions).title()
                        st.markdown(f"**Detected Conditions:** {condition_list}")
                        
                        # Display diagnostic basis
                        if diagnostic_details:
                            st.markdown("**Diagnostic Basis:**")
                            for detail in diagnostic_details:
                                st.markdown(f"• {detail}")
                        
                        # Display clinical insights
                        st.markdown("**Clinical Analysis:**")
                        # Remove the reference section from RAG response for cleaner display
                        clean_response = rag_response.split("References:")[0].strip()
                        st.markdown(clean_response)
                        
                        # Display relevant papers separately (remove duplicates)
                        if relevant_papers:
                            st.markdown("**Supporting Evidence:**")
                            unique_filenames = []
                            for paper in relevant_papers[:3]:
                                filename = paper.get('filename', '')
                                if filename not in unique_filenames:
                                    unique_filenames.append(filename)

                                    # Get paper metadata from database
                                    title = paper.get('title', filename.replace('.pdf', '').replace('.txt', ''))
                                    author = paper.get('authors', 'Unknown')
                                    year = paper.get('year', 'Unknown')

                                    # Format citation: Filename (Author, Year)
                                    # Clean filename for display - 不截断文件名
                                    display_filename = filename.replace('.pdf', '').replace('.txt', '')

                                    # 构建完整引用：文件名 (作者, 年份)
                                    citation_parts = []

                                    # 处理作者信息 - 更宽松的条件
                                    if author and author != 'Unknown' and author.strip() and author != 'affiliations':
                                        citation_parts.append(author.strip())

                                    # 处理年份信息 - 更宽松的条件
                                    if year and year is not None and str(year) != 'Unknown' and str(year) != 'nan' and str(year) != 'None':
                                        citation_parts.append(str(year))

                                    # 格式：文件名 (作者, 年份) 或 文件名 (年份) 或 文件名
                                    if citation_parts:
                                        citation = f"{display_filename} ({', '.join(citation_parts)})"
                                    else:
                                        citation = display_filename

                                    # 使用自动换行的HTML，超出宽度自动下一行
                                    st.markdown(f"""
                                    <div style="
                                        margin-bottom: 8px;
                                        word-wrap: break-word;
                                        word-break: break-word;
                                        white-space: normal;
                                        overflow-wrap: anywhere;
                                        line-height: 1.4;
                                    ">
                                        • {citation}
                                    </div>
                                    """, unsafe_allow_html=True)
                    else:
                        st.info("Ask questions in the chat to get evidence-based insights for this patient.")
                        
                except Exception as e:
                    st.warning("Clinical insights temporarily unavailable.")
    
    # Health Status Overview (Full width, 4 metrics)
    st.markdown("### Health Status Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Age Group", patient['age_group'])
        
    with col2:
        st.metric("Department", patient['facid'])
        
    with col3:
        st.metric("Length of Stay", f"{patient['lengthofstay']} days")
        
    with col4:
        # Determine overall risk status
        st.metric("Risk Status", "")
        if patient['risk_level'] == 'High Risk':
            st.markdown("<span style='color: #D47A84;'>● High Risk</span>", unsafe_allow_html=True)
        else:
            st.markdown("○ Standard Risk")
    
    st.markdown("---")
    
    # Single column layout for detailed information
    # Risk Assessment
    st.markdown("### Risk Assessment")
    risk_factors = []
    
    # Analyze key risk factors
    if patient['lengthofstay'] > df['lengthofstay'].quantile(0.75):
        risk_factors.append("Extended length of stay")
    if patient['readmit_flag'] == 1:
        risk_factors.append("Previous readmission")
    if patient['age_at_admission'] > 65:
        risk_factors.append("Advanced age")
    if patient['creatinine'] > 1.2:
        risk_factors.append("Elevated creatinine")
    if patient['glucose'] > 140:
        risk_factors.append("Elevated glucose")
    if patient['hematocrit'] < 12 or patient['hematocrit'] > 16:
        hematocrit_status = "High hematocrit" if patient['hematocrit'] > 16 else "Low hematocrit"
        risk_factors.append(f"<span style='color: #D47A84;'>{hematocrit_status}</span>")
    
    if risk_factors:
        for factor in risk_factors:
            st.markdown(f"● {factor}", unsafe_allow_html=True)
    else:
        st.write("○ No significant risk factors identified")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Medical Conditions
    st.markdown("### Medical Conditions")
    conditions = []
    condition_names = {
        'dialysisrenalendstage': 'End-stage renal disease',
        'asthma': 'Asthma',
        'irondef': 'Iron deficiency',
        'pneum': 'Pneumonia',
        'substancedependence': 'Substance dependence',
        'psychologicaldisordermajor': 'Major psychological disorder',
        'depress': 'Depression',
        'psychother': 'Requiring psychotherapy',
        'fibrosisandother': 'Fibrosis and related conditions',
        'malnutrition': 'Malnutrition'
    }
    
    medical_cols = ['dialysisrenalendstage', 'asthma', 'irondef', 'pneum', 'substancedependence', 
                   'psychologicaldisordermajor', 'depress', 'psychother', 'fibrosisandother', 'malnutrition']
    
    for col in medical_cols:
        if patient[col] == 1:
            conditions.append(condition_names.get(col, col.replace('_', ' ').title()))
    
    if conditions:
        for condition in conditions:
            st.write(f"● {condition}")
    else:
        st.write("○ No recorded medical conditions")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Vital Signs & BMI Assessment
    st.markdown("### Vital Signs & Assessment")

    # Define vital signs and BMI data
    vital_values = [
        {
            'name': 'Pulse',
            'value': patient['pulse'],
            'unit': 'bpm',
            'normal_range': (60, 100),
            'format': '.0f'
        },
        {
            'name': 'Respiration',
            'value': patient['respiration'],
            'unit': '/min',
            'normal_range': (12, 20),
            'format': '.1f'
        },
        {
            'name': 'BMI',
            'value': patient['bmi'],
            'unit': '',
            'normal_range': (18.5, 25),
            'format': '.1f',
            'custom_status': True  # BMI has special categorization
        }
    ]

    # Create 2-column layout for vital signs
    col1, col2 = st.columns(2)

    for i, vital in enumerate(vital_values):
        # Special handling for BMI categories
        if vital.get('custom_status'):
            bmi_val = vital['value']
            if bmi_val < 18.5:
                status_text = "Underweight"
                is_normal = False
            elif 18.5 <= bmi_val < 25:
                status_text = "Normal"
                is_normal = True
            elif 25 <= bmi_val < 30:
                status_text = "Overweight"
                is_normal = False
            else:
                status_text = "Obese"
                is_normal = False
            range_text = "18.5-24.9"
        else:
            # Standard range checking
            is_normal = vital['normal_range'][0] <= vital['value'] <= vital['normal_range'][1]
            if is_normal:
                status_text = "Normal"
            else:
                status_text = "High" if vital['value'] > vital['normal_range'][1] else "Low"
            range_text = f"{vital['normal_range'][0]}-{vital['normal_range'][1]}"

        status_icon = "○" if is_normal else "●"
        status_color = "#10B981" if is_normal else "#EF4444"  # Green for normal, red for abnormal

        # Format value
        formatted_value = f"{vital['value']:{vital['format']}}"

        # Determine column (BMI goes to first available spot)
        if i == 2:  # BMI - put in first column if both vital signs are done
            target_col = col1
        else:
            target_col = col1 if i % 2 == 0 else col2

        with target_col:
            # Custom styled metric card
            st.markdown(f"""
            <div style='background: #F8FAFC; padding: 16px; border-radius: 8px; border-left: 4px solid {status_color}; margin-bottom: 8px;'>
                <div style='font-weight: 600; color: #1F2937; margin-bottom: 4px;'>{vital['name']}</div>
                <div style='font-size: 24px; font-weight: 700; color: #1F2937; margin-bottom: 4px;'>
                    {formatted_value} <span style='font-size: 14px; font-weight: 400; color: #6B7280;'>{vital['unit']}</span>
                </div>
                <div style='font-size: 12px; color: {status_color}; display: flex; align-items: center;'>
                    <span style='margin-right: 4px;'>{status_icon}</span> {status_text}
                    <span style='color: #9CA3AF; margin-left: 8px;'>({range_text}{' ' + vital['unit'] if vital['unit'] and not vital.get('custom_status') else ''})</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Laboratory Results with interpretations
    st.markdown("### Laboratory Results")

    # Define lab values with normal ranges and interpretations
    lab_values = [
        {
            'name': 'Hematocrit',
            'value': patient['hematocrit'],
            'unit': 'g/dL',
            'normal_range': (12, 16),
            'format': '.1f'
        },
        {
            'name': 'Creatinine',
            'value': patient['creatinine'],
            'unit': 'mg/dL',
            'normal_range': (0.6, 1.2),
            'format': '.3f'
        },
        {
            'name': 'Glucose',
            'value': patient['glucose'],
            'unit': 'mg/dL',
            'normal_range': (70, 140),
            'format': '.1f'
        },
        {
            'name': 'Neutrophils',
            'value': patient['neutrophils'],
            'unit': '%',
            'normal_range': (40, 70),
            'format': '.1f'
        },
        {
            'name': 'Sodium',
            'value': patient['sodium'],
            'unit': 'mEq/L',
            'normal_range': (135, 145),
            'format': '.1f'
        },
        {
            'name': 'Blood Urea Nitrogen',
            'value': patient['bloodureanitro'],
            'unit': 'mg/dL',
            'normal_range': (7, 20),
            'format': '.1f'
        }
    ]

    # Create a styled table with 2 columns
    col1, col2 = st.columns(2)

    for i, lab in enumerate(lab_values):
        # Determine if value is normal
        is_normal = lab['normal_range'][0] <= lab['value'] <= lab['normal_range'][1]
        status_icon = "○" if is_normal else "●"

        if is_normal:
            status_text = "Normal"
            status_color = "#10B981"  # Green
        else:
            status_text = "High" if lab['value'] > lab['normal_range'][1] else "Low"
            status_color = "#EF4444"  # Red

        # Format value according to specified format
        formatted_value = f"{lab['value']:{lab['format']}}"

        # Alternate between columns
        with col1 if i % 2 == 0 else col2:
            # Custom styled metric card
            st.markdown(f"""
            <div style='background: #F8FAFC; padding: 16px; border-radius: 8px; border-left: 4px solid {status_color}; margin-bottom: 8px;'>
                <div style='font-weight: 600; color: #1F2937; margin-bottom: 4px;'>{lab['name']}</div>
                <div style='font-size: 24px; font-weight: 700; color: #1F2937; margin-bottom: 4px;'>
                    {formatted_value} <span style='font-size: 14px; font-weight: 400; color: #6B7280;'>{lab['unit']}</span>
                </div>
                <div style='font-size: 12px; color: {status_color}; display: flex; align-items: center;'>
                    <span style='margin-right: 4px;'>{status_icon}</span> {status_text}
                    <span style='color: #9CA3AF; margin-left: 8px;'>({lab['normal_range'][0]}-{lab['normal_range'][1]} {lab['unit']})</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Extract lab values for subsequent use in clinical decision support
    hematocrit = patient['hematocrit']
    creatinine = patient['creatinine']
    glucose = patient['glucose']

    st.markdown("<br>", unsafe_allow_html=True)

    # Clinical Decision Support
    st.markdown("### 🎯 Priority Actions")
    
    # Priority system: Critical -> High -> Medium -> Low
    critical_actions = []
    high_priority = []
    medium_priority = []
    low_priority = []
    
    # Critical (immediate action needed)
    if glucose > 300:
        critical_actions.append({
            'issue': 'Severe Hyperglycemia',
            'action': 'Immediate insulin protocol + hourly glucose monitoring',
            'timeline': 'NOW'
        })
    if creatinine > 2.0:
        critical_actions.append({
            'issue': 'Severe Kidney Dysfunction', 
            'action': 'Urgent nephrology consult + fluid balance review',
            'timeline': 'Within 2 hours'
        })
    if patient['pulse'] > 120 or patient['pulse'] < 50:
        critical_actions.append({
            'issue': f"{'High' if patient['pulse'] > 120 else 'Low'} Heart Rate",
            'action': 'ECG + cardiac monitoring + vitals q15min',
            'timeline': 'NOW'
        })
    if hematocrit < 8:
        critical_actions.append({
            'issue': 'Severe Anemia',
            'action': 'Type & cross + consider transfusion',
            'timeline': 'Within 1 hour'
        })
    
    # High Priority (same day)
    if glucose > 180:
        high_priority.append({
            'issue': 'Hyperglycemia',
            'action': 'Adjust insulin regimen + q6h glucose checks',
            'timeline': 'Within 4 hours'
        })
    if creatinine > 1.5:
        high_priority.append({
            'issue': 'Kidney Function Decline',
            'action': 'Review medications + increase monitoring',
            'timeline': 'Today'
        })
    if patient['lengthofstay'] > 10:
        high_priority.append({
            'issue': 'Extended Stay Risk',
            'action': 'Discharge planning meeting + complications review',
            'timeline': 'Today'
        })
    
    # Medium Priority (24-48 hours)
    if hematocrit < 12:
        medium_priority.append({
            'issue': 'Anemia',
            'action': 'Iron studies + nutrition consult',
            'timeline': 'Within 24h'
        })
    if patient['bmi'] < 18.5:
        medium_priority.append({
            'issue': 'Underweight',
            'action': 'Nutrition assessment + calorie count',
            'timeline': 'Within 48h'
        })
    if any(patient[col] == 1 for col in ['depress', 'psychologicaldisordermajor']):
        medium_priority.append({
            'issue': 'Mental Health Needs',
            'action': 'Psychology/psychiatry consult',
            'timeline': 'Within 48h'
        })
    
    # Low Priority (routine care)
    if patient['bmi'] > 25:
        low_priority.append({
            'issue': 'Weight Management',
            'action': 'Dietary counseling + activity plan',
            'timeline': 'Before discharge'
        })
    if patient['readmit_flag'] == 1:
        low_priority.append({
            'issue': 'Readmission Risk',
            'action': 'Enhanced discharge education + follow-up',
            'timeline': 'Before discharge'
        })
    
    # Display priorities
    if critical_actions:
        st.markdown("#### 🚨 **CRITICAL - Immediate Action Required**")
        for action in critical_actions:
            st.markdown(f"""
            <div style="background-color: #FFF5F5; border-left: 4px solid #D47A84; padding: 10px; margin: 5px 0;">
                <strong style="color: #D47A84;">{action['issue']}</strong><br>
                <strong>Action:</strong> {action['action']}<br>
                <strong>Timeline:</strong> {action['timeline']}
            </div>
            """, unsafe_allow_html=True)
    
    if high_priority:
        st.markdown("#### ⚠️ **HIGH PRIORITY - Same Day**")
        for action in high_priority:
            st.markdown(f"""
            <div style="background-color: #FFF8E1; border-left: 4px solid #E6B85C; padding: 10px; margin: 5px 0;">
                <strong style="color: #E6B85C;">{action['issue']}</strong><br>
                <strong>Action:</strong> {action['action']}<br>
                <strong>Timeline:</strong> {action['timeline']}
            </div>
            """, unsafe_allow_html=True)
    
    if medium_priority:
        st.markdown("#### 📋 **MEDIUM PRIORITY - 24-48 Hours**")
        for action in medium_priority:
            st.markdown(f"• **{action['issue']}**: {action['action']} ({action['timeline']})")
    
    if low_priority:
        st.markdown("#### 📝 **ROUTINE CARE**")
        for action in low_priority:
            st.markdown(f"• **{action['issue']}**: {action['action']} ({action['timeline']})")
    
    if not (critical_actions or high_priority or medium_priority or low_priority):
        st.markdown("✅ **No urgent interventions identified - continue routine care**")
    
    st.markdown("---")
    
    # Discharge Readiness Assessment
    st.markdown("### 🏠 Discharge Readiness")
    
    # Calculate discharge readiness score
    discharge_score = 0
    blocking_factors = []
    ready_factors = []
    
    # Medical stability (40% of score)
    if not critical_actions and not high_priority:
        discharge_score += 40
        ready_factors.append("Medical condition stable")
    else:
        blocking_factors.append("Unresolved critical/high priority issues")
    
    # Lab values stability (30% of score)
    stable_labs = 0
    total_labs = 0
    
    if 70 <= glucose <= 180:
        stable_labs += 1
        ready_factors.append("Glucose controlled")
    elif glucose > 180:
        blocking_factors.append("Uncontrolled glucose")
    total_labs += 1
    
    if 0.6 <= creatinine <= 1.5:
        stable_labs += 1
        ready_factors.append("Kidney function stable")
    elif creatinine > 1.5:
        blocking_factors.append("Kidney function concerns")
    total_labs += 1
    
    if hematocrit >= 10:
        stable_labs += 1
        ready_factors.append("Adequate blood levels")
    else:
        blocking_factors.append("Severe anemia needs treatment")
    total_labs += 1
    
    discharge_score += int(30 * stable_labs / total_labs)
    
    # Length of stay consideration (20% of score)
    if patient['lengthofstay'] <= 7:
        discharge_score += 20
        ready_factors.append("Appropriate length of stay")
    elif patient['lengthofstay'] > 14:
        blocking_factors.append("Extended stay - investigate barriers")
    else:
        discharge_score += 10
    
    # Social factors (10% of score)
    if patient['malnutrition'] == 0:
        discharge_score += 5
        ready_factors.append("Nutrition adequate")
    else:
        blocking_factors.append("Nutrition concerns need addressing")
    
    if not any(patient[col] == 1 for col in ['depress', 'psychologicaldisordermajor']):
        discharge_score += 5
        ready_factors.append("Mental health stable")
    else:
        blocking_factors.append("Mental health needs ongoing care")
    
    # Display discharge readiness
    if discharge_score >= 80:
        status_color = "#7FB069"
        status_text = "READY FOR DISCHARGE"
        status_icon = "✅"
    elif discharge_score >= 60:
        status_color = "#E6B85C"
        status_text = "DISCHARGE PLANNING NEEDED"
        status_icon = "⚠️"
    else:
        status_color = "#D47A84"
        status_text = "NOT READY - REQUIRES INTERVENTION"
        status_icon = "🚨"
    
    st.markdown(f"""
    <div style="background-color: #F8F9FA; border: 2px solid {status_color}; border-radius: 8px; padding: 15px; margin: 10px 0;">
        <h4 style="color: {status_color}; margin: 0;">{status_icon} {status_text}</h4>
        <p style="font-size: 18px; margin: 5px 0;"><strong>Discharge Readiness Score: {discharge_score}/100</strong></p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if ready_factors:
            st.markdown("**✅ Ready Indicators:**")
            for factor in ready_factors:
                st.markdown(f"• {factor}")
    
    with col2:
        if blocking_factors:
            st.markdown("**🚫 Blocking Factors:**")
            for factor in blocking_factors:
                st.markdown(f"• <span style='color: #D47A84;'>{factor}</span>", unsafe_allow_html=True)
    
    # Estimated discharge timeline
    if discharge_score >= 80:
        timeline = "Today - within 24 hours"
    elif discharge_score >= 60:
        timeline = "24-48 hours (after addressing issues)"
    else:
        timeline = "48+ hours (significant interventions needed)"
    
    st.markdown(f"**📅 Estimated Discharge Timeline:** {timeline}")
    
    # Bottom full width sections
    st.markdown("---")
    
    # Three-column layout for bottom sections
    bottom_col1, bottom_col2, bottom_col3 = st.columns(3)
    
    with bottom_col1:
        # Follow-up Schedule
        st.markdown("### Follow-up Schedule")
        import datetime
        admit_date = patient['vdate']
        discharge_date = patient['discharged']
        
        # Calculate follow-up dates based on risk level
        if patient['risk_level'] == 'High Risk':
            followup_days = 7
        else:
            followup_days = 30
            
        followup_date = discharge_date + pd.Timedelta(days=followup_days)
        st.write(f"**Next appointment:** {followup_date.strftime('%Y-%m-%d')}")
        st.write(f"**Appointment type:** {'High-priority' if patient['risk_level'] == 'High Risk' else 'Routine'} follow-up")
        
    with bottom_col2:
        # Timeline
        st.markdown("### Care Timeline")
        st.write(f"**Date of Birth:** {patient['Date_of_Birth'].strftime('%Y-%m-%d')}")
        st.write(f"**Age at admission:** {patient['age_at_admission']:.1f} years")
        st.write(f"**Admission:** {patient['vdate'].strftime('%Y-%m-%d')}")
        st.write(f"**Discharge:** {patient['discharged'].strftime('%Y-%m-%d')}")
        st.write(f"**Gender:** {patient['gender']}")
        
    with bottom_col3:
        # Emergency Information
        st.markdown("### Emergency Information")
        
        emergency_indicators = []
        if creatinine > 2.0:
            emergency_indicators.append("Severe kidney dysfunction")
        if glucose > 300:
            emergency_indicators.append("Severe hyperglycemia")
        if patient['pulse'] > 120:
            emergency_indicators.append("High heart rate")
        elif patient['pulse'] < 50:
            emergency_indicators.append("Low heart rate")
        if hematocrit < 8:
            emergency_indicators.append("Severe anemia")
            
        if emergency_indicators:
            st.write("**Alert conditions:**")
            for indicator in emergency_indicators:
                st.write(f"● {indicator}")
        else:
            st.write("○ No immediate emergency indicators")
            
        st.write(f"**Risk count:** {patient['rcount']}")
        st.write(f"**Priority level:** {'High' if patient['risk_level'] == 'High Risk' else 'Standard'}")

    # Patient Notes Section - Added for supplemental information
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📝 Patient Notes")
    st.markdown("Add supplemental information about this patient (symptoms, observations, care instructions, etc.):")

    # Get existing notes
    current_notes = get_patient_notes(patient_id)

    # Create a text area for notes
    notes_key = f"patient_notes_{patient_id}"
    if notes_key not in st.session_state:
        st.session_state[notes_key] = current_notes

    # Display text area with existing notes
    notes_text = st.text_area(
        "",
        value=st.session_state[notes_key],
        height=120,
        key=f"notes_input_{patient_id}",
        placeholder="Example: Patient reports mild headache in the morning. Family history of diabetes noted. Prefers vegetarian diet. Food allergies: peanuts..."
    )

    # Save button
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("💾 Save Notes", key=f"save_notes_{patient_id}"):
            if update_patient_notes(patient_id, notes_text):
                st.session_state[notes_key] = notes_text
                st.success("✅ Notes saved successfully!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Failed to save notes. Please try again.")

    with col2:
        if st.button("🗑️ Clear Notes", key=f"clear_notes_{patient_id}"):
            if update_patient_notes(patient_id, ""):
                st.session_state[notes_key] = ""
                st.success("✅ Notes cleared!")
                time.sleep(1)
                st.rerun()

    # Show character count
    if notes_text:
        st.caption(f"📊 {len(notes_text)} characters | These notes will be included in AI chat responses")
    else:
        st.info("💡 Add notes here to provide additional context for the AI assistant during conversations.")

    # Simple chat toggle using Streamlit
    chat_state_key = f"show_chat_{patient_id}"
    if chat_state_key not in st.session_state:
        st.session_state[chat_state_key] = False

    # Floating chat button in bottom right
    st.markdown("""
    <style>
    .chat-float-container {
        position: fixed;
        bottom: 30px;
        right: 30px;
        z-index: 1000;
    }
    .stButton > button {
        background-color: #374151;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 20px;
        font-weight: 500;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #4B5563;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transform: translateY(-1px);
    }
    </style>
    """, unsafe_allow_html=True)

    # Create a container for the floating button
    with st.container():
        col1, col2, col3 = st.columns([8, 1, 1])
        with col3:
            # Chat button removed - commented out
            # if st.button("💬 Chat", key=f"chat_toggle_{patient_id}", help="Open AI Assistant"):
            #     st.session_state[chat_state_key] = not st.session_state[chat_state_key]
            pass

    # Show chat interface if toggled - DISABLED
    if False:  # Chat interface disabled - was: st.session_state[chat_state_key]
        st.markdown("---")
        st.markdown(f"### 🤖 AI Medical Assistant")
        st.markdown(f"**Patient:** {patient['full_name']}")

        # Initialize chat history
        chat_key = f"simple_chat_{patient_id}"
        if chat_key not in st.session_state:
            pronoun = 'his' if patient['gender'] == 'M' else 'her'
            st.session_state[chat_key] = [
                {"role": "assistant", "content": f"I've reviewed {patient['full_name']}'s medical records and am ready to discuss {pronoun} case. How may I assist you with the clinical assessment or treatment planning?"}
            ]

        # File Upload Section - Always Visible
        st.markdown("---")
        st.markdown("### 📎 Attach Files to Chat")

        file_key = f"uploaded_file_{patient_id}"

        # Check if there's already an uploaded file
        if file_key in st.session_state:
            file_info = st.session_state[file_key]

            # Display attached file with remove option
            st.success(f"✅ **Attached:** {file_info['name']}")
            col1, col2 = st.columns([3, 1])
            with col1:
                if 'summary' in file_info and file_info['summary']:
                    st.caption(f"**AI Analysis:** {file_info['summary'][:150]}...")
                else:
                    st.caption(f"Type: {file_info['type']} • Size: {file_info['size']:,} bytes")
            with col2:
                if st.button("🗑️ Remove", key=f"remove_file_{patient_id}"):
                    del st.session_state[file_key]
                    st.rerun()
        else:
            # Show file uploader
            uploaded_file = st.file_uploader(
                "Upload medical records, lab results, images, or related documents",
                type=['pdf', 'jpg', 'jpeg', 'png', 'txt', 'doc', 'docx', 'csv'],
                key=f"file_upload_always_{patient_id}",
                help="Supported formats: PDF, Images (JPG/PNG), Text files, Word documents, CSV"
            )

            if uploaded_file is not None:
                with st.spinner("Processing file..."):
                    # Read file content
                    file_content = ""
                    file_type_info = ""
                    try:
                        uploaded_file.seek(0)

                        if uploaded_file.type == "text/plain":
                            file_content = str(uploaded_file.read(), "utf-8")
                            file_type_info = "Text file"
                        elif uploaded_file.type == "application/pdf":
                            file_type_info = "PDF file"
                            file_content = "PDF content (extraction requires PyPDF2 library)"
                        elif uploaded_file.type.startswith("image/"):
                            file_type_info = "Image file"
                            file_content = "Image content (analysis requires computer vision)"
                        elif uploaded_file.name.endswith('.csv'):
                            file_content = str(uploaded_file.read(), "utf-8")
                            file_type_info = "CSV file"
                        else:
                            try:
                                file_content = str(uploaded_file.read(), "utf-8")
                                file_type_info = "Document"
                            except:
                                file_content = "Binary file content"
                                file_type_info = "Binary file"
                    except Exception as e:
                        st.warning(f"Could not read file: {e}")
                        file_content = "File content unavailable"

                    # Generate AI summary
                    file_summary = ""
                    if 'openai_api_key' in st.session_state and st.session_state.openai_api_key and file_content:
                        try:
                            from openai import OpenAI
                            client = OpenAI(api_key=st.session_state.openai_api_key)

                            content_sample = file_content[:2000] + "..." if len(file_content) > 2000 else file_content

                            response = client.chat.completions.create(
                                model="gpt-3.5-turbo",
                                messages=[
                                    {"role": "system", "content": "You are a medical file analyst. Provide concise summaries of medical documents."},
                                    {"role": "user", "content": f"Analyze this file for patient {patient['full_name']}:\n\nFile: {uploaded_file.name}\nType: {uploaded_file.type}\n\nContent:\n{content_sample}\n\nProvide a brief medical summary (2-3 sentences)."}
                                ],
                                max_tokens=150,
                                temperature=0.1
                            )
                            file_summary = response.choices[0].message.content.strip()
                        except Exception as e:
                            file_summary = f"AI analysis unavailable: {str(e)}"

                    # Store file info
                    st.session_state[file_key] = {
                        "name": uploaded_file.name,
                        "type": uploaded_file.type,
                        "size": uploaded_file.size,
                        "summary": file_summary,
                        "content_preview": file_content[:500] + "..." if len(file_content) > 500 else file_content
                    }

                    st.rerun()

        st.markdown("---")

        # Display chat history
        for message in st.session_state[chat_key]:
            if message["role"] == "user":
                st.markdown(f"**🗣️ You:** {message['content']}")
            else:
                st.markdown(f"**🤖 AI:** {message['content']}")

        # Initialize voice-related session state
        voice_key = f"voice_input_{patient_id}"
        listening_key = f"listening_{patient_id}"

        if voice_key not in st.session_state:
            st.session_state[voice_key] = ""
        if listening_key not in st.session_state:
            st.session_state[listening_key] = False

        # Auto-speak control
        auto_speak_key = f"auto_speak_enabled_{patient_id}"
        if auto_speak_key not in st.session_state:
            st.session_state[auto_speak_key] = True

        col_toggle, col_info = st.columns([3, 1])
        with col_toggle:
            auto_speak_enabled = st.checkbox(
                "🔊 Auto-speak AI responses",
                value=st.session_state[auto_speak_key],
                key=f"auto_speak_checkbox_{patient_id}",
                help="Automatically read AI responses aloud when using voice input"
            )
            st.session_state[auto_speak_key] = auto_speak_enabled

        # Chat input
        with st.form(key=f"simple_chat_form_{patient_id}", clear_on_submit=True):
            user_input = st.text_input("Ask about this patient...",
                                       value=st.session_state[voice_key],
                                       key=f"simple_chat_input_{patient_id}")
            # Adjust columns based on voice availability
            if SHOW_VOICE_FEATURES:
                col1, col2 = st.columns([3, 1])
                with col1:
                    submitted = st.form_submit_button("Send", use_container_width=True, type="primary")
                with col2:
                    voice_clicked = st.form_submit_button("🎤 Voice", use_container_width=True)
            else:
                submitted = st.form_submit_button("Send", use_container_width=True, type="primary")
                voice_clicked = False  # No voice button in cloud environment

        # Handle voice input - unified interface for both environments
        if voice_clicked:
            # Always show the Web Speech API interface for consistency
            st.info("🎤 **Voice Recognition Active**")

            # Create a simpler solution using HTML input that can update session state
            speech_input_key = f"speech_input_{patient_id}"

            if speech_input_key not in st.session_state:
                st.session_state[speech_input_key] = ""

            # Check if we should also use Python speech recognition for local env
            use_python_speech = SPEECH_RECOGNITION_AVAILABLE and IS_LOCAL_ENV

            if use_python_speech:
                st.markdown("*Using enhanced local speech recognition with Web interface*")
            else:
                st.markdown("*Using browser-based speech recognition*")

            # Display unified speech recognition interface
            html_content = f"""
                <script>
                console.log('Embedded voice interface loaded - no external dependencies needed');

                // Simple test function for debugging
                function testFunction() {{
                    console.log('Test function called');
                    alert('JavaScript is working! Voice recognition is embedded in buttons.');
                }}

                // Global variables for compatibility
                window.currentRecognition = null;
                window.currentSpeechText = '';
                window.speechInputUsed = false;

                console.log('✅ Voice script loaded - all functionality embedded in buttons');

                // Additional speech recognition functions
                window.stopSpeechRecognition = function() {{
                    if (window.recognition) {{
                        window.recognition.stop();
                    }}
                }};

                window.resetSpeechButtons = function() {{
                    const startBtn = document.getElementById('startSpeech');
                    const stopBtn = document.getElementById('stopSpeech');
                    if (startBtn) startBtn.disabled = false;
                    if (stopBtn) stopBtn.disabled = true;
                }};

                window.useSpeechResult = function() {{
                    if (window.currentSpeechText) {{
                        console.log('Using speech result:', window.currentSpeechText);
                        document.getElementById('speechStatus').innerHTML = '🔍 Finding Streamlit input...';

                        // Mark that speech input was used - key for auto-TTS trigger
                        window.speechInputUsed = true;

                        let targetInput = null;
                        let submitButton = null;

                        // Strategy 1: Enhanced Streamlit chat input detection
                        const chatSelectors = [
                            'input[data-testid="stChatInput"] input',
                            'input[data-testid="stTextInput"] input',
                            'div[data-testid="stChatInput"] input',
                            'div[data-testid="stTextInput"] input',
                            'input[placeholder*="Ask about this patient"]',
                            'input[placeholder*="Ask"]',
                            'input[placeholder*="chat" i]',
                            'textarea[placeholder*="message" i]',
                            'input[aria-label*="Ask about this patient"]'
                        ];

                        let streamlitInputs = [];
                        for (let selector of chatSelectors) {{
                            const found = document.querySelectorAll(selector);
                            streamlitInputs.push(...found);
                        }}
                        console.log('Found Streamlit inputs:', streamlitInputs.length);

                        // Enhanced debugging - always show all inputs for troubleshooting
                        const allInputs = document.querySelectorAll('input, textarea');
                        console.log('=== VOICE DEBUG: All inputs on page ===', allInputs.length);
                        allInputs.forEach((input, i) => {{
                            const rect = input.getBoundingClientRect();
                            console.log(`Input ${{i}}:`, {{
                                tag: input.tagName,
                                type: input.type,
                                placeholder: input.placeholder,
                                id: input.id,
                                className: input.className,
                                visible: rect.width > 0 && rect.height > 0,
                                dataset: input.dataset,
                                form: input.closest('form') ? 'IN-FORM' : 'NO-FORM',
                                value: input.value
                            }});
                        }});

                        // Try first input from specific selectors
                        if (streamlitInputs.length > 0) {{
                            for (let input of streamlitInputs) {{
                                const rect = input.getBoundingClientRect();
                                if (rect.width > 50 && rect.height > 10 && !input.disabled && !input.readOnly) {{
                                    targetInput = input;
                                    break;
                                }}
                            }}
                        }}

                        // Strategy 2: Find by nearby form submit buttons
                        const submitButtons = document.querySelectorAll('button[kind="primary"], button[type="submit"], button:contains("Send")');
                        console.log('Found submit buttons:', submitButtons.length);

                        for (let btn of submitButtons) {{
                            const form = btn.closest('form') || btn.closest('[data-testid*="form"]');
                            if (form) {{
                                const inputs = form.querySelectorAll('input[type="text"], textarea, input:not([type])');
                                for (let input of inputs) {{
                                    const rect = input.getBoundingClientRect();
                                    if (rect.width > 100 && rect.height > 20 && !input.disabled && !input.readOnly) {{
                                        targetInput = input;
                                        submitButton = btn;
                                        break;
                                    }}
                                }}
                                if (targetInput) break;
                            }}
                        }}

                        // Strategy 3: Find by Streamlit widget structure
                        if (!targetInput) {{
                            const widgets = document.querySelectorAll('[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea');
                            for (let widget of widgets) {{
                                const rect = widget.getBoundingClientRect();
                                if (rect.width > 100 && rect.height > 20 && !widget.disabled && !widget.readOnly) {{
                                    targetInput = widget;
                                    // Look for nearby submit button
                                    const container = widget.closest('.stForm, form, [data-testid*="form"]');
                                    if (container) {{
                                        submitButton = container.querySelector('button[kind="primary"], button[type="submit"]');
                                    }}
                                    break;
                                }}
                            }}
                        }}

                        // Strategy 4: Streamlit form text input specifically
                        if (!targetInput) {{
                            // Look for Streamlit text inputs within forms
                            const formInputs = document.querySelectorAll('form [data-testid="stTextInput"] input, [data-testid="stForm"] [data-testid="stTextInput"] input');
                            console.log('Found form text inputs:', formInputs.length);
                            for (let input of formInputs) {{
                                const rect = input.getBoundingClientRect();
                                if (rect.width > 100 && rect.height > 20 && !input.disabled && !input.readOnly) {{
                                    targetInput = input;
                                    console.log('Found form text input');
                                    break;
                                }}
                            }}
                        }}

                        // Strategy 5: Streamlit chat message input specifically
                        if (!targetInput) {{
                            // Look for the Streamlit chat input which often has distinctive styling
                            const chatWidgets = document.querySelectorAll('[data-testid="stChatInput"]');
                            for (let widget of chatWidgets) {{
                                const input = widget.querySelector('input') || widget.querySelector('textarea');
                                if (input) {{
                                    targetInput = input;
                                    console.log('Found chat widget input');
                                    break;
                                }}
                            }}
                        }}

                        // Strategy 6: Direct text match approach with multiple attempts
                        if (!targetInput) {{
                            console.log('Strategy 6: Searching through all inputs...');

                            // Try multiple times with delays to handle dynamic content
                            for (let attempt = 0; attempt < 3; attempt++) {{
                                const allInputs = document.querySelectorAll('input, textarea');
                                console.log(`Attempt ${{attempt + 1}}: Found ${{allInputs.length}} inputs`);

                                for (let input of allInputs) {{
                                    const rect = input.getBoundingClientRect();

                                    // Strategy 6a: Exact placeholder match
                                    if (input.placeholder && input.placeholder.includes('Ask about this patient')) {{
                                        targetInput = input;
                                        console.log('✅ Found target by exact placeholder match!');
                                        break;
                                    }}

                                    // Strategy 6b: Any "Ask" related placeholder
                                    if (input.placeholder && input.placeholder.toLowerCase().includes('ask')) {{
                                        targetInput = input;
                                        console.log('✅ Found target by "Ask" keyword match!');
                                        break;
                                    }}

                                    // Strategy 6c: Text inputs in forms that are currently visible and active
                                    if ((input.type === 'text' || input.type === '' || input.tagName === 'TEXTAREA') &&
                                        rect.width > 200 && rect.height > 25 && !input.disabled && !input.readOnly &&
                                        input.offsetParent !== null) {{ // Check if element is actually visible

                                        console.log('Potential input found:', {{
                                            placeholder: input.placeholder,
                                            rect: rect,
                                            visible: input.offsetParent !== null,
                                            form: input.closest('form') ? 'IN-FORM' : 'NO-FORM'
                                        }});

                                        if (!targetInput) {{ // Take first suitable one as fallback
                                            targetInput = input;
                                            console.log('Taking this as fallback input');
                                        }}
                                    }}
                                }}

                                if (targetInput) break;

                                // Wait before next attempt
                                if (attempt < 2) {{
                                    console.log('No input found, waiting 200ms before next attempt...');
                                    await new Promise(resolve => setTimeout(resolve, 200));
                                }}
                            }}
                        }}

                        // Strategy 7: Last resort - any visible text input
                        if (!targetInput) {{
                            const allInputs = document.querySelectorAll('input, textarea');
                            for (let input of allInputs) {{
                                const rect = input.getBoundingClientRect();
                                const style = window.getComputedStyle(input);

                                const isVisible = style.display !== 'none' &&
                                                style.visibility !== 'hidden' &&
                                                rect.width > 100 && rect.height > 20;
                                const isUsable = !input.disabled && !input.readOnly;

                                if (isVisible && isUsable) {{
                                    targetInput = input;
                                    break;
                                }}
                            }}
                        }}

                        if (targetInput) {{
                            console.log('✅ FOUND TARGET INPUT:', {{
                                element: targetInput,
                                placeholder: targetInput.placeholder,
                                id: targetInput.id,
                                className: targetInput.className,
                                type: targetInput.type,
                                form: targetInput.closest('form') ? 'IN-FORM' : 'NO-FORM'
                            }});

                            // Clear existing content first
                            targetInput.value = '';
                            targetInput.focus();

                            // Insert text
                            targetInput.value = window.currentSpeechText;

                            // Trigger all necessary events for Streamlit
                            const events = [
                                new Event('input', {{ bubbles: true, cancelable: true }}),
                                new Event('change', {{ bubbles: true, cancelable: true }}),
                                new KeyboardEvent('keydown', {{ bubbles: true, cancelable: true, key: 'Enter' }}),
                                new KeyboardEvent('keyup', {{ bubbles: true, cancelable: true, key: 'Enter' }})
                            ];

                            events.forEach(event => targetInput.dispatchEvent(event));

                            // Mark input as voice-originated
                            targetInput.setAttribute('data-voice-input', 'true');
                            sessionStorage.setItem('voice_input_used', 'true');
                            sessionStorage.setItem('lastSuccessfulVoiceInput', window.currentSpeechText);

                            document.getElementById('speechStatus').innerHTML = '✅ Text inserted!';
                            document.getElementById('speechStatus').style.color = '#00c851';

                            // Try automatic submission after a short delay
                            if (submitButton) {{
                                console.log('🚀 Auto-clicking submit button');
                                setTimeout(() => {{
                                    submitButton.click();
                                    document.getElementById('speechStatus').innerHTML = '✅ Text sent!';
                                }}, 500);
                            }} else {{
                                console.log('⚠️ No submit button found for auto-submission');
                            }}

                            console.log('✅ Speech text inserted successfully:', window.currentSpeechText);
                        }} else {{
                            console.error('❌ NO SUITABLE INPUT FOUND!');
                            console.log('=== VOICE INPUT FAILURE SUMMARY ===');
                            console.log('Total inputs on page:', allInputs.length);
                            console.log('Speech text:', window.currentSpeechText);
                            console.log('All strategies failed to find target input');

                            // Store for manual retrieval
                            sessionStorage.setItem('pendingVoiceInput', window.currentSpeechText);
                            sessionStorage.setItem('voiceInputFailureTime', new Date().toISOString());

                            // Simple fallback without popups
                            if (navigator.clipboard && navigator.clipboard.writeText) {{
                                navigator.clipboard.writeText(window.currentSpeechText).then(() => {{
                                    document.getElementById('speechStatus').innerHTML = '📋 已复制到剪贴板 - 请粘贴到输入框';
                                    document.getElementById('speechStatus').style.color = '#ff9800';
                                    console.log('✅ Fallback: Copied to clipboard:', window.currentSpeechText);
                                }}).catch(() => {{
                                    document.getElementById('speechStatus').innerHTML = `⚠️ 语音结果: "${{window.currentSpeechText}}"`;
                                    document.getElementById('speechStatus').style.color = '#ff4444';
                                }});
                            }} else {{
                                document.getElementById('speechStatus').innerHTML = `📝 语音结果: "${{window.currentSpeechText}}"`;
                                document.getElementById('speechStatus').style.color = '#2196F3';
                                console.log('Voice result for manual copy:', window.currentSpeechText);
                            }}
                        }}
                    }}
                }};

                window.startSpeechRecognitionBasic = function() {{
                    document.getElementById('speechStatus').innerHTML = '🔍 Checking browser support...';

                    // Enhanced environment detection for speech recognition
                    console.log('Current protocol:', location.protocol);
                    console.log('Current hostname:', location.hostname);
                    console.log('Current href:', location.href);
                    console.log('User agent:', navigator.userAgent);

                    // Check if we're in a supported environment
                    const isHTTPS = location.protocol === 'https:';
                    const isLocalhost = location.hostname === 'localhost' || location.hostname === '127.0.0.1';
                    const isPrivateNetwork = location.hostname.startsWith('192.168.') ||
                                           location.hostname.startsWith('10.') ||
                                           location.hostname.startsWith('172.16.');
                    const isEmbeddedOrSpecial = location.protocol === 'about:' ||
                                               location.protocol === 'file:' ||
                                               location.protocol === 'moz-extension:' ||
                                               location.protocol === 'chrome-extension:';

                    console.log('Environment check:', {{
                        isHTTPS: isHTTPS,
                        isLocalhost: isLocalhost,
                        isPrivateNetwork: isPrivateNetwork,
                        isEmbeddedOrSpecial: isEmbeddedOrSpecial
                    }});

                    // Allow speech recognition if any of these conditions are met:
                    const isAllowedEnvironment = isHTTPS || isLocalhost || isPrivateNetwork || isEmbeddedOrSpecial;

                    if (!isAllowedEnvironment) {{
                        document.getElementById('speechStatus').innerHTML =
                            '⚠️ Speech recognition requires HTTPS or localhost.<br>' +
                            'Current: ' + location.protocol + '//' + location.hostname + '<br>' +
                            'Try accessing via https:// or localhost';
                        document.getElementById('speechStatus').style.color = '#ff9800';
                        return;
                    }}

                    console.log('Environment check passed - proceeding with speech recognition');

                    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {{
                        document.getElementById('speechStatus').innerHTML = '✅ Speech recognition supported, starting...';
                        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

                        try {{
                            window.recognition = new SpeechRecognition();
                            console.log('SpeechRecognition object created successfully');

                            window.recognition.continuous = false;
                            window.recognition.interimResults = false;
                            window.recognition.lang = 'en-US';

                            window.recognition.onstart = function() {{
                                console.log('Speech recognition started');
                                const startBtn = document.getElementById('startSpeech');
                                const stopBtn = document.getElementById('stopSpeech');
                                if (startBtn) startBtn.disabled = true;
                                if (stopBtn) stopBtn.disabled = false;
                                document.getElementById('speechStatus').innerHTML = '🎧 Listening... Please speak now!';
                                document.getElementById('speechStatus').style.color = '#ff4b4b';
                                document.getElementById('speechResult').innerHTML = '<em>Listening...</em>';
                            }};

                            window.recognition.onresult = function(event) {{
                                console.log('Speech recognition result received:', event);
                                const text = event.results[0][0].transcript;
                                const confidence = event.results[0][0].confidence;
                                window.currentSpeechText = text;
                                document.getElementById('speechResult').innerHTML = '<strong>Recognized:</strong> ' + text +
                                    ' <small>(confidence: ' + (confidence ? (confidence * 100).toFixed(1) + '%' : 'N/A') + ')</small>';
                                document.getElementById('speechStatus').innerHTML = '✅ Speech recognition completed!';
                                document.getElementById('speechStatus').style.color = '#00c851';
                                document.getElementById('useSpeech').style.display = 'inline-block';
                            }};

                            window.recognition.onerror = function(event) {{
                                console.error('Speech recognition error:', event);
                                let errorMsg = 'Unknown error';
                                switch(event.error) {{
                                    case 'no-speech':
                                        errorMsg = 'No speech detected. Please try again.';
                                        break;
                                    case 'audio-capture':
                                        errorMsg = 'Audio capture failed. Check your microphone.';
                                        break;
                                    case 'not-allowed':
                                        errorMsg = 'Microphone access denied. Please allow microphone access.';
                                        break;
                                    case 'network':
                                        errorMsg = 'Network error. Check your internet connection.';
                                        break;
                                    case 'service-not-allowed':
                                        errorMsg = 'Speech service not allowed. Try using HTTPS.';
                                        break;
                                    default:
                                        errorMsg = event.error;
                                }}
                                document.getElementById('speechStatus').innerHTML = '❌ Error: ' + errorMsg;
                                document.getElementById('speechStatus').style.color = '#ff4444';
                                window.resetSpeechButtons();
                            }};

                            window.recognition.onend = function() {{
                                console.log('Speech recognition ended');
                                window.resetSpeechButtons();
                            }};

                            console.log('Starting speech recognition...');
                            document.getElementById('speechStatus').innerHTML = '🎤 Starting microphone...';
                            window.recognition.start();

                        }} catch (error) {{
                            console.error('Error creating/starting speech recognition:', error);
                            document.getElementById('speechStatus').innerHTML = '❌ Failed to start: ' + error.message;
                            document.getElementById('speechStatus').style.color = '#ff4444';
                            window.resetSpeechButtons();
                        }}
                    }} else {{
                        document.getElementById('speechStatus').innerHTML = '❌ Speech recognition not supported in this browser';
                        document.getElementById('speechStatus').style.color = '#ff4444';
                    }}
                }};

                // Initialize and verify all functions are loaded
                function initializeVoiceInterface() {{
                    console.log('Initializing voice interface...');

                    // Check if all required functions are available
                    var functionsToCheck = ['startSpeechRecognitionBasic', 'stopSpeechRecognition', 'useSpeechResult', 'testFunction'];
                    var allFunctionsAvailable = true;

                    for (var i = 0; i < functionsToCheck.length; i++) {{
                        if (typeof window[functionsToCheck[i]] !== 'function') {{
                            console.error('Function not available:', functionsToCheck[i]);
                            allFunctionsAvailable = false;
                        }} else {{
                            console.log('Function available:', functionsToCheck[i]);
                        }}
                    }}

                    if (allFunctionsAvailable) {{
                        console.log('✅ All speech functions loaded successfully');
                        if (document.getElementById('speechStatus')) {{
                            document.getElementById('speechStatus').innerHTML = '✅ Voice interface ready! Click "Start Voice Input" to begin.';
                            document.getElementById('speechStatus').style.color = '#00c851';
                        }}
                    }} else {{
                        console.error('❌ Some speech functions failed to load');
                        if (document.getElementById('speechStatus')) {{
                            document.getElementById('speechStatus').innerHTML = '❌ Voice interface failed to load. Try refreshing the page.';
                            document.getElementById('speechStatus').style.color = '#ff4444';
                        }}
                    }}
                }}

                // Initialize after a short delay to ensure DOM is ready
                setTimeout(initializeVoiceInterface, 500);

                console.log('Voice script loaded successfully');
                </script>

                <div style="margin: 10px 0; padding: 15px; background: #f0f2f6; border-radius: 8px;">
                    <button onclick="
                        console.log('Button clicked directly!');
                        document.getElementById('speechStatus').innerHTML = 'Button clicked! JavaScript is working...';
                        testFunction();
                    " style="background: #ff4b4b; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; margin-right: 10px;">
                        🎤 Test Click
                    </button>

                    <button id="startSpeech" onclick="window.startSpeechRecognitionBasic();"
                            style="background: #00c851; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; margin-right: 10px;">
                        🎤 Start Voice Input
                    </button>

                    <button id="stopSpeech" onclick="window.stopSpeechRecognition();"
                            style="background: #666; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer;" disabled>
                        ⏹️ Stop
                    </button>
                    <div id="speechStatus" style="margin-top: 10px; font-size: 14px; color: #666;">
                        ✅ Voice interface ready! Click "Start Voice Input" to begin.
                    </div>
                    <div id="speechResult" style="margin-top: 10px; padding: 10px; background: white; border-radius: 4px; min-height: 40px; border: 1px solid #ddd;">
                        <em>Your speech will appear here...</em>
                    </div>
                    <button id="useSpeech" onclick="window.useSpeechResult();"
                            style="background: #00c851; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; margin-top: 10px; display: none;">
                        📝 Insert into Chat
                    </button>
                </div>

                """

            components.html(html_content, height=250)

        # Handle user input submission
        if submitted and user_input:
            # Add user message
            st.session_state[chat_key].append({"role": "user", "content": user_input})

            # Simple and reliable voice input detection
            # Use a custom component to check sessionStorage
            voice_check_html = """
            <script>
            const voiceUsed = sessionStorage.getItem('voice_input_used') === 'true';
            if (voiceUsed) {
                sessionStorage.removeItem('voice_input_used');
                document.body.setAttribute('data-voice-input-detected', 'true');
            }
            </script>
            """
            components.html(voice_check_html, height=0)

            # Check if auto-speak should be enabled for this session
            auto_speak_enabled = st.session_state.get(f"auto_speak_enabled_{patient_id}", True)
            if auto_speak_enabled:
                st.session_state[f"auto_speak_{patient_id}"] = True

            # Generate AI response using OpenAI
            try:
                if 'openai_api_key' in st.session_state and st.session_state.openai_api_key:
                    from openai import OpenAI
                    client = OpenAI(api_key=st.session_state.openai_api_key)

                    # Create patient context
                    # Get patient notes
                    patient_notes = get_patient_notes(patient_id)
                    notes_section = f"\n\n                    Additional Clinical Notes:\n                    {patient_notes}" if patient_notes else ""

                    patient_context = f"""
                    Patient Information:
                    - Name: {patient['full_name']}
                    - Gender: {'Male' if patient['gender'] == 'M' else 'Female'}
                    - Age Group: {patient.get('age_group', 'Unknown')}
                    - Admission Reason: {patient.get('admission_reason', 'Not specified')}
                    - Length of Stay: {patient['lengthofstay']} days
                    - Admission Date: {patient['vdate']}
                    - Discharge Date: {patient['discharged']}
                    - Facility: {patient['facid']}
                    - Risk Level: {patient.get('risk_level', 'Standard')}

                    Lab Values:
                    - Glucose: {patient.get('glucose', 'N/A')}
                    - Creatinine: {patient.get('creatinine', 'N/A')}
                    - Hematocrit: {patient.get('hematocrit', 'N/A')}
                    - BMI: {patient.get('bmi', 'N/A')}

                    Medical Conditions:
                    - Asthma: {'Yes' if patient.get('asthma', 0) == 1 else 'No'}
                    - Pneumonia: {'Yes' if patient.get('pneum', 0) == 1 else 'No'}
                    - Diabetes: {'Yes' if patient.get('dialysisrenalendstage', 0) == 1 else 'No'}
                    - Depression: {'Yes' if patient.get('depress', 0) == 1 else 'No'}{notes_section}
                    """

                    # Check if there's an uploaded file
                    file_key = f"uploaded_file_{patient_id}"
                    file_context = ""
                    if file_key in st.session_state:
                        file_info = st.session_state[file_key]
                        file_context = f"\n\nAttached file: {file_info['name']} (Type: {file_info['type']}, Size: {file_info['size']} bytes)"

                        # Include AI-generated file summary if available
                        if 'summary' in file_info and file_info['summary']:
                            file_context += f"\nFile Analysis: {file_info['summary']}"

                        # Include content preview for text files
                        if 'content_preview' in file_info and file_info['content_preview']:
                            file_context += f"\nContent Preview: {file_info['content_preview']}"

                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a senior medical specialist with 20+ years of clinical experience in internal medicine, emergency care, and hospital management. You have expertise in interpreting lab values, assessing patient risk factors, and providing evidence-based medical recommendations. Respond as an experienced clinician would - provide direct, professional medical analysis without introducing yourself. Be clear, actionable, and use appropriate medical terminology while explaining complex concepts when needed. Always use correct pronouns based on patient gender. When files are attached, acknowledge them and provide guidance on how they might relate to the patient's care."},
                            {"role": "user", "content": f"Patient context:\n{patient_context}{file_context}\n\nUser question: {user_input}"}
                        ],
                        max_tokens=500,
                        temperature=0.7
                    )

                    ai_response = response.choices[0].message.content.strip()
                else:
                    ai_response = "Please enter your OpenAI API key in the dashboard sidebar to enable AI responses. I can provide basic patient information in the meantime."

            except Exception as e:
                ai_response = f"I'm having trouble connecting to the AI service. Error: {str(e)}. Please check your API key or try again later."

            # Add AI response to chat
            st.session_state[chat_key].append({"role": "assistant", "content": ai_response})

            # Clear voice input after successful submission
            st.session_state[voice_key] = ""

            # Auto-speak AI response if it came from voice input
            if st.session_state.get(f"auto_speak_{patient_id}", False):
                if SPEECH_RECOGNITION_AVAILABLE and IS_LOCAL_ENV:
                    # Local environment - use Python TTS
                    threading.Thread(
                        target=lambda: speak_text(ai_response),
                        daemon=True
                    ).start()
                else:
                    # Cloud environment - use Web Speech API
                    tts_session_id = f"tts_{patient_id}_{int(time.time())}"
                    tts_html = speak_text_web(ai_response, tts_session_id)
                    components.html(tts_html, height=0)  # Hidden component, just for TTS
                st.session_state[f"auto_speak_{patient_id}"] = False

            st.rerun()

        # Close chat button
        if st.button("❌ Close Chat", key=f"close_chat_{patient_id}"):
            st.session_state[chat_state_key] = False
            st.rerun()

    # Add patient-specific floating chat widget with voice support
    add_patient_chat(patient)

def main():
    # Initialize session state
    if "current_page" not in st.session_state:
        st.session_state.current_page = "dashboard"
    if "selected_patient" not in st.session_state:
        st.session_state.selected_patient = None
    
    # Load data
    df, disease_cols = load_data()
    
    # Check if we should show patient detail page
    if st.session_state.current_page == "patient_detail" and st.session_state.selected_patient:
        show_patient_detail(st.session_state.selected_patient, df)
        return
    
    # Header
    st.markdown("""
    <div class="main-header">
        <div class="main-title">Healthcare Analytics</div>
        <div class="main-subtitle">Patient Care & Performance Insights</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar filters (moved to sidebar with chat)
    with st.sidebar:
        # OpenAI API Key input
        st.markdown("### ⚙️ Settings")
        api_key_input = st.text_input(
            "OpenAI API Key",
            type="password",
            placeholder="sk-...",
            help="Enter your OpenAI API key to enable AI chat features",
            key="dashboard_api_key"
        )

        if api_key_input:
            st.session_state.openai_api_key = api_key_input
            setup_openai_api()  # Update environment variable
            st.success("✅ API key configured")
        elif not api_key_input and 'openai_api_key' not in st.session_state:
            st.info("💡 Enter API key to enable AI features")

        st.markdown("---")

        st.markdown("### 🔍 Filters")

        # Date range filter
        date_range = st.date_input(
            "Date Range",
            value=[df['vdate'].min().date(), df['vdate'].max().date()],
            min_value=df['vdate'].min().date(),
            max_value=df['vdate'].max().date()
        )
        
        # Gender filter
        gender_options = st.multiselect(
            "Gender",
            options=['M', 'F'],
            default=['M', 'F']
        )
        
        # Department filter
        dept_options = st.multiselect(
            "Department",
            options=sorted(df['facid'].unique()),
            default=sorted(df['facid'].unique())
        )
        
        # Age group filter
        age_options = st.multiselect(
            "Age Group",
            options=sorted(df['age_group'].dropna().unique()),
            default=sorted(df['age_group'].dropna().unique())
        )
        
        # Risk level filter
        risk_options = st.multiselect(
            "Risk Level",
            options=["Standard Risk", "High Risk"],
            default=["Standard Risk", "High Risk"]
        )
    
    # Handle date range - ensure we have both start and end dates
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start_date, end_date = date_range[0], date_range[1]
    else:
        # If only one date is selected, use it as both start and end
        start_date = end_date = date_range if not isinstance(date_range, (list, tuple)) else date_range[0]
    
    # Apply filters with error handling
    try:
        mask = (
            (df['vdate'].dt.date >= start_date) &
            (df['vdate'].dt.date <= end_date)
        )
        
        if gender_options:
            mask = mask & (df['gender'].isin(gender_options))
        if dept_options:
            mask = mask & (df['facid'].isin(dept_options))
        if age_options:
            mask = mask & (df['age_group'].isin(age_options))
        if risk_options:
            mask = mask & (df['risk_level'].isin(risk_options))
            
        filtered_df = df[mask]
        
        if filtered_df.empty:
            st.warning("No data available with current filters. Please adjust your selection.")
            # Show charts with full dataset instead of returning
            filtered_df = df
    except Exception as e:
        st.error(f"Filter error: {e}")
        # Use full dataset if filtering fails
        filtered_df = df
    
    # KPI Section
    st.markdown('<div class="section-header">Key Performance Indicators</div>', unsafe_allow_html=True)
    create_kpi_cards(filtered_df)
    
    # Charts section
    st.markdown('<div class="section-header">Analytics Dashboard</div>', unsafe_allow_html=True)
    
    # Two column layout for charts
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        create_dept_comparison(filtered_df)
        st.markdown("<br>", unsafe_allow_html=True)
        create_lab_scatter(filtered_df)
    
    with col2:
        create_disease_heatmap(filtered_df, disease_cols)
        st.markdown("<br>", unsafe_allow_html=True)
        create_trend_analysis(filtered_df)
    
    # Detailed analysis
    st.markdown('<div class="section-header">Patient Details</div>', unsafe_allow_html=True)
    create_detail_table(filtered_df)

    # AI floating chat widget
    add_floating_chat()

def create_kpi_cards(df):
    """Create KPI cards with Nordic styling"""
    col1, col2, col3, col4 = st.columns(4, gap="medium")
    
    avg_los = df['lengthofstay'].mean()
    long_stay_rate = (df['lengthofstay'] > 7).mean() * 100
    readmit_rate = df['readmit_flag'].mean() * 100
    turnover = 365 / avg_los
    
    with col1:
        st.metric(
            "Average Length of Stay",
            f"{avg_los:.1f} days",
            delta=None
        )
    
    with col2:
        st.metric(
            "Extended Stay Rate",
            f"{long_stay_rate:.1f}%",
            delta=None
        )
    
    with col3:
        st.metric(
            "Readmission Rate",
            f"{readmit_rate:.1f}%",
            delta=None
        )
    
    with col4:
        st.metric(
            "Bed Turnover Rate",
            f"{turnover:.1f}/year",
            delta=None
        )

def create_dept_comparison(df):
    """Create department comparison chart with Nordic styling"""
    dept_stats = df.groupby('facid', observed=False)['lengthofstay'].agg(['mean', 'count']).reset_index()
    dept_stats = dept_stats[dept_stats['count'] >= 10]
    
    fig = px.bar(
        dept_stats.sort_values('mean', ascending=True), 
        x='mean', 
        y='facid',
        orientation='h',
        title="Average Length of Stay by Department",
        labels={'mean': 'Days', 'facid': 'Department'},
        color='mean',
        color_continuous_scale=['#A8B8C2', '#6C7B7F', '#2E5266']
    )
    
    fig.update_layout(create_chart_template()['layout'])
    fig.update_layout(height=400, showlegend=False)
    fig.update_coloraxes(showscale=False)
    
    st.plotly_chart(fig, use_container_width=True)

def create_disease_heatmap(df, disease_cols):
    """Create disease heatmap with Nordic styling"""
    disease_los = []
    disease_names = {
        'dialysisrenalendstage': 'Renal Disease',
        'asthma': 'Asthma',
        'irondef': 'Iron Deficiency',
        'pneum': 'Pneumonia',
        'substancedependence': 'Substance Abuse',
        'psychologicaldisordermajor': 'Psychological Disorder',
        'depress': 'Depression',
        'psychother': 'Psychotherapy',
        'fibrosisandother': 'Fibrosis',
        'malnutrition': 'Malnutrition'
    }
    
    for disease in disease_cols:
        disease_df = df[df[disease] == 1]
        if len(disease_df) >= 5:
            avg_los = disease_df['lengthofstay'].mean()
            disease_los.append({
                'condition': disease_names.get(disease, disease),
                'avg_los': avg_los,
                'count': len(disease_df)
            })
    
    if disease_los:
        disease_df = pd.DataFrame(disease_los).sort_values('avg_los', ascending=True)
        
        fig = px.bar(
            disease_df,
            x='avg_los',
            y='condition',
            orientation='h',
            title="Condition Impact on Length of Stay",
            labels={'avg_los': 'Average Days', 'condition': 'Medical Condition'},
            color='avg_los',
            color_continuous_scale=['#7FB069', '#E6B85C', '#D47A84']
        )
        
        fig.update_layout(create_chart_template()['layout'])
        fig.update_layout(height=400, showlegend=False)
        fig.update_coloraxes(showscale=False)
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Insufficient condition data for visualization")

def create_lab_scatter(df):
    """Create lab bubble chart for risk stratification with Nordic styling"""
    st.markdown("**Laboratory Indicators & Risk Stratification**")
    
    # Lab metric selection
    lab_metrics = st.selectbox(
        "Laboratory Metric",
        ['creatinine', 'glucose', 'hematocrit', 'neutrophils', 'sodium', 'bloodureanitro'],
        key="lab_selector"
    )
    
    # Clean and prepare data
    clean_df = df.dropna(subset=[lab_metrics, 'lengthofstay']).copy()
    
    # Remove outliers for better visualization
    q1 = clean_df[lab_metrics].quantile(0.05)
    q99 = clean_df[lab_metrics].quantile(0.95)
    clean_df = clean_df[(clean_df[lab_metrics] >= q1) & (clean_df[lab_metrics] <= q99)]
    
    # Create value-based bins instead of quantile-based bins
    min_val = clean_df[lab_metrics].min()
    max_val = clean_df[lab_metrics].max()
    
    # Create 8-12 equal-width bins based on value range
    n_bins = min(12, max(8, int((max_val - min_val) / (clean_df[lab_metrics].std() * 0.5))))
    lab_bins = pd.cut(clean_df[lab_metrics], bins=n_bins, include_lowest=True)
    
    # Group data for bubble chart
    bubble_data = []
    for lab_range, group in clean_df.groupby(lab_bins, observed=False):
        if len(group) >= 10:  # Minimum sample size for reliability
            avg_lab_value = group[lab_metrics].mean()
            avg_los = group['lengthofstay'].mean()
            readmit_rate = group['readmit_flag'].mean() * 100
            patient_count = len(group)
            
            # Format the range for better display
            range_str = f"{lab_range.left:.2f} - {lab_range.right:.2f}"
            
            bubble_data.append({
                'lab_value': avg_lab_value,
                'avg_los': avg_los,
                'readmit_rate': readmit_rate,
                'patient_count': patient_count,
                'lab_range': range_str
            })
    
    if not bubble_data:
        st.warning("Insufficient data for bubble chart analysis")
        return
        
    bubble_df = pd.DataFrame(bubble_data)
    
    # Create bubble chart
    fig = px.scatter(
        bubble_df,
        x='lab_value',
        y='avg_los',
        size='patient_count',
        hover_data={
            'patient_count': True,
            'readmit_rate': ':.1f',
            'lab_value': ':.2f',
            'avg_los': ':.1f',
            'lab_range': False
        },
        title=f"Laboratory Values vs Length of Stay: {lab_metrics.title()}",
        labels={
            'lab_value': f'{lab_metrics.title()} Level',
            'avg_los': 'Average Length of Stay (days)',
            'patient_count': 'Patient Count'
        },
        color_discrete_sequence=[COLORS['primary']],
        size_max=50
    )
    
    # Customize bubble chart appearance
    fig.update_layout(create_chart_template()['layout'])
    fig.update_layout(height=450, showlegend=False)
    
    fig.update_traces(
        marker=dict(
            opacity=0.7,
            line=dict(width=1, color='white'),
            color=COLORS['primary']
        )
    )
    
    # Add annotation explaining the chart
    fig.add_annotation(
        text="Bubble size = Patient Count",
        xref="paper", yref="paper",
        x=0.02, y=0.98,
        showarrow=False,
        font=dict(size=10, color=COLORS['text_light']),
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor=COLORS['accent'],
        borderwidth=1
    )
    
    st.plotly_chart(fig, use_container_width=True)
    

def create_trend_analysis(df):
    """Create trend analysis with Nordic styling"""
    monthly_stats = df.groupby('month', observed=False).agg({
        'lengthofstay': 'mean',
        'eid': 'count'
    }).reset_index()
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Scatter(
            x=monthly_stats['month'], 
            y=monthly_stats['lengthofstay'],
            name="Avg Length of Stay",
            line=dict(color=COLORS['primary'], width=3),
            mode='lines+markers',
            marker=dict(size=6)
        ),
        secondary_y=False,
    )
    
    fig.add_trace(
        go.Scatter(
            x=monthly_stats['month'], 
            y=monthly_stats['eid'],
            name="Patient Volume",
            line=dict(color=COLORS['success'], width=3),
            mode='lines+markers',
            marker=dict(size=6)
        ),
        secondary_y=True,
    )
    
    fig.update_layout(create_chart_template()['layout'])
    fig.update_layout(
        title="Monthly Trends Analysis",
        height=400,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    fig.update_xaxes(title_text="Month")
    fig.update_yaxes(title_text="Average Length of Stay (days)", secondary_y=False)
    fig.update_yaxes(title_text="Patient Count", secondary_y=True)
    
    st.plotly_chart(fig, use_container_width=True)

def create_detail_table(df):
    """Create detailed patient table"""
    
    # Full patient list
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Create tabs for better organization
    tab1, tab2 = st.tabs(["Full Patient List", "Search & Filter"])
    
    with tab1:
        if not df.empty:
            # Add search functionality at the top
            st.markdown("**Quick Search**")
            search_col1, search_col2, search_col3 = st.columns([2, 1, 1])
            
            with search_col1:
                quick_search = st.text_input(
                    "Search by name or department:", 
                    key="quick_search_full_list",
                    placeholder="Enter patient name or department..."
                )
            
            with search_col2:
                gender_filter = st.selectbox(
                    "Gender:",
                    options=["All", "M", "F"],
                    key="gender_filter_search"
                )
            
            with search_col3:
                clear_search = st.button("Clear All", key="clear_quick_search")
                if clear_search:
                    st.session_state.quick_search_full_list = ""
                    st.session_state.gender_filter_search = "All"
                    st.rerun()
            
            st.markdown("---")
            
            display_cols = ['full_name', 'risk_level', 'age_group', 'vdate', 'gender', 'facid', 'lengthofstay', 'rcount']
            full_list = df[display_cols].copy()
            full_list['vdate'] = full_list['vdate'].dt.strftime('%Y-%m-%d')
            
            # Apply search filters
            search_applied = False
            
            # Text search filter
            if quick_search:
                search_mask = (
                    df['full_name'].str.contains(quick_search, case=False, na=False) |
                    df['facid'].str.contains(quick_search, case=False, na=False)
                )
                filtered_df_indices = df[search_mask].index
                full_list = full_list.loc[filtered_df_indices]
                search_applied = True
            
            # Gender filter
            if gender_filter != "All":
                if search_applied:
                    # Apply gender filter to already filtered data
                    gender_mask = df.loc[full_list.index, 'gender'] == gender_filter
                    full_list = full_list[gender_mask]
                else:
                    # Apply gender filter to all data
                    gender_mask = df['gender'] == gender_filter
                    filtered_df_indices = df[gender_mask].index
                    full_list = full_list.loc[filtered_df_indices]
                search_applied = True
            
            # Rename columns for better display
            full_list = full_list.rename(columns={
                'full_name': 'Patient Name',
                'risk_level': 'Risk Level',
                'age_group': 'Age Group', 
                'vdate': 'Admission Date',
                'gender': 'Gender',
                'facid': 'Department',
                'lengthofstay': 'Length of Stay',
                'rcount': 'Risk Count'
            })
            
            # Sort by admission date (most recent first)
            full_list = full_list.sort_values('Admission Date', ascending=False)
            
            # Show different titles based on search
            if search_applied:
                search_terms = []
                if quick_search:
                    search_terms.append(f"'{quick_search}'")
                if gender_filter != "All":
                    search_terms.append(f"Gender: {gender_filter}")
                
                if search_terms:
                    st.markdown(f"**Search Results** ({len(full_list)} patients matching {' & '.join(search_terms)})")
                else:
                    st.markdown(f"**Filtered Results** ({len(full_list)} patients)")
            else:
                st.markdown(f"**All Patients** ({len(full_list)} patients)")
            
            # Add pagination for better performance
            items_per_page = 20
            total_pages = (len(full_list) - 1) // items_per_page + 1
            
            col_page1, col_page2, col_page3 = st.columns([1, 2, 1])
            with col_page2:
                current_page = st.selectbox("Page", range(1, total_pages + 1), key="full_list_page")
            
            # Ensure current_page is not None
            if current_page is None:
                current_page = 1
                
            start_idx = (current_page - 1) * items_per_page
            end_idx = start_idx + items_per_page
            page_data = full_list.iloc[start_idx:end_idx]
            
            # Column headers
            header_col1, header_col2, header_col3, header_col4, header_col5, header_col6, header_col7, header_col8 = st.columns([2, 1, 1, 1, 1, 1, 1, 1])
            with header_col1:
                st.write("**Patient Name**")
            with header_col2:
                st.write("**Risk Level**")
            with header_col3:
                st.write("**Age Group**")
            with header_col4:
                st.write("**Admission Date**")
            with header_col5:
                st.write("**Gender**")
            with header_col6:
                st.write("**Department**")
            with header_col7:
                st.write("**Length of Stay**")
            with header_col8:
                st.write("**Risk Count**")
            
            st.divider()
            
            # Display patients with clickable names
            for idx, row in page_data.iterrows():
                col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([2, 1, 1, 1, 1, 1, 1, 1])
                
                with col1:
                    # Get original patient ID for this row
                    patient_id = df.loc[idx, 'eid']
                    if st.button(f"▸ {row['Patient Name']}", key=f"full_list_patient_{patient_id}"):
                        st.session_state.current_page = "patient_detail"
                        st.session_state.selected_patient = patient_id
                        st.rerun()
                
                with col2:
                    # Color code the risk level
                    risk_color = "●" if row['Risk Level'] == "High Risk" else "○"
                    st.write(f"{risk_color} {row['Risk Level']}")
                with col3:
                    st.write(row['Age Group'])
                with col4:
                    st.write(row['Admission Date'])
                with col5:
                    st.write(row['Gender'])
                with col6:
                    st.write(row['Department'])
                with col7:
                    st.write(f"{row['Length of Stay']} days")
                with col8:
                    st.write(row['Risk Count'])
        else:
            st.info("No patients found with current filters")
    
    with tab2:
        st.markdown("**Search Patients**")
        search_term = st.text_input("Search by patient name or department:")
        
        if search_term and not df.empty:
            # Filter data based on search term
            search_mask = (
                df['full_name'].str.contains(search_term, case=False, na=False) |
                df['facid'].str.contains(search_term, case=False, na=False)
            )
            search_results = df[search_mask]
            
            if not search_results.empty:
                display_cols = ['full_name', 'risk_level', 'age_group', 'vdate', 'gender', 'facid', 'lengthofstay', 'rcount']
                search_display = search_results[display_cols].copy()
                search_display['vdate'] = search_display['vdate'].dt.strftime('%Y-%m-%d')
                
                search_display = search_display.rename(columns={
                    'full_name': 'Patient Name',
                    'age_group': 'Age Group',
                    'vdate': 'Admission Date', 
                    'gender': 'Gender',
                    'facid': 'Department',
                    'lengthofstay': 'Length of Stay',
                    'rcount': 'Risk Count'
                })
                
                st.markdown(f"**Search Results** ({len(search_display)} patients)")
                
                # Column headers
                header_col1, header_col2, header_col3, header_col4, header_col5, header_col6, header_col7, header_col8 = st.columns([2, 1, 1, 1, 1, 1, 1, 1])
                with header_col1:
                    st.write("**Patient Name**")
                with header_col2:
                    st.write("**Risk Level**")
                with header_col3:
                    st.write("**Age Group**")
                with header_col4:
                    st.write("**Admission Date**")
                with header_col5:
                    st.write("**Gender**")
                with header_col6:
                    st.write("**Department**")
                with header_col7:
                    st.write("**Length of Stay**")
                with header_col8:
                    st.write("**Risk Count**")
                
                st.divider()
                
                # Display search results with clickable names
                for idx, row in search_display.iterrows():
                    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([2, 1, 1, 1, 1, 1, 1, 1])
                    
                    with col1:
                        # Get original patient ID for this row
                        patient_id = search_results.loc[idx, 'eid']
                        if st.button(f"▸ {row['Patient Name']}", key=f"search_patient_{patient_id}"):
                            st.session_state.current_page = "patient_detail"
                            st.session_state.selected_patient = patient_id
                            st.rerun()
                    
                    with col2:
                        # Color code the risk level
                        risk_color = "●" if row['Risk Level'] == "High Risk" else "○"
                        st.write(f"{risk_color} {row['Risk Level']}")
                    with col3:
                        st.write(row['Age Group'])
                    with col4:
                        st.write(row['Admission Date'])
                    with col5:
                        st.write(row['Gender'])
                    with col6:
                        st.write(row['Department'])
                    with col7:
                        st.write(f"{row['Length of Stay']} days")
                    with col8:
                        st.write(row['Risk Count'])
            else:
                st.info(f"No patients found matching '{search_term}'")

def add_floating_agent_chat():
    """Add AI Agent chat widget using ChatKit"""
    # Create a container with the chatbot
    st.markdown("""
    <style>
    .chatbot-iframe-container {
        width: 100%;
        height: 600px;
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        margin: 20px 0;
    }
    </style>
    """, unsafe_allow_html=True)

    # Use components.iframe for cleaner embedding
    components.iframe(
        "https://chatkit.openai.com/embed?workflow_id=wf_68e542103dc481909e41a2e7e9e30d100e4dea407d69250a&version=1",
        height=600,
        scrolling=False
    )

def add_floating_chat():
    """Add floating chat widget to the bottom right corner"""
    # Use components.html to enable position:fixed
    components.html("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
    /* Floating chat button */
    .floating-chat-btn {
        position: fixed;
        bottom: 30px;
        right: 30px;
        width: 60px;
        height: 60px;
        background: linear-gradient(135deg, #2E5266, #4A90A4);
        border-radius: 50%;
        box-shadow: 0 4px 20px rgba(46, 82, 102, 0.3);
        cursor: pointer;
        z-index: 1000;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 24px;
        border: none;
        transition: all 0.3s ease;
    }
    
    .floating-chat-btn:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 30px rgba(46, 82, 102, 0.4);
    }
    
    /* Floating chat window */
    .floating-chat-window {
        position: fixed;
        bottom: 100px;
        right: 30px;
        width: 350px;
        height: 500px;
        background: white;
        border-radius: 15px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
        z-index: 1001;
        display: none;
        flex-direction: column;
        border: 1px solid #E2E8F0;
        overflow: hidden;
    }
    
    .floating-chat-window.visible {
        display: flex;
        animation: slideUp 0.3s ease-out;
    }
    
    @keyframes slideUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .chat-header {
        background: linear-gradient(135deg, #2E5266, #4A90A4);
        color: white;
        padding: 15px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-weight: 600;
    }
    
    .chat-close {
        cursor: pointer;
        font-size: 20px;
        background: none;
        border: none;
        color: white;
        padding: 0;
    }
    
    .chat-messages {
        flex: 1;
        padding: 15px;
        overflow-y: auto;
        background: #F8FAFC;
    }
    
    .chat-input-area {
        padding: 15px;
        border-top: 1px solid #E2E8F0;
        background: white;
    }
    
    .message {
        margin-bottom: 12px;
        padding: 8px 12px;
        border-radius: 18px;
        max-width: 80%;
        word-wrap: break-word;
    }
    
    .user-message {
        background: #2E5266;
        color: white;
        margin-left: auto;
    }
    
    .bot-message {
        background: white;
        border: 1px solid #E2E8F0;
    }

    @keyframes pulse {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.1); opacity: 0.8; }
    }
    </style>
    </head>
    <body>
    <div id="floating-chat-btn" class="floating-chat-btn" onclick="toggleFloatingChat()">
        💬
    </div>
    
    <div id="floating-chat-window" class="floating-chat-window">
        <div class="chat-header">
            <span>Healthcare AI Assistant</span>
            <button class="chat-close" onclick="toggleFloatingChat()">✕</button>
        </div>
        <div class="chat-messages" id="chat-messages">
            <div class="message bot-message">
                Hello! I'm your healthcare AI assistant. I can help you analyze patient data, explain medical indicators, and provide insights about the dashboard. What would you like to know?
            </div>
        </div>
        <div class="chat-input-area">
            <input type="text" 
                   id="chat-input" 
                   placeholder="Ask about patient data, medical terms..."
                   style="width: 100%; padding: 10px; border: 1px solid #E2E8F0; border-radius: 20px; outline: none;">
        </div>
    </div>
    
    <script>
    // Chat history management with localStorage
    const CHAT_STORAGE_KEY = 'healthcare_chat_history';

    function loadChatHistory() {
        try {
            const history = localStorage.getItem(CHAT_STORAGE_KEY);
            return history ? JSON.parse(history) : [];
        } catch (e) {
            console.error('Error loading chat history:', e);
            return [];
        }
    }

    function saveChatHistory(messages) {
        try {
            localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(messages));
        } catch (e) {
            console.error('Error saving chat history:', e);
        }
    }

    function clearChatHistory() {
        localStorage.removeItem(CHAT_STORAGE_KEY);
        location.reload();
    }

    function toggleFloatingChat() {
        const chatWindow = document.getElementById('floating-chat-window');
        chatWindow.classList.toggle('visible');
    }

    // Initialize chat on page load
    document.addEventListener('DOMContentLoaded', function() {
        const chatInput = document.getElementById('chat-input');
        const chatMessages = document.getElementById('chat-messages');

        // Load and display chat history
        const history = loadChatHistory();
        if (history.length > 0) {
            // Clear initial welcome message
            chatMessages.innerHTML = '';
            // Render all messages from history
            history.forEach(msg => {
                const msgDiv = document.createElement('div');
                msgDiv.className = 'message ' + (msg.role === 'user' ? 'user-message' : 'bot-message');
                msgDiv.textContent = msg.content;
                chatMessages.appendChild(msgDiv);
            });
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        // Handle Enter key
        if (chatInput) {
            chatInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter' && this.value.trim()) {
                    sendFloatingMessage(this.value.trim());
                    this.value = '';
                }
            });
        }
    });

    function sendFloatingMessage(message) {
        const chatMessages = document.getElementById('chat-messages');
        const history = loadChatHistory();

        // Add user message to DOM
        const userMsg = document.createElement('div');
        userMsg.className = 'message user-message';
        userMsg.textContent = message;
        chatMessages.appendChild(userMsg);

        // Save user message to history
        history.push({ role: 'user', content: message });
        saveChatHistory(history);

        // Add loading indicator
        const loadingMsg = document.createElement('div');
        loadingMsg.className = 'message bot-message';
        loadingMsg.innerHTML = '💭 Thinking...';
        loadingMsg.id = 'loading-msg';
        chatMessages.appendChild(loadingMsg);

        chatMessages.scrollTop = chatMessages.scrollHeight;

        // Simulate API response
        setTimeout(() => {
            const loading = document.getElementById('loading-msg');
            if (loading) {
                const response = generateFloatingResponse(message);
                loading.innerHTML = response;
                loading.removeAttribute('id');

                // Save bot response to history
                history.push({ role: 'assistant', content: response });
                saveChatHistory(history);

                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        }, 1000);
    }

    function generateFloatingResponse(userMessage) {
        const message = userMessage.toLowerCase();

        if (message.includes('clear') || message.includes('reset')) {
            clearChatHistory();
            return 'Chat history cleared! Reloading...';
        } else if (message.includes('risk') || message.includes('high risk')) {
            return 'High-risk patients are those with length of stay > 90th percentile or readmission flags. You can filter them using the Risk Level filter in the sidebar.';
        } else if (message.includes('creatinine')) {
            return 'Creatinine levels indicate kidney function. Higher levels may suggest kidney problems. Normal range is typically 0.6-1.2 mg/dL.';
        } else if (message.includes('glucose') || message.includes('blood sugar')) {
            return 'Glucose levels show blood sugar control. High levels may indicate diabetes risk. Normal fasting range is 70-100 mg/dL.';
        } else if (message.includes('hematocrit') || message.includes('hct')) {
            return 'Hematocrit measures red blood cell volume. Low levels may indicate anemia. Normal range: 38-46% (female), 42-54% (male).';
        } else if (message.includes('length') || message.includes('stay') || message.includes('los')) {
            return 'Length of stay (LOS) is a key metric. Longer stays often indicate complex cases or complications. Average LOS varies by department and condition severity.';
        } else if (message.includes('readmit') || message.includes('readmission')) {
            return 'Readmission rate tracks patients returning within 30 days. High rates may indicate care quality issues or patient compliance problems.';
        } else if (message.includes('department') || message.includes('dept')) {
            return 'Different departments show varying patient patterns. You can filter by department in the sidebar to analyze specific units.';
        } else if (message.includes('dashboard') || message.includes('help') || message.includes('how')) {
            return 'This dashboard shows patient analytics, KPIs, and trends. Use sidebar filters for: date range, gender, department, age group, and risk level. Click patient names for detailed records. Type "clear" to reset chat.';
        } else {
            return 'I can help analyze patient data, explain medical metrics, and navigate the dashboard. Try asking about: "high risk patients", "creatinine levels", "length of stay", "readmission rates", or type "help" for more info.';
        }
    }
    </script>
    </body>
    </html>
    """, height=0, scrolling=False)

def add_patient_chat(patient):
    """Add patient-specific floating chat widget"""
    # Get patient notes
    patient_id = patient['eid']
    patient_notes = get_patient_notes(patient_id)
    notes_section = f"\n\n    Additional Notes:\n    {patient_notes}" if patient_notes else ""

    # Build patient context for the chatbot
    patient_context = f"""
    Patient: {patient['full_name']}
    Age: {patient['age_at_admission']} years ({patient['age_group']})
    Gender: {'Male' if patient['gender'] == 'M' else 'Female'}
    Department: {patient['facid']}
    Length of Stay: {patient['lengthofstay']} days
    Admission Date: {patient['vdate']}
    Discharge Date: {patient['discharged']}

    Lab Results:
    - Glucose: {patient['glucose']:.1f} mg/dL
    - Creatinine: {patient['creatinine']:.2f} mg/dL
    - Hematocrit: {patient['hematocrit']:.1f}%
    - Sodium: {patient['sodium']:.1f} mEq/L
    - Blood Urea Nitrogen: {patient['bloodureanitro']:.1f} mg/dL

    Risk Status: {patient['risk_level']}
    Readmission Flag: {'Yes' if patient['readmit_flag'] == 1 else 'No'}{notes_section}
    """

    # Encode patient context as base64 to pass to JavaScript
    import base64
    import json
    patient_data = {
        'name': patient['full_name'],
        'age': int(patient['age_at_admission']),
        'gender': 'Male' if patient['gender'] == 'M' else 'Female',
        'department': patient['facid'],
        'los': int(patient['lengthofstay']),
        'glucose': float(patient['glucose']),
        'creatinine': float(patient['creatinine']),
        'hematocrit': float(patient['hematocrit']),
        'sodium': float(patient['sodium']),
        'bun': float(patient['bloodureanitro']),
        'risk': patient['risk_level'],
        'readmit': 'Yes' if patient['readmit_flag'] == 1 else 'No'
    }

    patient_json = json.dumps(patient_data)

    # Get API key from session state or environment variable
    api_key = ""
    if 'openai_api_key' in st.session_state and st.session_state.openai_api_key:
        api_key = st.session_state.openai_api_key
    else:
        api_key = os.getenv("OPENAI_API_KEY", "")

    # Check if API key is available for voice features
    voice_enabled = bool(api_key)

    components.html(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
    /* Floating chat button */
    .floating-chat-btn {{
        position: fixed;
        bottom: 30px;
        right: 30px;
        width: 60px;
        height: 60px;
        background: linear-gradient(135deg, #2E5266, #4A90A4);
        border-radius: 50%;
        box-shadow: 0 4px 20px rgba(46, 82, 102, 0.3);
        cursor: pointer;
        z-index: 1000;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 24px;
        border: none;
        transition: all 0.3s ease;
    }}

    .floating-chat-btn:hover {{
        transform: scale(1.1);
        box-shadow: 0 6px 30px rgba(46, 82, 102, 0.4);
    }}

    /* Floating chat window */
    .floating-chat-window {{
        position: fixed;
        bottom: 100px;
        right: 30px;
        width: 350px;
        height: 500px;
        background: white;
        border-radius: 15px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
        z-index: 1001;
        display: none;
        flex-direction: column;
        border: 1px solid #E2E8F0;
        overflow: hidden;
    }}

    .floating-chat-window.visible {{
        display: flex;
        animation: slideUp 0.3s ease-out;
    }}

    @keyframes slideUp {{
        from {{
            opacity: 0;
            transform: translateY(20px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}

    .chat-header {{
        background: linear-gradient(135deg, #2E5266, #4A90A4);
        color: white;
        padding: 15px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-weight: 600;
    }}

    .chat-close {{
        cursor: pointer;
        font-size: 20px;
        background: none;
        border: none;
        color: white;
        padding: 0;
    }}

    .chat-messages {{
        flex: 1;
        padding: 15px;
        overflow-y: auto;
        background: #F8FAFC;
    }}

    .chat-input-area {{
        padding: 15px;
        border-top: 1px solid #E2E8F0;
        background: white;
    }}

    .message {{
        margin-bottom: 12px;
        padding: 8px 12px;
        border-radius: 18px;
        max-width: 80%;
        word-wrap: break-word;
    }}

    .user-message {{
        background: #2E5266;
        color: white;
        margin-left: auto;
    }}

    .bot-message {{
        background: white;
        border: 1px solid #E2E8F0;
    }}

    .file-attachment {{
        background: #E0F2FE;
        border: 1px solid #BAE6FD;
        border-radius: 8px;
        padding: 8px 12px;
        margin-bottom: 10px;
        font-size: 13px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }}

    .file-info {{
        flex: 1;
    }}

    .file-remove {{
        cursor: pointer;
        padding: 2px 6px;
        border-radius: 4px;
        background: #FEE2E2;
        border: none;
        font-size: 12px;
        transition: all 0.2s;
    }}

    .file-remove:hover {{
        background: #FECACA;
    }}
    </style>
    </head>
    <body>
    <div id="floating-chat-btn" class="floating-chat-btn" onclick="toggleFloatingChat()">
        💬
    </div>

    <div id="floating-chat-window" class="floating-chat-window">
        <div class="chat-header">
            <span>Patient AI Assistant</span>
            <button class="chat-close" onclick="toggleFloatingChat()">✕</button>
        </div>
        <div class="chat-messages" id="chat-messages">
            <div class="message bot-message">
                Hello! I'm analyzing {patient['full_name']}'s medical record. Ask me anything about this patient's condition, lab results, or care recommendations.
            </div>
        </div>
        <div class="chat-input-area" style="position: relative;">
            <input type="text"
                   id="chat-input"
                   placeholder="Ask about patient data, medical terms..."
                   style="width: 100%; padding: 12px 85px 12px 45px; border: 1px solid #E2E8F0; border-radius: 25px; outline: none; font-size: 14px; box-sizing: border-box;">
            <!-- Hidden file input -->
            <input type="file"
                   id="fileInput"
                   accept=".pdf,.jpg,.jpeg,.png,.txt,.doc,.docx,.csv"
                   style="display: none;"
                   onchange="handleFileSelect(event)">
            <!-- File attachment button -->
            <button id="attachBtn" onclick="document.getElementById('fileInput').click()"
                    style="position: absolute; left: 15px; top: 50%; transform: translateY(-50%); background: none; border: none; font-size: 20px; cursor: pointer; padding: 5px; opacity: 0.6; transition: all 0.3s ease;"
                    onmouseover="this.style.opacity='1'"
                    onmouseout="this.style.opacity='0.6'"
                    title="Attach file">
                📎
            </button>
            <!-- Voice button -->
            <button id="voiceBtn" onclick="toggleVoiceInput()"
                    style="position: absolute; right: 15px; top: 50%; transform: translateY(-50%); background: none; border: none; font-size: 20px; cursor: pointer; padding: 5px; opacity: 0.6; transition: all 0.3s ease;"
                    onmouseover="this.style.opacity='1'"
                    onmouseout="if(!this.classList.contains('recording')) this.style.opacity='0.6'"
                    title="Voice input (click to speak)">
                🎤
            </button>
        </div>
    </div>

    <script>
    // Patient data
    const patientData = {patient_json};

    // Chat history management with localStorage
    const CHAT_STORAGE_KEY = 'patient_chat_' + patientData.name.replace(/\\s+/g, '_');

    function loadChatHistory() {{
        try {{
            const history = localStorage.getItem(CHAT_STORAGE_KEY);
            return history ? JSON.parse(history) : [];
        }} catch (e) {{
            console.error('Error loading chat history:', e);
            return [];
        }}
    }}

    function saveChatHistory(messages) {{
        try {{
            localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(messages));
        }} catch (e) {{
            console.error('Error saving chat history:', e);
        }}
    }}

    function clearChatHistory() {{
        localStorage.removeItem(CHAT_STORAGE_KEY);
        location.reload();
    }}

    // File attachment management with localStorage
    const FILE_STORAGE_KEY = 'patient_file_' + patientData.name.replace(/\\s+/g, '_');

    function loadAttachedFile() {{
        try {{
            const file = localStorage.getItem(FILE_STORAGE_KEY);
            return file ? JSON.parse(file) : null;
        }} catch (e) {{
            console.error('Error loading attached file:', e);
            return null;
        }}
    }}

    function saveAttachedFile(fileData) {{
        try {{
            localStorage.setItem(FILE_STORAGE_KEY, JSON.stringify(fileData));
        }} catch (e) {{
            console.error('Error saving attached file:', e);
        }}
    }}

    function removeAttachedFile() {{
        localStorage.removeItem(FILE_STORAGE_KEY);
        displayAttachedFile();
    }}

    function handleFileSelect(event) {{
        const file = event.target.files[0];
        if (!file) return;

        // Read file content
        const reader = new FileReader();

        reader.onload = function(e) {{
            const content = e.target.result;

            // Store file info
            const fileData = {{
                name: file.name,
                type: file.type,
                size: file.size,
                content: content.substring(0, 2000), // Store first 2000 chars
                timestamp: new Date().toISOString()
            }};

            saveAttachedFile(fileData);
            displayAttachedFile();

            // Show confirmation in chat
            const chatMessages = document.getElementById('chat-messages');
            const fileMsg = document.createElement('div');
            fileMsg.className = 'message bot-message';
            fileMsg.innerHTML = `📎 File attached: <strong>${{file.name}}</strong> (${{(file.size / 1024).toFixed(1)}} KB)`;
            chatMessages.appendChild(fileMsg);
            chatMessages.scrollTop = chatMessages.scrollHeight;

            // Save to history
            const history = loadChatHistory();
            history.push({{ role: 'system', content: `File attached: ${{file.name}}` }});
            saveChatHistory(history);
        }};

        reader.readAsText(file);

        // Reset file input
        event.target.value = '';
    }}

    function displayAttachedFile() {{
        const fileData = loadAttachedFile();
        const chatMessages = document.getElementById('chat-messages');

        // Remove any existing file display
        const existingDisplay = document.getElementById('file-display');
        if (existingDisplay) {{
            existingDisplay.remove();
        }}

        if (fileData) {{
            // Create file display element
            const fileDisplay = document.createElement('div');
            fileDisplay.id = 'file-display';
            fileDisplay.className = 'file-attachment';
            fileDisplay.innerHTML = `
                <div class="file-info">
                    <strong>📎 ${{fileData.name}}</strong><br>
                    <span style="font-size: 11px; color: #64748B;">
                        ${{(fileData.size / 1024).toFixed(1)}} KB • ${{fileData.type || 'Unknown type'}}
                    </span>
                </div>
                <button class="file-remove" onclick="removeAttachedFile()">🗑️</button>
            `;

            // Insert at the beginning of chat messages
            chatMessages.insertBefore(fileDisplay, chatMessages.firstChild);
        }}
    }}

    function toggleFloatingChat() {{
        const chatWindow = document.getElementById('floating-chat-window');
        chatWindow.classList.toggle('visible');

        // Display attached file when chat opens
        if (chatWindow.classList.contains('visible')) {{
            displayAttachedFile();
        }}
    }}

    // Initialize chat on page load
    document.addEventListener('DOMContentLoaded', function() {{
        const chatInput = document.getElementById('chat-input');
        const chatMessages = document.getElementById('chat-messages');

        // Load and display chat history
        const history = loadChatHistory();
        if (history.length > 0) {{
            // Clear initial welcome message
            chatMessages.innerHTML = '';
            // Render all messages from history
            history.forEach(msg => {{
                const msgDiv = document.createElement('div');
                msgDiv.className = 'message ' + (msg.role === 'user' ? 'user-message' : 'bot-message');
                msgDiv.textContent = msg.content;
                chatMessages.appendChild(msgDiv);
            }});
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }}

        // Handle Enter key
        if (chatInput) {{
            chatInput.addEventListener('keypress', function(e) {{
                if (e.key === 'Enter' && this.value.trim()) {{
                    sendFloatingMessage(this.value.trim());
                    this.value = '';
                }}
            }});
        }}
    }});

    function sendFloatingMessage(message) {{
        const chatMessages = document.getElementById('chat-messages');
        const history = loadChatHistory();

        // Add user message to DOM
        const userMsg = document.createElement('div');
        userMsg.className = 'message user-message';
        userMsg.textContent = message;
        chatMessages.appendChild(userMsg);

        // Save user message to history
        history.push({{ role: 'user', content: message }});
        saveChatHistory(history);

        // Add loading indicator
        const loadingMsg = document.createElement('div');
        loadingMsg.className = 'message bot-message';
        loadingMsg.innerHTML = '💭 Analyzing patient data...';
        loadingMsg.id = 'loading-msg';
        chatMessages.appendChild(loadingMsg);

        chatMessages.scrollTop = chatMessages.scrollHeight;

        // Generate response
        setTimeout(() => {{
            const loading = document.getElementById('loading-msg');
            if (loading) {{
                const response = generatePatientResponse(message);
                loading.innerHTML = response;
                loading.removeAttribute('id');

                // Save bot response to history
                history.push({{ role: 'assistant', content: response }});
                saveChatHistory(history);

                chatMessages.scrollTop = chatMessages.scrollHeight;
            }}
        }}, 1000);
    }}

    // Generate concise voice response (key points only, no redundant numbers)
    function generateVoiceResponse(userMessage) {{
        const msg = userMessage.toLowerCase();
        const p = patientData;

        if (msg.includes('file') || msg.includes('attach') || msg.includes('upload') || msg.includes('document')) {{
            return `File attachment feature is available. Click the paperclip button to attach documents.`;
        }}

        if (msg.includes('clear') || msg.includes('reset')) {{
            return 'Clearing chat history';
        }} else if (msg.includes('name') || msg.includes('who')) {{
            return `This is ${{p.name}}, a ${{p.age}} year old ${{p.gender}} patient in ${{p.department}} department.`;
        }} else if (msg.includes('age')) {{
            return `Patient is ${{p.age}} years old.`;
        }} else if (msg.includes('glucose') || msg.includes('sugar') || msg.includes('blood sugar')) {{
            if (p.glucose > 140) return 'Glucose is elevated. This may indicate diabetes risk. Recommend close monitoring.';
            if (p.glucose < 70) return 'Glucose is low. Hypoglycemia concern. Immediate attention needed.';
            return 'Glucose level is within normal range.';
        }} else if (msg.includes('creatinine') || msg.includes('kidney')) {{
            if (p.creatinine > 1.2) return 'Creatinine is elevated, indicating potential kidney dysfunction. Recommend nephrology consultation.';
            return 'Creatinine level is normal. Kidney function appears healthy.';
        }} else if (msg.includes('hematocrit') || msg.includes('hct') || msg.includes('blood count')) {{
            if (p.hematocrit < 38) return 'Hematocrit is low. Possible anemia. Recommend further investigation.';
            if (p.hematocrit > 50) return 'Hematocrit is high. May indicate dehydration or polycythemia.';
            return 'Hematocrit is within normal range.';
        }} else if (msg.includes('sodium') || msg.includes('na')) {{
            if (p.sodium < 135) return 'Sodium is low. Hyponatremia detected. Monitor electrolyte balance.';
            if (p.sodium > 145) return 'Sodium is high. Hypernatremia detected. Check hydration status.';
            return 'Sodium level is normal.';
        }} else if (msg.includes('bun') || msg.includes('urea')) {{
            if (p.bun > 20) return 'BUN is elevated. Check kidney function and hydration.';
            return 'BUN is within normal range.';
        }} else if (msg.includes('lab') || msg.includes('test') || msg.includes('result')) {{
            let concerns = [];
            if (p.glucose > 140 || p.glucose < 70) concerns.push('glucose');
            if (p.creatinine > 1.2) concerns.push('creatinine');
            if (p.hematocrit < 38 || p.hematocrit > 50) concerns.push('hematocrit');
            if (p.sodium < 135 || p.sodium > 145) concerns.push('sodium');
            if (p.bun > 20) concerns.push('BUN');

            if (concerns.length > 0) {{
                return `I see ${{concerns.length}} value${{concerns.length > 1 ? 's' : ''}} that need attention: ${{concerns.join(', ')}}. Ask about specific tests for details.`;
            }} else {{
                return 'All lab results are within normal ranges.';
            }}
        }} else if (msg.includes('risk') || msg.includes('危险')) {{
            if (p.risk === 'High Risk') {{
                return 'This is a high risk patient. Close monitoring is required.';
            }} else {{
                return 'Patient has standard risk level.';
            }}
        }} else if (msg.includes('readmit') || msg.includes('return')) {{
            if (p.readmit === 'Yes') {{
                return 'Patient has previous readmissions. Enhanced discharge planning recommended.';
            }} else {{
                return 'No previous readmissions on record.';
            }}
        }} else if (msg.includes('stay') || msg.includes('los') || msg.includes('length')) {{
            if (p.los > 7) return `Extended stay of ${{p.los}} days. Monitor for complications.`;
            if (p.los > 3) return `Moderate stay of ${{p.los}} days in ${{p.department}}.`;
            return `Short stay of ${{p.los}} days.`;
        }} else if (msg.includes('department') || msg.includes('where')) {{
            return `Patient is in ${{p.department}} department.`;
        }} else if (msg.includes('recommend') || msg.includes('suggest') || msg.includes('care')) {{
            let recommendations = [];
            if (p.glucose > 140) recommendations.push('Monitor blood glucose closely');
            if (p.creatinine > 1.2) recommendations.push('Consult nephrology');
            if (p.hematocrit < 38) recommendations.push('Investigate anemia');
            if (p.los > 7) recommendations.push('Review discharge planning');
            if (p.risk === 'High Risk') recommendations.push('Enhanced monitoring');

            if (recommendations.length > 0) {{
                return `I have ${{recommendations.length}} recommendation${{recommendations.length > 1 ? 's' : ''}}: ${{recommendations.join(', ')}}.`;
            }} else {{
                return 'Continue standard care. All indicators are acceptable.';
            }}
        }} else if (msg.includes('summary') || msg.includes('overview')) {{
            let concerns = [];
            if (p.glucose > 140 || p.glucose < 70) concerns.push('abnormal glucose');
            if (p.creatinine > 1.2) concerns.push('elevated creatinine');
            if (p.risk === 'High Risk') concerns.push('high risk status');

            if (concerns.length > 0) {{
                return `${{p.name}}, ${{p.age}} years old, ${{p.gender}}, in ${{p.department}}. Key concerns: ${{concerns.join(', ')}}.`;
            }} else {{
                return `${{p.name}}, ${{p.age}} years old, ${{p.gender}}, in ${{p.department}}. All indicators are stable.`;
            }}
        }} else if (msg.includes('help')) {{
            return 'I can help with patient demographics, lab results, risk assessment, and care recommendations. What would you like to know?';
        }} else {{
            return `I can help you analyze ${{p.name}}'s medical record. Ask about lab results, risk level, or care recommendations.`;
        }}
    }}

    function generatePatientResponse(userMessage) {{
        const msg = userMessage.toLowerCase();
        const p = patientData;
        const attachedFile = loadAttachedFile();

        // Check for file-related queries
        if (msg.includes('file') || msg.includes('attach') || msg.includes('upload') || msg.includes('document')) {{
            if (attachedFile) {{
                return `📎 Attached file: <strong>${{attachedFile.name}}</strong> (${{(attachedFile.size / 1024).toFixed(1)}} KB)<br><br>Preview: ${{attachedFile.content.substring(0, 200)}}...<br><br>I'll reference this file when answering your questions about the patient.`;
            }} else {{
                return `No file is currently attached. Click the 📎 button below to attach medical records, lab results, or other relevant documents.`;
            }}
        }}

        if (msg.includes('clear') || msg.includes('reset')) {{
            clearChatHistory();
            return 'Chat history cleared! Reloading...';
        }} else if (msg.includes('name') || msg.includes('who')) {{
            return `This is ${{p.name}}, a ${{p.age}}-year-old ${{p.gender}} patient currently in ${{p.department}} department.`;
        }} else if (msg.includes('age')) {{
            return `${{p.name}} is ${{p.age}} years old.`;
        }} else if (msg.includes('glucose') || msg.includes('sugar') || msg.includes('blood sugar')) {{
            let assessment = p.glucose > 140 ? '⚠️ ELEVATED - may indicate diabetes risk' :
                           p.glucose < 70 ? '⚠️ LOW - hypoglycemia concern' :
                           '✓ Normal range';
            return `Glucose level: ${{p.glucose}} mg/dL. ${{assessment}}. Normal fasting range is 70-100 mg/dL.`;
        }} else if (msg.includes('creatinine') || msg.includes('kidney')) {{
            let assessment = p.creatinine > 1.2 ? '⚠️ ELEVATED - potential kidney dysfunction' : '✓ Normal range';
            return `Creatinine level: ${{p.creatinine}} mg/dL. ${{assessment}}. Normal range is 0.6-1.2 mg/dL. Higher levels suggest reduced kidney function.`;
        }} else if (msg.includes('hematocrit') || msg.includes('hct') || msg.includes('blood count')) {{
            let assessment = p.hematocrit < 38 ? '⚠️ LOW - possible anemia' :
                           p.hematocrit > 50 ? '⚠️ HIGH - dehydration or polycythemia concern' :
                           '✓ Normal range';
            return `Hematocrit: ${{p.hematocrit}}%. ${{assessment}}. Normal: 38-46% (female), 42-54% (male).`;
        }} else if (msg.includes('sodium') || msg.includes('na')) {{
            let assessment = p.sodium < 135 ? '⚠️ LOW (hyponatremia)' :
                           p.sodium > 145 ? '⚠️ HIGH (hypernatremia)' :
                           '✓ Normal range';
            return `Sodium level: ${{p.sodium}} mEq/L. ${{assessment}}. Normal range is 135-145 mEq/L.`;
        }} else if (msg.includes('bun') || msg.includes('urea')) {{
            let assessment = p.bun > 20 ? '⚠️ ELEVATED - check kidney function' : '✓ Normal range';
            return `Blood Urea Nitrogen (BUN): ${{p.bun}} mg/dL. ${{assessment}}. Normal range is 7-20 mg/dL.`;
        }} else if (msg.includes('lab') || msg.includes('test') || msg.includes('result')) {{
            return `Lab Results Summary:\\n• Glucose: ${{p.glucose}} mg/dL\\n• Creatinine: ${{p.creatinine}} mg/dL\\n• Hematocrit: ${{p.hematocrit}}%\\n• Sodium: ${{p.sodium}} mEq/L\\n• BUN: ${{p.bun}} mg/dL\\n\\nAsk about specific tests for detailed analysis.`;
        }} else if (msg.includes('risk') || msg.includes('危险')) {{
            return `Risk Assessment: ${{p.risk}}. ${{p.risk === 'High Risk' ?
                'This patient requires close monitoring due to elevated risk factors.' :
                'Standard monitoring protocols apply.'}}`;
        }} else if (msg.includes('readmit') || msg.includes('return')) {{
            return `Readmission History: ${{p.readmit}}. ${{p.readmit === 'Yes' ?
                '⚠️ This patient has been readmitted before. Consider enhanced discharge planning.' :
                'No previous readmissions recorded.'}}`;
        }} else if (msg.includes('stay') || msg.includes('los') || msg.includes('length')) {{
            let assessment = p.los > 7 ? '⚠️ Extended stay - monitor for complications' :
                           p.los > 3 ? 'Moderate duration' :
                           'Short stay';
            return `Length of Stay: ${{p.los}} days. ${{assessment}}. Patient is in ${{p.department}} department.`;
        }} else if (msg.includes('department') || msg.includes('where')) {{
            return `${{p.name}} is currently in the ${{p.department}} department with a length of stay of ${{p.los}} days.`;
        }} else if (msg.includes('recommend') || msg.includes('suggest') || msg.includes('care')) {{
            let recommendations = [];
            if (p.glucose > 140) recommendations.push('Monitor blood glucose levels closely');
            if (p.creatinine > 1.2) recommendations.push('Consult nephrology for kidney function assessment');
            if (p.hematocrit < 38) recommendations.push('Investigate potential anemia causes');
            if (p.los > 7) recommendations.push('Review discharge planning and home care needs');
            if (p.risk === 'High Risk') recommendations.push('Implement enhanced monitoring protocols');

            if (recommendations.length > 0) {{
                return 'Care Recommendations:\\n• ' + recommendations.join('\\n• ');
            }} else {{
                return 'Continue standard care protocols. All vital indicators are within acceptable ranges.';
            }}
        }} else if (msg.includes('summary') || msg.includes('overview')) {{
            return `Patient Summary:\\n\\n${{p.name}}, ${{p.age}} yr old ${{p.gender}}\\nDepartment: ${{p.department}}\\nLOS: ${{p.los}} days\\nRisk Level: ${{p.risk}}\\n\\nKey Labs:\\n• Glucose: ${{p.glucose}}\\n• Creatinine: ${{p.creatinine}}\\n• Hematocrit: ${{p.hematocrit}}%\\n\\nType 'recommend' for care suggestions.`;
        }} else if (msg.includes('help')) {{
            const fileNote = attachedFile ? `\\n• Attached files: ${{attachedFile.name}}` : '\\n• Attach files (click 📎 to add documents)';
            return `I can help you with:\\n• Patient demographics (name, age, gender)\\n• Lab results (glucose, creatinine, hematocrit, sodium, BUN)\\n• Risk assessment\\n• Length of stay analysis\\n• Care recommendations\\n• Overall summary${{fileNote}}\\n\\nTry: "What are the lab results?" or "Any care recommendations?"`;
        }} else {{
            const fileHint = attachedFile ? `\\n\\n📎 I also have access to the attached file: ${{attachedFile.name}}` : '';
            return `I can answer questions about ${{p.name}}'s medical record. Try asking about:\\n• Lab results (glucose, creatinine, etc.)\\n• Risk level and readmission history\\n• Care recommendations\\n• Length of stay${{fileHint}}\\n\\nType "help" for more options or "summary" for an overview.`;
        }}
    }}

    // ========== Web Speech API Voice Input ==========
    let recognition = null;
    let isListening = false;
    let speechSynthesis = window.speechSynthesis;

    // Initialize Web Speech API
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {{
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';

        recognition.onstart = () => {{
            isListening = true;
            const btn = document.getElementById('voiceBtn');
            btn.classList.add('recording');
            btn.style.opacity = '1';
            btn.style.background = 'linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%)';
            btn.style.borderRadius = '50%';
            btn.style.padding = '8px';
            btn.style.animation = 'pulse 1.5s ease-in-out infinite';
        }};

        recognition.onresult = (event) => {{
            const transcript = event.results[0][0].transcript;
            const chatInput = document.getElementById('chat-input');
            chatInput.value = transcript;

            // Automatically send the message
            setTimeout(() => {{
                sendFloatingMessage(transcript);
                chatInput.value = '';
            }}, 500);
        }};

        recognition.onerror = (event) => {{
            console.error('Speech recognition error:', event.error);
            stopListening();

            if (event.error === 'not-allowed') {{
                alert('Microphone access denied. Please allow microphone permission in your browser settings.');
            }} else if (event.error === 'no-speech') {{
                alert('No speech detected. Please try again.');
            }}
        }};

        recognition.onend = () => {{
            stopListening();
        }};
    }} else {{
        // Disable voice button if not supported
        document.getElementById('voiceBtn').style.opacity = '0.3';
        document.getElementById('voiceBtn').style.cursor = 'not-allowed';
        document.getElementById('voiceBtn').title = 'Voice input not supported in this browser (use Chrome/Edge)';
    }}

    function toggleVoiceInput() {{
        if (!recognition) {{
            alert('Voice input is not supported in your browser. Please use Chrome or Edge.');
            return;
        }}

        if (isListening) {{
            recognition.stop();
        }} else {{
            try {{
                recognition.start();
            }} catch (error) {{
                console.error('Failed to start recognition:', error);
                alert('Failed to start voice input. Please try again.');
            }}
        }}
    }}

    function stopListening() {{
        isListening = false;
        const btn = document.getElementById('voiceBtn');
        btn.classList.remove('recording');
        btn.style.opacity = '0.6';
        btn.style.background = 'none';
        btn.style.padding = '5px';
        btn.style.animation = 'none';
    }}

    // OpenAI API Key
    const API_KEY = "{api_key}";

    // Clean text for speech (remove emojis, format medical terms)
    function cleanTextForSpeech(text) {{
        return text
            .replace(/⚠️/g, 'Warning:')
            .replace(/✓/g, 'Normal.')
            .replace(/•/g, '')
            .replace(/\\n/g, '. ')
            .replace(/:/g, ',')
            .replace(/mg\\/dL/g, 'milligrams per deciliter')
            .replace(/mEq\\/L/g, 'milliequivalents per liter')
            .replace(/%/g, ' percent')
            .replace(/\(/g, ', ')
            .replace(/\)/g, '')
            .replace(/\s+/g, ' ')
            .trim();
    }}

    // Speak using OpenAI TTS API (more natural voice)
    async function speakWithOpenAI(text) {{
        if (!API_KEY || API_KEY === '') {{
            console.log('No API key, falling back to browser speech');
            speakWithBrowser(text);
            return;
        }}

        try {{
            const cleanText = cleanTextForSpeech(text);

            const response = await fetch('https://api.openai.com/v1/audio/speech', {{
                method: 'POST',
                headers: {{
                    'Authorization': `Bearer ${{API_KEY}}`,
                    'Content-Type': 'application/json'
                }},
                body: JSON.stringify({{
                    model: 'tts-1',     // Faster TTS model (tts-1 is 2x faster than tts-1-hd)
                    voice: 'nova',      // nova is warm and friendly for medical context
                    input: cleanText,
                    speed: 1.0
                }})
            }});

            if (!response.ok) {{
                throw new Error('TTS API failed');
            }}

            const audioBlob = await response.blob();
            const audioUrl = URL.createObjectURL(audioBlob);
            const audio = new Audio(audioUrl);

            audio.onended = () => {{
                URL.revokeObjectURL(audioUrl);
            }};

            audio.play();
        }} catch (error) {{
            console.error('OpenAI TTS error:', error);
            speakWithBrowser(text);
        }}
    }}

    // Fallback: Speak using browser's built-in speech synthesis
    function speakWithBrowser(text) {{
        if (speechSynthesis) {{
            speechSynthesis.cancel();

            const cleanText = cleanTextForSpeech(text);
            const utterance = new SpeechSynthesisUtterance(cleanText);
            utterance.lang = 'en-US';
            utterance.rate = 1.0;
            utterance.pitch = 1.0;
            utterance.volume = 1.0;

            const voices = speechSynthesis.getVoices();
            const preferredVoice = voices.find(voice =>
                voice.name.includes('Samantha') ||
                voice.name.includes('Google US English') ||
                voice.name.includes('Microsoft Zira')
            );

            if (preferredVoice) {{
                utterance.voice = preferredVoice;
            }}

            speechSynthesis.speak(utterance);
        }}
    }}

    // Main speech function - use OpenAI TTS for natural voice
    function speakResponse(text) {{
        speakWithOpenAI(text);
    }}

    // Get intelligent response using OpenAI GPT
    async function getGPTResponse(userMessage) {{
        if (!API_KEY || API_KEY === '') {{
            return generatePatientResponse(userMessage);
        }}

        try {{
            const response = await fetch('https://api.openai.com/v1/chat/completions', {{
                method: 'POST',
                headers: {{
                    'Authorization': `Bearer ${{API_KEY}}`,
                    'Content-Type': 'application/json'
                }},
                body: JSON.stringify({{
                    model: 'gpt-4o',
                    messages: [
                        {{
                            role: 'system',
                            content: `You are an experienced hospital administrator with deep clinical knowledge. Patient: ${{patientData.name}}, ${{patientData.age}}yo ${{patientData.gender}}, ${{patientData.department}}, LOS: ${{patientData.los}} days, Risk: ${{patientData.risk}}, Readmission: ${{patientData.readmit}}

Labs: Glucose ${{patientData.glucose}}, Creatinine ${{patientData.creatinine}}, Hematocrit ${{patientData.hematocrit}}%, Sodium ${{patientData.sodium}}, BUN ${{patientData.bun}}

Communicate like a seasoned healthcare manager:
- Focus on what matters clinically - abnormal findings and actionable recommendations
- Skip mentioning normal values unless specifically asked
- Don't repeat numbers already visible on screen
- Be concise but professional - get to the point
- Provide context and clinical judgment when relevant

Good example: "Elevated glucose and critically low hematocrit are the main concerns here. The glucose suggests diabetes risk and needs monitoring. The hematocrit at 12% is severe anemia requiring immediate workup and possible transfusion."

Bad example: "Carol Thomas, a 64-year-old female, has been in the hospital for 3 days... glucose at 160.6 mg/dL... creatinine level is 1.16 mg/dL which is within normal range..."`
                        }},
                        {{ role: 'user', content: userMessage }}
                    ],
                    temperature: 0.7,
                    max_tokens: 150
                }})
            }});

            if (!response.ok) {{
                throw new Error('GPT API failed');
            }}

            const data = await response.json();
            return data.choices[0].message.content;
        }} catch (error) {{
            console.error('GPT API error:', error);
            return generatePatientResponse(userMessage);
        }}
    }}

    // Override sendFloatingMessage to add GPT and voice response
    const originalSendMessage = sendFloatingMessage;
    sendFloatingMessage = async function(message) {{
        const chatMessages = document.getElementById('chat-messages');
        const history = loadChatHistory();

        // Add user message to DOM
        const userMsg = document.createElement('div');
        userMsg.className = 'message user-message';
        userMsg.textContent = message;
        chatMessages.appendChild(userMsg);

        // Save user message to history
        history.push({{ role: 'user', content: message }});
        saveChatHistory(history);

        // Add loading indicator
        const loadingMsg = document.createElement('div');
        loadingMsg.className = 'message bot-message';
        loadingMsg.innerHTML = '💭 Analyzing patient data...';
        loadingMsg.id = 'loading-msg';
        chatMessages.appendChild(loadingMsg);

        chatMessages.scrollTop = chatMessages.scrollHeight;

        // Get concise response from GPT (same for screen and voice)
        const response = await getGPTResponse(message);

        const loading = document.getElementById('loading-msg');
        if (loading) {{
            loading.innerHTML = response;
            loading.removeAttribute('id');

            // Save bot response to history
            history.push({{ role: 'assistant', content: response }});
            saveChatHistory(history);

            chatMessages.scrollTop = chatMessages.scrollHeight;

            // Speak the same concise response
            speakResponse(response);
        }}
    }};
    </script>
    </body>
    </html>
    """, height=0, scrolling=False)

@st.cache_data(ttl=300)  # Cache responses for 5 minutes
def get_chatgpt_response(user_message, context=""):
    """Get response from ChatGPT API"""
    try:
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        system_prompt = """You are a helpful AI assistant specialized in healthcare analytics and data interpretation. 
        You are integrated into a hospital management dashboard that shows:
        - Patient length of stay data
        - Laboratory test results (creatinine, glucose, hematocrit, etc.)
        - Readmission rates
        - Department performance metrics
        - Disease condition impacts on hospital stays
        
        Provide clear, accurate, and professional responses about healthcare data analysis, medical insights, 
        and dashboard interpretation. Keep responses concise but informative. If you're unsure about medical 
        specifics, acknowledge limitations and suggest consulting healthcare professionals."""
        
        if context:
            system_prompt += f"\n\nCurrent dashboard context: {context}"
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=300,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"I apologize, but I'm having trouble connecting to my AI service right now. Error: {str(e)[:100]}... Please try again later or contact support if the issue persists."

def add_chat_widget_DISABLED():
    """Add floating chat widget with ChatGPT integration"""
    
    # Initialize chat messages in session state
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {"role": "assistant", "content": "Hi! I'm your AI assistant for healthcare analytics. Ask me about the dashboard data, medical insights, or any questions you have!"}
        ]
    
    # Force reset floating chat visibility to ensure it starts hidden
    st.session_state.float_chat_visible = False
    
    if "chat_visible" not in st.session_state:
        st.session_state.chat_visible = False
    
    # Handle new messages
    if "pending_message" in st.session_state and st.session_state.pending_message:
        user_message = st.session_state.pending_message
        st.session_state.pending_message = ""
        
        # Add user message
        st.session_state.chat_messages.append({"role": "user", "content": user_message})
        
        # Get ChatGPT response
        with st.spinner("AI Assistant is thinking..."):
            ai_response = get_chatgpt_response(user_message)
            st.session_state.chat_messages.append({"role": "assistant", "content": ai_response})
        
        # Force rerun to update the chat
        st.rerun()
    
    # Create a sidebar for chat functionality
    with st.sidebar:
        st.markdown("---")
        
        # Chat toggle button
        if st.button("▸ AI Assistant", use_container_width=True, help="Chat with AI about the dashboard data"):
            st.session_state.chat_visible = not st.session_state.chat_visible
        
        # Show chat interface if visible
        if st.session_state.chat_visible:
            st.markdown("### AI Healthcare Assistant")
            
            # Display chat messages
            chat_container = st.container()
            with chat_container:
                # Display chat history in a scrollable area
                for i, message in enumerate(st.session_state.chat_messages):
                    if message["role"] == "user":
                        st.markdown(f"""
                        <div style="background-color: #2E5266; color: white; padding: 0.75rem; border-radius: 0.75rem; margin: 0.5rem 0; margin-left: 2rem;">
                            {message["content"]}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style="background-color: #F1F5F9; color: #2D3748; padding: 0.75rem; border-radius: 0.75rem; margin: 0.5rem 0; margin-right: 2rem;">
                            {message["content"]}
                        </div>
                        """, unsafe_allow_html=True)
            
            # Chat input
            user_input = st.text_area(
                "Ask me anything about the healthcare data:",
                key="sidebar_chat_input",
                height=80,
                placeholder="E.g., 'What do the creatinine levels tell us about patient outcomes?'"
            )
            
            # Send button
            col1, col2 = st.columns([2, 1])
            with col1:
                if st.button("Send", key="sidebar_send_message", use_container_width=True, type="primary"):
                    if user_input and user_input.strip():
                        st.session_state.pending_message = user_input.strip()
                        st.rerun()
            
            with col2:
                if st.button("Clear", key="sidebar_clear_chat", use_container_width=True):
                    st.session_state.chat_messages = [
                        {"role": "assistant", "content": "Hi! I'm your AI assistant for healthcare analytics. Ask me about the dashboard data, medical insights, or any questions you have!"}
                    ]
                    st.rerun()
    
    # Floating chat functionality
    # Toggle floating chat when button is clicked
    if st.button("", key="float_chat_toggle", help="Open floating AI chat"):
        st.session_state.float_chat_visible = not st.session_state.float_chat_visible
        st.rerun()
    
    # Floating chat button and modal
    chat_visibility = "block" if st.session_state.float_chat_visible else "none"
    
    # This function has been disabled - all functionality moved to dynamic JavaScript chat
    pass

def add_patient_voice_chat(patient):
    """Add patient-specific voice chat using OpenAI Realtime API"""
    import json

    # Build patient context
    patient_data = {
        'name': patient['full_name'],
        'age': int(patient['age_at_admission']),
        'gender': 'Male' if patient['gender'] == 'M' else 'Female',
        'department': patient['facid'],
        'los': int(patient['lengthofstay']),
        'glucose': float(patient['glucose']),
        'creatinine': float(patient['creatinine']),
        'hematocrit': float(patient['hematocrit']),
        'sodium': float(patient['sodium']),
        'bun': float(patient['bloodureanitro']),
        'risk': patient['risk_level'],
        'readmit': 'Yes' if patient['readmit_flag'] == 1 else 'No'
    }

    patient_json = json.dumps(patient_data)
    api_key = os.getenv("OPENAI_API_KEY", "")

    # Warning about API key security
    if not api_key:
        st.warning("⚠️ OpenAI API Key not configured. Voice chat requires an API key in environment variables.")
        return

    components.html(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script src="https://cdn.jsdelivr.net/npm/@openai/realtime-api-beta@0.4.0/dist/index.min.js"></script>
        <style>
        .voice-chat-container {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            z-index: 1000;
        }}

        .voice-btn {{
            width: 70px;
            height: 70px;
            border-radius: 50%;
            border: none;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-size: 30px;
            cursor: pointer;
            box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .voice-btn:hover {{
            transform: scale(1.1);
            box-shadow: 0 6px 30px rgba(102, 126, 234, 0.6);
        }}

        .voice-btn.recording {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            animation: pulse 1.5s ease-in-out infinite;
        }}

        .voice-btn.connected {{
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }}

        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.05); }}
        }}

        .status-indicator {{
            position: absolute;
            bottom: -25px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 11px;
            white-space: nowrap;
            display: none;
        }}

        .status-indicator.show {{
            display: block;
        }}

        .transcript-box {{
            position: fixed;
            bottom: 120px;
            right: 30px;
            width: 350px;
            max-height: 400px;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
            padding: 15px;
            overflow-y: auto;
            display: none;
            z-index: 999;
        }}

        .transcript-box.show {{
            display: block;
        }}

        .transcript-item {{
            margin-bottom: 12px;
            padding: 8px 12px;
            border-radius: 12px;
        }}

        .transcript-item.user {{
            background: #667eea;
            color: white;
            margin-left: 20px;
        }}

        .transcript-item.assistant {{
            background: #f0f0f0;
            margin-right: 20px;
        }}
        </style>
    </head>
    <body>
        <div class="voice-chat-container">
            <button id="voiceBtn" class="voice-btn" onclick="toggleVoice()">
                🎤
            </button>
            <div id="statusIndicator" class="status-indicator">
                Ready
            </div>
        </div>

        <div id="transcriptBox" class="transcript-box">
            <h4 style="margin-top: 0;">Voice Conversation</h4>
            <div id="transcriptContent"></div>
        </div>

        <script>
        const patientData = {patient_json};
        const API_KEY = "{api_key}";

        let realtimeClient = null;
        let isConnected = false;
        let isRecording = false;
        let audioContext = null;
        let mediaStream = null;

        // Initialize OpenAI Realtime Client
        async function initRealtimeClient() {{
            try {{
                // Using the OpenAI Realtime API Beta library
                const {{ RealtimeClient }} = window.RealtimeAPI;

                realtimeClient = new RealtimeClient({{
                    apiKey: API_KEY,
                    dangerouslyAllowAPIKeyInBrowser: true
                }});

                // Set up system instructions with patient context
                realtimeClient.updateSession({{
                    instructions: `You are a medical AI assistant analyzing patient ${{patientData.name}}'s records.

Patient Details:
- Name: ${{patientData.name}}
- Age: ${{patientData.age}} years old
- Gender: ${{patientData.gender}}
- Department: ${{patientData.department}}
- Length of Stay: ${{patientData.los}} days
- Risk Level: ${{patientData.risk}}

Lab Results:
- Glucose: ${{patientData.glucose}} mg/dL
- Creatinine: ${{patientData.creatinine}} mg/dL
- Hematocrit: ${{patientData.hematocrit}}%
- Sodium: ${{patientData.sodium}} mEq/L
- BUN: ${{patientData.bun}} mg/dL
- Readmission: ${{patientData.readmit}}

Provide concise, professional medical insights. Assess abnormal values and suggest care recommendations. Keep responses under 30 seconds.`,
                    voice: 'alloy',
                    turn_detection: {{ type: 'server_vad' }}
                }});

                // Event listeners
                realtimeClient.on('conversation.updated', handleConversationUpdate);
                realtimeClient.on('error', handleError);

                await realtimeClient.connect();
                isConnected = true;
                updateStatus('Connected', 'connected');

                return true;
            }} catch (error) {{
                console.error('Failed to initialize Realtime API:', error);
                updateStatus('Connection failed', 'error');
                alert('Failed to connect to OpenAI Realtime API. Check API key and console.');
                return false;
            }}
        }}

        async function toggleVoice() {{
            if (!isConnected) {{
                updateStatus('Connecting...', '');
                const success = await initRealtimeClient();
                if (!success) return;
            }}

            if (isRecording) {{
                stopRecording();
            }} else {{
                startRecording();
            }}
        }}

        async function startRecording() {{
            try {{
                // Get microphone access
                mediaStream = await navigator.mediaDevices.getUserMedia({{ audio: true }});

                // Create audio context
                audioContext = new AudioContext({{ sampleRate: 24000 }});
                const source = audioContext.createMediaStreamSource(mediaStream);

                // Create script processor for audio data
                const processor = audioContext.createScriptProcessor(4096, 1, 1);

                processor.onaudioprocess = (e) => {{
                    if (isRecording && realtimeClient) {{
                        const inputData = e.inputBuffer.getChannelData(0);

                        // Convert Float32Array to Int16Array (PCM16)
                        const pcm16 = new Int16Array(inputData.length);
                        for (let i = 0; i < inputData.length; i++) {{
                            const s = Math.max(-1, Math.min(1, inputData[i]));
                            pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
                        }}

                        // Send to Realtime API
                        realtimeClient.appendInputAudio(pcm16);
                    }}
                }};

                source.connect(processor);
                processor.connect(audioContext.destination);

                isRecording = true;
                updateStatus('Listening...', 'recording');
                document.getElementById('transcriptBox').classList.add('show');

            }} catch (error) {{
                console.error('Failed to start recording:', error);
                alert('Microphone access denied or unavailable');
            }}
        }}

        function stopRecording() {{
            isRecording = false;

            if (mediaStream) {{
                mediaStream.getTracks().forEach(track => track.stop());
                mediaStream = null;
            }}

            if (audioContext) {{
                audioContext.close();
                audioContext = null;
            }}

            updateStatus('Connected', 'connected');
        }}

        function handleConversationUpdate(event) {{
            const items = realtimeClient.conversation.getItems();

            // Update transcript display
            const transcriptContent = document.getElementById('transcriptContent');
            transcriptContent.innerHTML = '';

            items.forEach(item => {{
                if (item.role === 'user' || item.role === 'assistant') {{
                    const div = document.createElement('div');
                    div.className = `transcript-item ${{item.role}}`;
                    div.textContent = item.formatted?.text || item.formatted?.transcript || '...';
                    transcriptContent.appendChild(div);
                }}
            }});

            // Auto-scroll to bottom
            transcriptContent.scrollTop = transcriptContent.scrollHeight;
        }}

        function handleError(error) {{
            console.error('Realtime API error:', error);
            updateStatus('Error occurred', 'error');
        }}

        function updateStatus(text, className) {{
            const btn = document.getElementById('voiceBtn');
            const indicator = document.getElementById('statusIndicator');

            indicator.textContent = text;
            indicator.classList.add('show');

            btn.className = 'voice-btn';
            if (className) {{
                btn.classList.add(className);
            }}

            setTimeout(() => {{
                if (className !== 'recording' && className !== 'connected') {{
                    indicator.classList.remove('show');
                }}
            }}, 2000);
        }}

        // Cleanup on page unload
        window.addEventListener('beforeunload', () => {{
            if (realtimeClient) {{
                realtimeClient.disconnect();
            }}
        }});
        </script>
    </body>
    </html>
    """, height=0)

if __name__ == "__main__":
    main()
    
