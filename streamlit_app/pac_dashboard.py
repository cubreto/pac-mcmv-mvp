#!/usr/bin/env python3
"""
PAC Dashboard - OGU e FGTS
Based on Power BI screens provided
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import os
from sqlalchemy import create_engine
import logging


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="PAC Dashboard - OGU e FGTS",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Add these imports at the top
import hashlib
from functools import wraps
from datetime import datetime, timedelta

# User database (same as MCMV)
USERS = {
    "rangel@digiteam.com.br": {
        "password_hash": "ebcf3510d73b4b829302228b5e98031f53f310015357db32e12e6e7ab3f7be9d",
        "name": "Guillermo Rangel",
        "company": "Digiteam",
        "role": "admin"
    },
    "rodolfo.dutra@tgvtec.com.br": {
        "password_hash": "ebcf3510d73b4b829302228b5e98031f53f310015357db32e12e6e7ab3f7be9d",
        "name": "Rodolfo Dutra",
        "company": "TGV",
        "role": "user"
    },
    "felipe.andrade@tgvtec.com.br": {
        "password_hash": "ebcf3510d73b4b829302228b5e98031f53f310015357db32e12e6e7ab3f7be9d",
        "name": "Felipe Andrade", 
        "company": "TGV",
        "role": "user"
    },
    "jcesar@digiteam.com.br": {
        "password_hash": "ebcf3510d73b4b829302228b5e98031f53f310015357db32e12e6e7ab3f7be9d",
        "name": "Julio César",
        "company": "Digiteam", 
        "role": "user"
    }
}

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(email, password):
    """Verify user credentials"""
    if email not in USERS:
        return False
    
    expected_hash = USERS[email]["password_hash"]
    actual_hash = hash_password(password)
    
    return actual_hash == expected_hash

def login_form():
    """Display login form and handle authentication"""
    st.markdown("""
    <div style="max-width: 400px; margin: 0 auto; padding: 2rem; background: white; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
        <h2 style="text-align: center; color: #1f4e79; margin-bottom: 2rem;">
            🏗️ PAC Dashboard - CAIXA
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🔐 Acesso Restrito")
    
    with st.form("login_form"):
        email = st.text_input("📧 Email Corporativo", placeholder="seu.email@empresa.com.br")
        password = st.text_input("🔑 Senha", type="password", placeholder="Digite sua senha")
        submit_button = st.form_submit_button("Entrar", use_container_width=True)
        
        if submit_button:
            if verify_password(email, password):
                # Store user session
                st.session_state.authenticated = True
                st.session_state.user_email = email
                st.session_state.user_name = USERS[email]["name"]
                st.session_state.user_company = USERS[email]["company"]
                st.session_state.user_role = USERS[email]["role"]
                st.session_state.login_time = datetime.now()
                
                st.success(f"✅ Bem-vindo, {USERS[email]['name']}!")
                st.rerun()
            else:
                st.error("❌ Email ou senha incorretos")
    
    st.info("""
    📋 **Instruções de Acesso:**
    - Digite seu email e senha para acessar o dashboard PAC
    """)

def check_session_timeout():
    """Check if user session has expired (8 hours)"""
    if 'login_time' in st.session_state:
        login_time = st.session_state.login_time
        current_time = datetime.now()
        if current_time - login_time > timedelta(hours=8):
            # Session expired
            for key in ['authenticated', 'user_email', 'user_name', 'user_company', 'user_role', 'login_time']:
                if key in st.session_state:
                    del st.session_state[key]
            st.warning("🕐 Sessão expirada. Faça login novamente.")
            st.rerun()

def user_info_sidebar():
    """Display user information in sidebar"""
    if st.session_state.get('authenticated', False):
        with st.sidebar:
            st.markdown("---")
            st.markdown("### 👤 Usuário Logado")
            st.write(f"**Nome:** {st.session_state.user_name}")
            st.write(f"**Email:** {st.session_state.user_email}")
            st.write(f"**Empresa:** {st.session_state.user_company}")
            
            if st.session_state.user_role == "admin":
                st.write("**Função:** 🔑 Administrador")
            else:
                st.write("**Função:** 👤 Usuário")
            
            # Login time
            login_time = st.session_state.login_time.strftime("%d/%m/%Y %H:%M")
            st.write(f"**Login:** {login_time}")
            
            # Logout button
            if st.button("🚪 Sair", use_container_width=True):
                for key in ['authenticated', 'user_email', 'user_name', 'user_company', 'user_role', 'login_time']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

def require_auth(func):
    """Decorator to require authentication for dashboard functions"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Check session timeout
        check_session_timeout()
        
        # Check if user is authenticated
        if not st.session_state.get('authenticated', False):
            login_form()
            return
        
        # Display user info in sidebar
        user_info_sidebar()
        
        # Call the actual function
        return func(*args, **kwargs)
    
    return wrapper

# Custom CSS for enhanced Brazilian theme (CAIXA professional styling)
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Global styling */
    .stApp {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #0066cc 0%, #004499 50%, #002975 100%);
        padding: 2rem;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        border: 3px solid #FFD700;
        box-shadow: 0 15px 50px rgba(0, 102, 204, 0.4);
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,215,0,0.1) 0%, transparent 70%);
        animation: pulse 4s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); opacity: 0.5; }
        50% { transform: scale(1.1); opacity: 0.8; }
    }
    
    .main-header h1 {
        font-size: 2.8rem !important;
        font-weight: 700 !important;
        margin-bottom: 1rem !important;
        text-shadow: 2px 2px 8px rgba(0, 0, 0, 0.3);
        position: relative;
        z-index: 2;
    }
    
    .main-header p {
        font-size: 1.2rem !important;
        opacity: 0.95;
        position: relative;
        z-index: 2;
    }
    
    /* Alert banner enhanced */
    .alert-banner {
        background: linear-gradient(45deg, #FFD700 0%, #FFA500 50%, #FF8C00 100%);
        color: #002975;
        padding: 1.5rem;
        border-radius: 15px;
        font-weight: 600;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 8px 25px rgba(255, 165, 0, 0.4);
        border: 2px solid rgba(255, 255, 255, 0.3);
        font-size: 1.1rem;
    }
    
    /* Enhanced metric cards */
    .metric-card {
        background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
        padding: 2rem;
        border-radius: 20px;
        border-left: 6px solid #0066cc;
        margin: 1rem 0;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #0066cc, #FFD700, #0066cc);
        animation: shimmer 3s linear infinite;
    }
    
    @keyframes shimmer {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 40px rgba(0, 102, 204, 0.15);
        border-left-color: #FFD700;
    }
    
    /* Enhanced phase tabs */
    .phase-tab {
        background: linear-gradient(145deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 249, 250, 0.95) 100%);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 2rem;
        margin: 1.5rem 0;
        border: 2px solid rgba(255, 215, 0, 0.3);
        box-shadow: 0 15px 40px rgba(0, 0, 0, 0.08);
    }
    
    /* Enhanced KPI numbers */
    .kpi-number {
        font-size: 3.5rem !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #0066cc 0%, #004499 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-shadow: none;
        margin: 1rem 0 !important;
        line-height: 1.2;
    }
    
    .kpi-label {
        font-size: 1rem;
        color: #495057;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Status indicators enhanced */
    .status-good { 
        color: #28a745; 
        font-weight: 600;
        text-shadow: 0 1px 3px rgba(40, 167, 69, 0.3);
    }
    .status-warning { 
        color: #ffc107; 
        font-weight: 600;
        text-shadow: 0 1px 3px rgba(255, 193, 7, 0.3);
    }
    .status-critical { 
        color: #dc3545; 
        font-weight: 600;
        text-shadow: 0 1px 3px rgba(220, 53, 69, 0.3);
    }
    
    /* Enhanced sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%);
        border-right: 3px solid #e9ecef;
    }
    
    /* Enhanced tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255, 255, 255, 0.8);
        padding: 8px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
        border-radius: 12px;
        padding: 12px 24px;
        border: 2px solid transparent;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #0066cc 0%, #004499 100%);
        color: white !important;
        border-color: #FFD700;
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 102, 204, 0.3);
    }
    
    /* Enhanced metrics */
    div[data-testid="metric-container"] {
        background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
        border: 2px solid transparent;
        border-image: linear-gradient(135deg, #0066cc, #FFD700) 1;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.06);
        transition: all 0.3s ease;
    }
    
    div[data-testid="metric-container"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 15px 40px rgba(0, 102, 204, 0.12);
    }
    
    div[data-testid="metric-container"] > div {
        color: #0066cc !important;
        font-weight: 700 !important;
    }
    
    /* Enhanced dataframes */
    .stDataFrame {
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
        border: 2px solid #e9ecef;
    }
    
    /* Enhanced buttons */
    .stButton > button {
        background: linear-gradient(135deg, #0066cc 0%, #004499 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0, 102, 204, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 102, 204, 0.4);
        background: linear-gradient(135deg, #004499 0%, #002975 100%);
    }
    
    /* Enhanced plotly charts */
    .js-plotly-plot {
        border-radius: 15px;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.06);
        overflow: hidden;
        border: 2px solid #f8f9fa;
    }
    
    /* Enhanced selectbox and multiselect */
    .stSelectbox > div > div {
        border-radius: 12px;
        border: 2px solid #e9ecef;
        transition: border-color 0.3s ease;
    }
    
    .stSelectbox > div > div:focus-within {
        border-color: #0066cc;
        box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.1);
    }
    
    .stMultiSelect > div > div {
        border-radius: 12px;
        border: 2px solid #e9ecef;
    }
    
    /* Progress bars */
    .stProgress .st-emotion-cache-1y0tads {
        background: linear-gradient(90deg, #0066cc 0%, #FFD700 100%);
        border-radius: 10px;
    }
    
    /* Info boxes */
    .stInfo {
        background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
        border-left: 5px solid #0066cc;
        border-radius: 10px;
    }
    
    .stSuccess {
        background: linear-gradient(135deg, #e8f5e8 0%, #f1f8e9 100%);
        border-left: 5px solid #28a745;
        border-radius: 10px;
    }
    
    .stWarning {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        border-left: 5px solid #ffc107;
        border-radius: 10px;
    }
    
    .stError {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        border-left: 5px solid #dc3545;
        border-radius: 10px;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 2rem !important;
        }
        
        .kpi-number {
            font-size: 2.5rem !important;
        }
        
        .metric-card {
            padding: 1.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_database_connection_string():
    """Get database connection string"""
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5434')
    db_name = os.getenv('DB_NAME', 'pac_database')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', 'postgres123')
    
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

def get_database_connection():
    """Get database connection - not cached"""
    try:
        connection_string = get_database_connection_string()
        engine = create_engine(connection_string)
        return engine
        
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

@st.cache_data(ttl=300)
def load_pac_data():
    """Load PAC data from database"""
    try:
        connection_string = get_database_connection_string()
        engine = create_engine(connection_string)
            
        query = "SELECT * FROM pac_ogu_data"
        df = pd.read_sql(query, engine)
        
        if df.empty:
            st.warning("⚠️ No data found in database. Please run ETL first.")
            return None
            
        logger.info(f"Loaded {len(df)} records from database")
        return df
        
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        return None

@st.cache_data(ttl=300)
def load_pac_views():
    """Load PAC dashboard views"""
    try:
        connection_string = get_database_connection_string()
        engine = create_engine(connection_string)
        
        views = {}
        
        # Load suspensivas view
        try:
            views['suspensivas'] = pd.read_sql("SELECT * FROM vw_pac_suspensivas", engine)
        except:
            views['suspensivas'] = pd.DataFrame()
            
        # Load VRPL view
        try:
            views['vrpl'] = pd.read_sql("SELECT * FROM vw_pac_vrpl", engine)
        except:
            views['vrpl'] = pd.DataFrame()
            
        # Load obras view
        try:
            views['obras'] = pd.read_sql("SELECT * FROM vw_pac_obras", engine)
        except:
            views['obras'] = pd.DataFrame()
            
        # Load portfolio summary
        try:
            views['summary'] = pd.read_sql("SELECT * FROM vw_pac_portfolio_summary", engine)
        except:
            views['summary'] = pd.DataFrame()
            
        return views
        
    except Exception as e:
        st.error(f"Failed to load views: {e}")
        return {}

def format_currency(value):
    """Format value as Brazilian currency"""
    if pd.isna(value) or value == 0:
        return "R$ 0,00"
    
    if value >= 1e9:
        return f"R$ {value/1e9:.1f}B"
    elif value >= 1e6:
        return f"R$ {value/1e6:.1f}M"
    elif value >= 1e3:
        return f"R$ {value/1e3:.1f}K"
    else:
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_number(value):
    """Format number with Brazilian formatting"""
    if pd.isna(value):
        return "0"
    return f"{int(value):,}".replace(",", ".")

@require_auth
def main():
    # Header with enhanced design
    st.markdown("""
    <div class="main-header">
        <div style="display: flex; align-items: center; justify-content: center; gap: 20px;">
            <div style="font-size: 3rem;">🏦</div>
            <div>
                <h1 style="margin: 0; background: linear-gradient(45deg, #FFD700, #FFF); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                    PAC Dashboard - OGU e FGTS
                </h1>
                <div style="margin: 10px 0; font-size: 1.3rem; font-weight: 600;">
                    Gestão da Carteira Contratada - Novo PAC
                </div>
                <div style="margin: 0; font-size: 1rem; opacity: 0.9; font-weight: 500;">
                    CAIXA ECONÔMICA FEDERAL | Análise de Suspensivas, Licitação e Obras
                </div>
            </div>
            <div style="font-size: 3rem;">🏗️</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Load data
    df = load_pac_data()
    views = load_pac_views()
    
    if df is None or df.empty:
        st.error("❌ Nenhum dado disponível. Verifique:")
        st.write("1. Banco de dados rodando (`docker-compose -f docker-compose.pac.yml up -d`)")
        st.write("2. ETL foi executado (`python etl/pac_etl.py`)")
        st.write("3. Arquivo de dados existe em `data/pac/`")
        st.stop()
    
    # Calculate portfolio summary
    total_operacoes = len(df)
    total_estados = df['uf'].nunique() if 'uf' in df.columns else 0
    total_municipios = df['municipio_beneficiado'].nunique() if 'municipio_beneficiado' in df.columns else 0
    total_ministerios = df['repassador'].nunique() if 'repassador' in df.columns else 0
    valor_total = df['valor_empenhado'].sum() if 'valor_empenhado' in df.columns else 0
    
    # Enhanced alert banner with icons and better formatting
    st.markdown(f"""
    <div class="alert-banner">
        <div style="display: flex; align-items: center; justify-content: center; gap: 30px; flex-wrap: wrap;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 1.4rem;">📊</span>
                <strong>{format_number(total_operacoes)} operações ativas</strong>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 1.4rem;">🗺️</span>
                <strong>{total_estados} estados</strong>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 1.4rem;">🏙️</span>
                <strong>{total_municipios} municípios</strong>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 1.4rem;">🏛️</span>
                <strong>{total_ministerios} ministérios</strong>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 1.4rem;">💰</span>
                <strong>{format_currency(valor_total)} empenhado</strong>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


    
    # Enhanced sidebar filters with better UX
    st.sidebar.header("🔍 Filtros Inteligentes")
    
    # Quick filter presets
    st.sidebar.subheader("🚀 Filtros Rápidos")
    
    filter_preset = st.sidebar.selectbox(
        "Seleção Rápida:",
        [
            "🌟 Todos os Dados",
            "⚠️ Operações Críticas (>60 dias)",
            "🔥 Prioridade Alta (>40 dias)", 
            "🎯 Grandes Volumes (>R$ 100M)",
            "🏛️ Principais Ministérios",
            "🗺️ Regiões Prioritárias",
            "✅ Personalizado"
        ],
        index=0
    )
    
    # Apply preset filters
    if filter_preset == "⚠️ Operações Críticas (>60 dias)":
        # Filter to operations with >60 days without movement
        if 'dias_sem_movimentacao' in df.columns:
            critical_ops = df[df['dias_sem_movimentacao'] > 60]
            selected_uf = sorted(critical_ops['uf'].dropna().unique().tolist()) if 'uf' in critical_ops.columns else []
            selected_repassador = sorted(critical_ops['repassador'].dropna().unique().tolist()) if 'repassador' in critical_ops.columns else []
            selected_regiao = sorted(critical_ops['gigov_regov'].dropna().unique().tolist()) if 'gigov_regov' in critical_ops.columns else []
        else:
            selected_uf = selected_repassador = selected_regiao = []
            
    elif filter_preset == "🔥 Prioridade Alta (>40 dias)":
        if 'dias_sem_movimentacao' in df.columns:
            priority_ops = df[df['dias_sem_movimentacao'] > 40]
            selected_uf = sorted(priority_ops['uf'].dropna().unique().tolist()) if 'uf' in priority_ops.columns else []
            selected_repassador = sorted(priority_ops['repassador'].dropna().unique().tolist()) if 'repassador' in priority_ops.columns else []
            selected_regiao = sorted(priority_ops['gigov_regov'].dropna().unique().tolist()) if 'gigov_regov' in priority_ops.columns else []
        else:
            selected_uf = selected_repassador = selected_regiao = []
            
    elif filter_preset == "🎯 Grandes Volumes (>R$ 100M)":
        if 'valor_empenhado' in df.columns:
            high_value_ops = df[df['valor_empenhado'] > 100000000]  # >100M
            selected_uf = sorted(high_value_ops['uf'].dropna().unique().tolist()) if 'uf' in high_value_ops.columns else []
            selected_repassador = sorted(high_value_ops['repassador'].dropna().unique().tolist()) if 'repassador' in high_value_ops.columns else []
            selected_regiao = sorted(high_value_ops['gigov_regov'].dropna().unique().tolist()) if 'gigov_regov' in high_value_ops.columns else []
        else:
            selected_uf = selected_repassador = selected_regiao = []
            
    elif filter_preset == "🏛️ Principais Ministérios":
        if 'repassador' in df.columns:
            # Get top 5 ministries by operation count
            top_ministries = df['repassador'].value_counts().head(5).index.tolist()
            top_ministry_ops = df[df['repassador'].isin(top_ministries)]
            selected_uf = sorted(top_ministry_ops['uf'].dropna().unique().tolist()) if 'uf' in top_ministry_ops.columns else []
            selected_repassador = top_ministries
            selected_regiao = sorted(top_ministry_ops['gigov_regov'].dropna().unique().tolist()) if 'gigov_regov' in top_ministry_ops.columns else []
        else:
            selected_uf = selected_repassador = selected_regiao = []
            
    elif filter_preset == "🗺️ Regiões Prioritárias":
        if 'gigov_regov' in df.columns:
            # Get top 3 regions by operation count
            top_regions = df['gigov_regov'].value_counts().head(3).index.tolist()
            top_region_ops = df[df['gigov_regov'].isin(top_regions)]
            selected_uf = sorted(top_region_ops['uf'].dropna().unique().tolist()) if 'uf' in top_region_ops.columns else []
            selected_repassador = sorted(top_region_ops['repassador'].dropna().unique().tolist()) if 'repassador' in top_region_ops.columns else []
            selected_regiao = top_regions
        else:
            selected_uf = selected_repassador = selected_regiao = []
            
    elif filter_preset == "✅ Personalizado":
        # Show custom filters
        st.sidebar.subheader("🎛️ Filtros Personalizados")
        
        # Smart UF filter with search
        if 'uf' in df.columns:
            available_ufs = sorted([uf for uf in df['uf'].dropna().unique() if uf and str(uf) != 'nan'])
            
            # UF selection with search
            uf_search = st.sidebar.text_input("🔍 Buscar Estados (ex: SP, RJ):", key="uf_search")
            
            if uf_search:
                # Filter UFs based on search
                filtered_ufs = [uf for uf in available_ufs if uf_search.upper() in uf.upper()]
                st.sidebar.write(f"**Estados encontrados:** {', '.join(filtered_ufs)}")
                selected_uf = st.sidebar.multiselect(
                    f"Estados (encontrados: {len(filtered_ufs)}):",
                    options=filtered_ufs,
                    default=filtered_ufs,
                    key="uf_filtered"
                )
            else:
                # Quick selection options
                uf_selection_type = st.sidebar.radio(
                    "Seleção de Estados:",
                    ["📍 Principais (Top 10)", "🌎 Todos", "✏️ Personalizar"]
                )
                
                if uf_selection_type == "📍 Principais (Top 10)":
                    top_ufs = df['uf'].value_counts().head(10).index.tolist()
                    selected_uf = st.sidebar.multiselect(
                        f"Estados (Top 10):",
                        options=top_ufs,
                        default=top_ufs
                    )
                elif uf_selection_type == "🌎 Todos":
                    selected_uf = available_ufs
                else:
                    selected_uf = st.sidebar.multiselect(
                        f"Selecionar Estados ({len(available_ufs)} disponíveis):",
                        options=available_ufs,
                        default=available_ufs[:10] if len(available_ufs) > 10 else available_ufs
                    )
        else:
            selected_uf = []
        
        # Smart Repassador filter
        if 'repassador' in df.columns:
            available_repassadores = sorted([rep for rep in df['repassador'].dropna().unique() if rep and str(rep) != 'nan'])
            
            repassador_search = st.sidebar.text_input("🔍 Buscar Ministério:", key="rep_search")
            
            if repassador_search:
                filtered_reps = [rep for rep in available_repassadores if repassador_search.upper() in rep.upper()]
                st.sidebar.write(f"**Encontrados:** {len(filtered_reps)} ministérios")
                selected_repassador = st.sidebar.multiselect(
                    "Ministérios encontrados:",
                    options=filtered_reps,
                    default=filtered_reps
                )
            else:
                rep_selection_type = st.sidebar.radio(
                    "Seleção de Ministérios:",
                    ["🎯 Principais (Top 5)", "🏛️ Todos", "✏️ Personalizar"]
                )
                
                if rep_selection_type == "🎯 Principais (Top 5)":
                    top_reps = df['repassador'].value_counts().head(5).index.tolist()
                    selected_repassador = st.sidebar.multiselect(
                        "Ministérios (Top 5):",
                        options=top_reps,
                        default=top_reps
                    )
                elif rep_selection_type == "🏛️ Todos":
                    selected_repassador = available_repassadores
                else:
                    selected_repassador = st.sidebar.multiselect(
                        f"Selecionar Ministérios ({len(available_repassadores)}):",
                        options=available_repassadores,
                        default=available_repassadores[:5] if len(available_repassadores) > 5 else available_repassadores
                    )
        else:
            selected_repassador = []
        
        # Smart GIGOV filter
        if 'gigov_regov' in df.columns:
            available_regioes = sorted([reg for reg in df['gigov_regov'].dropna().unique() if reg and str(reg) != 'nan'])
            selected_regiao = st.sidebar.multiselect(
                f"GIGOV/REGOV ({len(available_regioes)} regiões):",
                options=available_regioes,
                default=available_regioes
            )
        else:
            selected_regiao = []
            
    else:  # "🌟 Todos os Dados"
        # Default: all data
        if 'uf' in df.columns:
            selected_uf = sorted([uf for uf in df['uf'].dropna().unique() if uf and str(uf) != 'nan'])
        else:
            selected_uf = []
            
        if 'repassador' in df.columns:
            selected_repassador = sorted([rep for rep in df['repassador'].dropna().unique() if rep and str(rep) != 'nan'])
        else:
            selected_repassador = []
            
        if 'gigov_regov' in df.columns:
            selected_regiao = sorted([reg for reg in df['gigov_regov'].dropna().unique() if reg and str(reg) != 'nan'])
        else:
            selected_regiao = []
    
    # Apply filters
    filtered_df = df.copy()
    
    if selected_uf and 'uf' in df.columns:
        filtered_df = filtered_df[filtered_df['uf'].isin(selected_uf)]
    
    if selected_repassador and 'repassador' in df.columns:
        filtered_df = filtered_df[filtered_df['repassador'].isin(selected_repassador)]
    
    if selected_regiao and 'gigov_regov' in df.columns:
        filtered_df = filtered_df[filtered_df['gigov_regov'].isin(selected_regiao)]
    
    # Enhanced sidebar summary with visual indicators
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 **Resumo dos Filtros**")
    
    # Calculate filtered results
    filter_summary_ops = len(filtered_df)
    filter_summary_states = filtered_df['uf'].nunique() if 'uf' in filtered_df.columns else 0
    filter_summary_municipios = filtered_df['municipio_beneficiado'].nunique() if 'municipio_beneficiado' in filtered_df.columns else 0
    
    # Visual summary cards in sidebar
    st.sidebar.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
        padding: 1rem;
        border-radius: 12px;
        border-left: 4px solid #0066cc;
        margin: 0.5rem 0;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-weight: 600;">📋 Operações:</span>
            <span style="font-size: 1.2rem; font-weight: bold; color: #0066cc;">{filter_summary_ops:,}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #e8f5e8 0%, #f1f8e9 100%);
        padding: 1rem;
        border-radius: 12px;
        border-left: 4px solid #28a745;
        margin: 0.5rem 0;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-weight: 600;">🗺️ Estados:</span>
            <span style="font-size: 1.2rem; font-weight: bold; color: #28a745;">{filter_summary_states}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        padding: 1rem;
        border-radius: 12px;
        border-left: 4px solid #ffc107;
        margin: 0.5rem 0;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-weight: 600;">🏙️ Municípios:</span>
            <span style="font-size: 1.2rem; font-weight: bold; color: #856404;">{filter_summary_municipios}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Filter status indicator
    total_original_ops = len(df)
    filter_percentage = (filter_summary_ops / total_original_ops * 100) if total_original_ops > 0 else 0
    
    if filter_percentage == 100:
        filter_status = "🌟 Exibindo todos os dados"
        filter_color = "#28a745"
    elif filter_percentage >= 50:
        filter_status = f"📊 Filtrado: {filter_percentage:.1f}% dos dados"
        filter_color = "#0066cc"
    else:
        filter_status = f"🔍 Filtro restrito: {filter_percentage:.1f}%"
        filter_color = "#ffc107"
    
    st.sidebar.markdown(f"""
    <div style="
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(248, 249, 250, 0.9) 100%);
        padding: 1rem;
        border-radius: 12px;
        border: 2px solid {filter_color};
        margin: 1rem 0;
        text-align: center;
    ">
        <div style="color: {filter_color}; font-weight: 600; font-size: 0.9rem;">
            {filter_status}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick actions
    st.sidebar.markdown("### ⚡ **Ações Rápidas**")
    
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("🔄 Resetar", use_container_width=True):
            st.rerun()
    
    with col2:
        if st.button("📊 Atualizar", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    # Main navigation tabs (based on Power BI structure)
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Suspensivas", 
        "🏗️ Licitação/VRPL", 
        "🏠 Obras", 
        "📊 Visão Geral"
    ])
    
    with tab1:
        st.markdown('<div class="phase-tab">', unsafe_allow_html=True)
        suspensivas_module(filtered_df, views.get('suspensivas', pd.DataFrame()))
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown('<div class="phase-tab">', unsafe_allow_html=True)
        licitacao_module(filtered_df, views.get('vrpl', pd.DataFrame()))
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab3:
        st.markdown('<div class="phase-tab">', unsafe_allow_html=True)
        obras_module(filtered_df, views.get('obras', pd.DataFrame()))
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab4:
        st.markdown('<div class="phase-tab">', unsafe_allow_html=True)
        overview_module(filtered_df, views.get('summary', pd.DataFrame()))
        st.markdown('</div>', unsafe_allow_html=True)

def suspensivas_module(df, suspensivas_df):
    """Suspensivas module - 6 screens from Power BI"""
    st.header("📋 Gestão da Carteira Contratada - Suspensivas")
    
    if df.empty:
        st.warning("⚠️ Nenhum dado disponível após aplicar os filtros")
        return
    
    # Sub-navigation for the 6 suspensivas screens
    sub_tab1, sub_tab2, sub_tab3, sub_tab4, sub_tab5, sub_tab6 = st.tabs([
        "📊 Visão Geral", "🔍 Ações", "📋 Detalhes", "🗺️ Regional", "📈 Desempenho", "🎯 Indicadores"
    ])
    
    with sub_tab1:
        suspensivas_overview(df, suspensivas_df)
    
    with sub_tab2:
        suspensivas_actions(df, suspensivas_df)
    
    with sub_tab3:
        suspensivas_details(df, suspensivas_df)
    
    with sub_tab4:
        suspensivas_regional(df, suspensivas_df)
    
    with sub_tab5:
        suspensivas_performance(df, suspensivas_df)
    
    with sub_tab6:
        suspensivas_kpis(df, suspensivas_df)

def suspensivas_overview(df, suspensivas_df):
    """Suspensivas Overview - Screen 1 from Power BI"""
    st.subheader("📊 Suspensivas - Visão Geral")
    
    # Use suspensivas view if available, otherwise main df
    data_df = suspensivas_df if not suspensivas_df.empty else df
    
    # Enhanced key metrics with visual cards
    total_ops = len(data_df)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div style="display: flex; align-items: center; gap: 15px;">
                <div style="font-size: 3rem; opacity: 0.8;">📊</div>
                <div>
                    <div class="kpi-number">{format_number(total_ops)}</div>
                    <div class="kpi-label">Total de Operações</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if 'dias_sem_movimentacao' in data_df.columns:
            avg_days = data_df['dias_sem_movimentacao'].mean()
            if pd.notna(avg_days):
                status_color = "🟢" if avg_days <= 30 else "🟡" if avg_days <= 60 else "🔴"
                st.markdown(f"""
                <div class="metric-card">
                    <div style="display: flex; align-items: center; gap: 15px;">
                        <div style="font-size: 3rem; opacity: 0.8;">⏱️</div>
                        <div>
                            <div class="kpi-number">{avg_days:.0f}</div>
                            <div class="kpi-label">Média Dias sem Movimento {status_color}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    with col3:
        if 'dias_sem_movimentacao' in data_df.columns:
            pending = len(data_df[data_df['dias_sem_movimentacao'] > 40])
            pending_pct = (pending / total_ops * 100) if total_ops > 0 else 0
            st.markdown(f"""
            <div class="metric-card">
                <div style="display: flex; align-items: center; gap: 15px;">
                    <div style="font-size: 3rem; opacity: 0.8;">⚠️</div>
                    <div>
                        <div class="kpi-number status-warning">{format_number(pending)}</div>
                        <div class="kpi-label">Operações > 40 dias ({pending_pct:.1f}%)</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with col4:
        if 'valor_empenhado' in data_df.columns:
            total_value = data_df['valor_empenhado'].sum()
            st.markdown(f"""
            <div class="metric-card">
                <div style="display: flex; align-items: center; gap: 15px;">
                    <div style="font-size: 3rem; opacity: 0.8;">💰</div>
                    <div>
                        <div class="kpi-number">{format_currency(total_value)}</div>
                        <div class="kpi-label">Valor Total Empenhado</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Main visualizations row with enhanced charts
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Enhanced scatter plot with multiple dimensions
        st.subheader("🎯 Análise Multidimensional de Suspensivas")
        
        if 'dias_sem_movimentacao' in data_df.columns and 'repassador' in data_df.columns:
            # Create enhanced scatter plot with size and color dimensions
            scatter_df = data_df.reset_index()
            
            # Add performance score
            if 'valor_empenhado' in data_df.columns:
                scatter_df['valor_normalizado'] = scatter_df['valor_empenhado'] / scatter_df['valor_empenhado'].max() * 100
            else:
                scatter_df['valor_normalizado'] = 10
            
            # Add urgency classification
            scatter_df['urgencia'] = scatter_df['dias_sem_movimentacao'].apply(lambda x: 
                '🔴 Crítico (>90d)' if pd.notna(x) and x > 90 else
                '🟡 Urgente (60-90d)' if pd.notna(x) and x > 60 else
                '🟠 Atenção (40-60d)' if pd.notna(x) and x > 40 else
                '🟢 Normal (<40d)'
            )
            
            # Create advanced scatter plot
            fig_scatter = px.scatter(
                scatter_df, 
                x=scatter_df.index,
                y='dias_sem_movimentacao',
                color='urgencia',
                size='valor_normalizado',
                hover_data={
                    'operacao': True,
                    'repassador': True,
                    'municipio_beneficiado': True if 'municipio_beneficiado' in scatter_df.columns else False,
                    'valor_empenhado': ':,.0f' if 'valor_empenhado' in scatter_df.columns else False,
                    'index': False,
                    'valor_normalizado': False
                },
                title="Operações por Criticidade e Volume",
                labels={
                    'index': 'Sequência das Operações',
                    'dias_sem_movimentacao': 'Dias sem Movimentação',
                    'urgencia': 'Nível de Urgência'
                },
                color_discrete_map={
                    '🔴 Crítico (>90d)': '#dc3545',
                    '🟡 Urgente (60-90d)': '#ffc107', 
                    '🟠 Atenção (40-60d)': '#fd7e14',
                    '🟢 Normal (<40d)': '#28a745'
                }
            )
            
            # Add trend line
            if len(scatter_df) > 10:
                z = np.polyfit(scatter_df.index, scatter_df['dias_sem_movimentacao'].fillna(0), 1)
                p = np.poly1d(z)
                fig_scatter.add_traces(
                    px.line(x=scatter_df.index, y=p(scatter_df.index)).data[0].update(
                        name="Tendência",
                        line=dict(color="rgba(255, 255, 255, 0.8)", width=3, dash="dash")
                    )
                )
            
            # Add SLA reference lines
            fig_scatter.add_hline(y=40, line_dash="dot", line_color="orange", 
                                annotation_text="SLA 40 dias", annotation_position="right")
            fig_scatter.add_hline(y=60, line_dash="dot", line_color="red", 
                                annotation_text="SLA 60 dias", annotation_position="right")
            fig_scatter.add_hline(y=90, line_dash="solid", line_color="darkred", 
                                annotation_text="Limite Crítico 90 dias", annotation_position="right")
            
            fig_scatter.update_layout(
                height=500,
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            fig_scatter.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
            fig_scatter.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
            
            st.plotly_chart(fig_scatter, use_container_width=True)
            
            # Performance insights below the chart
            critical_count = len(scatter_df[scatter_df['urgencia'] == '🔴 Crítico (>90d)'])
            urgent_count = len(scatter_df[scatter_df['urgencia'] == '🟡 Urgente (60-90d)'])
            
            if critical_count > 0:
                st.error(f"⚠️ **Ação Imediata Necessária:** {critical_count} operações críticas (>90 dias)")
            if urgent_count > 0:
                st.warning(f"🔔 **Atenção:** {urgent_count} operações urgentes (60-90 dias)")
                
        else:
            st.info("Dados de dias sem movimentação não disponíveis")
    
    with col2:
        # Enhanced analytics panel
        st.subheader("📊 Painel de Insights")
        
        # Performance heatmap by region and ministry
        if 'repassador' in data_df.columns and 'gigov_regov' in data_df.columns:
            st.markdown("#### 🔥 Mapa de Calor - Performance")
            
            # Create performance matrix
            performance_matrix = data_df.groupby(['gigov_regov', 'repassador']).agg({
                'dias_sem_movimentacao': 'mean',
                'operacao': 'count'
            }).reset_index()
            
            performance_matrix = performance_matrix[performance_matrix['operacao'] >= 3]  # Filter to significant combinations
            
            if not performance_matrix.empty:
                # Create heatmap
                fig_heatmap = px.density_heatmap(
                    performance_matrix,
                    x='repassador',
                    y='gigov_regov', 
                    z='dias_sem_movimentacao',
                    title="Tempo Médio por Região × Ministério",
                    color_continuous_scale='RdYlGn_r',
                    labels={'dias_sem_movimentacao': 'Dias Médios'}
                )
                fig_heatmap.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
                fig_heatmap.update_xaxes(tickangle=45)
                st.plotly_chart(fig_heatmap, use_container_width=True)
        
        # Top performers and bottlenecks
        st.markdown("#### 🏆 Top Performers vs 🚨 Gargalos")
        
        if 'repassador' in data_df.columns and 'dias_sem_movimentacao' in data_df.columns:
            ministry_performance = data_df.groupby('repassador').agg({
                'dias_sem_movimentacao': 'mean',
                'operacao': 'count'
            }).reset_index()
            
            ministry_performance = ministry_performance[ministry_performance['operacao'] >= 5]
            
            if not ministry_performance.empty:
                # Top 3 performers
                top_performers = ministry_performance.nsmallest(3, 'dias_sem_movimentacao')
                st.markdown("**🥇 Melhores Performances:**")
                
                for idx, row in top_performers.iterrows():
                    medal = ["🥇", "🥈", "🥉"][list(top_performers.index).index(idx)]
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%); 
                                padding: 0.8rem; margin: 0.3rem 0; border-radius: 8px; 
                                border-left: 4px solid #28a745;">
                        <strong>{medal} {row['repassador'][:25]}...</strong><br>
                        <span style="color: #155724;">⏱️ {row['dias_sem_movimentacao']:.1f} dias médios | 📊 {row['operacao']:.0f} operações</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Bottom 3 (need attention)
                bottom_performers = ministry_performance.nlargest(3, 'dias_sem_movimentacao')
                st.markdown("**🚨 Precisam de Atenção:**")
                
                for idx, row in bottom_performers.iterrows():
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%); 
                                padding: 0.8rem; margin: 0.3rem 0; border-radius: 8px; 
                                border-left: 4px solid #dc3545;">
                        <strong>⚠️ {row['repassador'][:25]}...</strong><br>
                        <span style="color: #721c24;">⏱️ {row['dias_sem_movimentacao']:.1f} dias médios | 📊 {row['operacao']:.0f} operações</span>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Regional comparison radar chart
        if 'gigov_regov' in data_df.columns:
            st.markdown("#### 🎯 Comparativo Regional")
            
            regional_metrics = data_df.groupby('gigov_regov').agg({
                'operacao': 'count',
                'dias_sem_movimentacao': 'mean',
                'data_retirada_suspensiva': lambda x: x.notna().sum() if 'data_retirada_suspensiva' in data_df.columns else 0,
                'valor_empenhado': 'sum' if 'valor_empenhado' in data_df.columns else lambda x: 0
            }).reset_index()
            
            if not regional_metrics.empty and len(regional_metrics) >= 3:
                # Normalize metrics for radar chart
                regional_metrics['volume_norm'] = (regional_metrics['operacao'] / regional_metrics['operacao'].max() * 100).round(1)
                regional_metrics['tempo_norm'] = (100 - (regional_metrics['dias_sem_movimentacao'] / regional_metrics['dias_sem_movimentacao'].max() * 100)).round(1)
                regional_metrics['conclusao_norm'] = ((regional_metrics['data_retirada_suspensiva'] / regional_metrics['operacao']) * 100).round(1)
                
                # Create mini radar for top 3 regions
                top_regions = regional_metrics.nlargest(3, 'operacao')
                
                categories = ['Volume', 'Velocidade', 'Taxa Conclusão']
                
                fig_radar = go.Figure()
                
                colors = ['#0066cc', '#28a745', '#ffc107']
                for idx, (_, region) in enumerate(top_regions.iterrows()):
                    fig_radar.add_trace(go.Scatterpolar(
                        r=[region['volume_norm'], region['tempo_norm'], region['conclusao_norm']],
                        theta=categories,
                        fill='toself',
                        name=region['gigov_regov'][:15],
                        line_color=colors[idx],
                        fillcolor=f"rgba{(*[int(colors[idx][i:i+2], 16) for i in (1, 3, 5)], 0.1)}"
                    ))
                
                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(visible=True, range=[0, 100])
                    ),
                    showlegend=True,
                    height=250,
                    margin=dict(l=20, r=20, t=20, b=20)
                )
                
                st.plotly_chart(fig_radar, use_container_width=True)

def suspensivas_actions(df, suspensivas_df):
    """Suspensivas Action Items - Screen 2 from Power BI"""
    st.subheader("🔍 Ações Necessárias - Suspensivas")
    
    # Use suspensivas view if available, otherwise main df
    data_df = suspensivas_df if not suspensivas_df.empty else df
    
    if data_df.empty:
        st.warning("⚠️ Nenhum dado de suspensivas disponível")
        return
    
    # Action filters section (left side)
    st.subheader("Filtros de Ação")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        st.markdown("**Tipos de Ação:**")
        
        # Get unique action types from etiquetas
        if 'etiquetas' in data_df.columns:
            available_actions = sorted([action for action in data_df['etiquetas'].dropna().unique() if action and str(action) != 'nan'])
            
            # Create checkboxes for each action type
            selected_actions = []
            for action in available_actions:
                if st.checkbox(action, value=True, key=f"action_{action}"):
                    selected_actions.append(action)
        else:
            selected_actions = []
            st.info("Dados de etiquetas não disponíveis")
    
    with col2:
        st.markdown("**Critérios:**")
        
        # Days threshold slider
        days_threshold = st.slider(
            "Dias sem movimentação (mínimo)",
            min_value=0,
            max_value=300,
            value=40,
            step=10
        )
        
        # Priority filter
        priority_only = st.checkbox("Apenas Prioridade Alta", value=False)
        
        # Status filter
        if 'situacao_atual' in data_df.columns:
            available_status = sorted([status for status in data_df['situacao_atual'].dropna().unique() if status and str(status) != 'nan'])
            selected_status = st.multiselect(
                "Situação Atual",
                options=available_status,
                default=available_status[:5] if len(available_status) > 5 else available_status
            )
        else:
            selected_status = []
    
    with col3:
        # Quick stats
        st.markdown("**Resumo Rápido:**")
        
        if 'dias_sem_movimentacao' in data_df.columns:
            total_ops = len(data_df)
            ops_40_plus = len(data_df[data_df['dias_sem_movimentacao'] > 40])
            ops_60_plus = len(data_df[data_df['dias_sem_movimentacao'] > 60])
            
            col3a, col3b, col3c = st.columns(3)
            with col3a:
                st.metric("Total", f"{total_ops:,}")
            with col3b:
                st.metric("> 40 dias", f"{ops_40_plus:,}", delta=f"{(ops_40_plus/total_ops*100):.1f}%")
            with col3c:
                st.metric("> 60 dias", f"{ops_60_plus:,}", delta=f"{(ops_60_plus/total_ops*100):.1f}%")
    
    st.markdown("---")
    
    # Apply filters
    filtered_df = data_df.copy()
    
    # Filter by selected actions
    if selected_actions and 'etiquetas' in data_df.columns:
        filtered_df = filtered_df[filtered_df['etiquetas'].isin(selected_actions)]
    
    # Filter by days threshold
    if 'dias_sem_movimentacao' in data_df.columns:
        filtered_df = filtered_df[filtered_df['dias_sem_movimentacao'] >= days_threshold]
    
    # Filter by priority (>60 days)
    if priority_only and 'dias_sem_movimentacao' in data_df.columns:
        filtered_df = filtered_df[filtered_df['dias_sem_movimentacao'] > 60]
    
    # Filter by status
    if selected_status and 'situacao_atual' in data_df.columns:
        filtered_df = filtered_df[filtered_df['situacao_atual'].isin(selected_status)]
    
    # Main visualizations
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader(f"Operações com mais de {days_threshold} dias sem movimentação")
        
        if 'repassador' in filtered_df.columns and not filtered_df.empty:
            # Bar chart: Operations by ministry/agency
            agency_counts = filtered_df.groupby('repassador')['dias_sem_movimentacao'].agg(['count', 'mean']).reset_index()
            agency_counts.columns = ['repassador', 'total_operacoes', 'media_dias']
            agency_counts = agency_counts.sort_values('total_operacoes', ascending=True).tail(10)
            
            fig_bar = px.bar(
                agency_counts,
                x='total_operacoes',
                y='repassador',
                orientation='h',
                title=f"Operações por Ministério/Repassador (>{days_threshold} dias)",
                labels={'total_operacoes': 'Número de Operações', 'repassador': 'Repassador'},
                hover_data={'media_dias': ':.1f'}
            )
            fig_bar.update_layout(height=400)
            st.plotly_chart(fig_bar, use_container_width=True)
            
            # Additional bar chart: Average days by agency
            st.subheader("Média de Dias sem Movimentação por Repassador")
            
            avg_days_agency = filtered_df.groupby('repassador')['dias_sem_movimentacao'].mean().sort_values(ascending=False).head(10)
            
            fig_avg = px.bar(
                x=avg_days_agency.values,
                y=avg_days_agency.index,
                orientation='h',
                title="Média de Dias sem Movimentação",
                labels={'x': 'Média de Dias', 'y': 'Repassador'}
            )
            fig_avg.update_layout(height=300)
            st.plotly_chart(fig_avg, use_container_width=True)
        else:
            st.info("Dados de repassador não disponíveis ou nenhuma operação atende aos critérios")
    
    with col2:
        # Status breakdown pie charts
        st.subheader("Categorização da Situação")
        
        # Pie chart 1: By current situation
        if 'situacao_atual' in filtered_df.columns and not filtered_df.empty:
            situation_counts = filtered_df['situacao_atual'].value_counts().head(5)
            
            if not situation_counts.empty:
                fig_pie1 = px.pie(
                    values=situation_counts.values,
                    names=situation_counts.index,
                    title="Por Situação Atual"
                )
                fig_pie1.update_layout(height=250, showlegend=False)
                st.plotly_chart(fig_pie1, use_container_width=True)
        
        # Pie chart 2: By action tags
        if 'etiquetas' in filtered_df.columns and not filtered_df.empty:
            etiqueta_counts = filtered_df['etiquetas'].value_counts().head(5)
            
            if not etiqueta_counts.empty:
                fig_pie2 = px.pie(
                    values=etiqueta_counts.values,
                    names=etiqueta_counts.index,
                    title="Por Tipo de Ação"
                )
                fig_pie2.update_layout(height=250, showlegend=False)
                st.plotly_chart(fig_pie2, use_container_width=True)
        
        # Pie chart 3: By region
        if 'gigov_regov' in filtered_df.columns and not filtered_df.empty:
            region_counts = filtered_df['gigov_regov'].value_counts().head(5)
            
            if not region_counts.empty:
                fig_pie3 = px.pie(
                    values=region_counts.values,
                    names=region_counts.index,
                    title="Por Região"
                )
                fig_pie3.update_layout(height=250, showlegend=False)
                st.plotly_chart(fig_pie3, use_container_width=True)
    
    # Top municipalities table
    st.subheader("🏙️ Municípios com Mais Operações Pendentes")
    
    if 'municipio_beneficiado' in filtered_df.columns and not filtered_df.empty:
        municipality_summary = filtered_df.groupby(['municipio_beneficiado', 'uf']).agg({
            'operacao': 'count',
            'dias_sem_movimentacao': ['mean', 'max'],
            'valor_empenhado': 'sum' if 'valor_empenhado' in filtered_df.columns else 'count'
        }).reset_index()
        
        # Flatten column names
        municipality_summary.columns = ['Município', 'UF', 'Total Operações', 'Média Dias', 'Máx Dias', 'Valor Total (R$)']
        municipality_summary = municipality_summary.sort_values('Total Operações', ascending=False).head(15)
        
        # Format the table
        if 'Valor Total (R$)' in municipality_summary.columns:
            municipality_summary['Valor Total (R$)'] = municipality_summary['Valor Total (R$)'].apply(format_currency)
        municipality_summary['Média Dias'] = municipality_summary['Média Dias'].round(1)
        
        st.dataframe(
            municipality_summary,
            use_container_width=True,
            height=400
        )
    else:
        st.info("Dados de município não disponíveis")
    
    # Detailed operations table
    st.subheader("📋 Operações Detalhadas que Precisam de Ação")
    
    if not filtered_df.empty:
        # Select relevant columns for display
        display_columns = ['operacao', 'uf', 'municipio_beneficiado', 'repassador', 'dias_sem_movimentacao']
        
        if 'situacao_atual' in filtered_df.columns:
            display_columns.append('situacao_atual')
        if 'etiquetas' in filtered_df.columns:
            display_columns.append('etiquetas')
        if 'valor_empenhado' in filtered_df.columns:
            display_columns.append('valor_empenhado')
        
        # Filter columns that exist
        available_display_columns = [col for col in display_columns if col in filtered_df.columns]
        
        display_df = filtered_df[available_display_columns].copy()
        display_df = display_df.sort_values('dias_sem_movimentacao', ascending=False)
        
        # Rename columns for better display
        column_renames = {
            'operacao': 'Operação',
            'uf': 'UF',
            'municipio_beneficiado': 'Município',
            'repassador': 'Repassador',
            'dias_sem_movimentacao': 'Dias sem Movimento',
            'situacao_atual': 'Situação Atual',
            'etiquetas': 'Tipo de Ação',
            'valor_empenhado': 'Valor Empenhado (R$)'
        }
        
        display_df = display_df.rename(columns=column_renames)
        
        # Format currency if present
        if 'Valor Empenhado (R$)' in display_df.columns:
            display_df['Valor Empenhado (R$)'] = display_df['Valor Empenhado (R$)'].apply(format_currency)
        
        # Show summary stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Operações Filtradas", f"{len(display_df):,}")
        with col2:
            if 'Dias sem Movimento' in display_df.columns:
                avg_days = display_df['Dias sem Movimento'].mean()
                st.metric("Média de Dias", f"{avg_days:.1f}")
        with col3:
            if 'Valor Empenhado (R$)' in display_df.columns:
                total_value = filtered_df['valor_empenhado'].sum()
                st.metric("Valor Total", format_currency(total_value))
        with col4:
            st.metric("Municípios Únicos", f"{filtered_df['municipio_beneficiado'].nunique()}" if 'municipio_beneficiado' in filtered_df.columns else "N/A")
        
        st.dataframe(
            display_df.head(50),  # Show top 50 records
            use_container_width=True,
            height=400
        )
        
        if len(display_df) > 50:
            st.info(f"Mostrando 50 de {len(display_df)} operações. Use os filtros para refinar a seleção.")
    else:
        st.warning("⚠️ Nenhuma operação atende aos critérios selecionados")

def suspensivas_details(df, suspensivas_df):
    """Suspensivas Details - Screen 3 from Power BI"""
    st.subheader("📋 Detalhes das Operações - Suspensivas")
    
    # Use suspensivas view if available, otherwise main df
    data_df = suspensivas_df if not suspensivas_df.empty else df
    
    if data_df.empty:
        st.warning("⚠️ Nenhum dado de suspensivas disponível")
        return
    
    # Date range filters (top section)
    st.subheader("📅 Filtros de Data")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("**Vencimento da Suspensiva:**")
        if 'vencimento_da_suspensiva' in data_df.columns:
            min_date = data_df['vencimento_da_suspensiva'].min()
            max_date = data_df['vencimento_da_suspensiva'].max()
            
            if pd.notna(min_date) and pd.notna(max_date):
                venc_start = st.date_input(
                    "Data início",
                    value=min_date,
                    min_value=min_date,
                    max_value=max_date,
                    key="venc_start"
                )
                venc_end = st.date_input(
                    "Data fim",
                    value=max_date,
                    min_value=min_date,
                    max_value=max_date,
                    key="venc_end"
                )
            else:
                st.info("Dados de vencimento não disponíveis")
                venc_start = venc_end = None
        else:
            st.info("Coluna vencimento não encontrada")
            venc_start = venc_end = None
    
    with col2:
        st.markdown("**Cumprimento da Suspensiva:**")
        if 'data_cumprimento_suspensiva' in data_df.columns:
            cumpr_dates = data_df['data_cumprimento_suspensiva'].dropna()
            if not cumpr_dates.empty:
                min_cumpr = cumpr_dates.min()
                max_cumpr = cumpr_dates.max()
                
                cumpr_start = st.date_input(
                    "Data início",
                    value=min_cumpr,
                    min_value=min_cumpr,
                    max_value=max_cumpr,
                    key="cumpr_start"
                )
                cumpr_end = st.date_input(
                    "Data fim",
                    value=max_cumpr,
                    min_value=min_cumpr,
                    max_value=max_cumpr,
                    key="cumpr_end"
                )
            else:
                st.info("Nenhuma data de cumprimento disponível")
                cumpr_start = cumpr_end = None
        else:
            st.info("Coluna cumprimento não encontrada")
            cumpr_start = cumpr_end = None
    
    with col3:
        st.markdown("**Retirada da Suspensiva:**")
        if 'data_retirada_suspensiva' in data_df.columns:
            retirada_dates = data_df['data_retirada_suspensiva'].dropna()
            if not retirada_dates.empty:
                min_ret = retirada_dates.min()
                max_ret = retirada_dates.max()
                
                ret_start = st.date_input(
                    "Data início",
                    value=min_ret,
                    min_value=min_ret,
                    max_value=max_ret,
                    key="ret_start"
                )
                ret_end = st.date_input(
                    "Data fim",
                    value=max_ret,
                    min_value=min_ret,
                    max_value=max_ret,
                    key="ret_end"
                )
            else:
                st.info("Nenhuma data de retirada disponível")
                ret_start = ret_end = None
        else:
            st.info("Coluna retirada não encontrada")
            ret_start = ret_end = None
    
    with col4:
        st.markdown("**Filtros Adicionais:**")
        
        # Status filter
        if 'situacao_da_analise_suspensiva' in data_df.columns:
            available_status = sorted([status for status in data_df['situacao_da_analise_suspensiva'].dropna().unique() if status and str(status) != 'nan'])
            selected_status = st.multiselect(
                "Status da Análise",
                options=available_status,
                default=available_status
            )
        else:
            selected_status = []
        
        # Days filter
        if 'dias_sem_movimentacao' in data_df.columns:
            max_days = int(data_df['dias_sem_movimentacao'].max()) if pd.notna(data_df['dias_sem_movimentacao'].max()) else 365
            days_filter = st.slider(
                "Máx. dias sem movimento",
                min_value=0,
                max_value=max_days,
                value=max_days,
                step=10
            )
        else:
            days_filter = None
    
    st.markdown("---")
    
    # Apply date filters
    filtered_df = data_df.copy()
    
    # Filter by vencimento dates
    if venc_start and venc_end and 'vencimento_da_suspensiva' in data_df.columns:
        venc_start_ts = pd.Timestamp(venc_start)
        venc_end_ts = pd.Timestamp(venc_end)
        filtered_df = filtered_df[
            (pd.to_datetime(filtered_df['vencimento_da_suspensiva']) >= venc_start_ts) &
            (pd.to_datetime(filtered_df['vencimento_da_suspensiva']) <= venc_end_ts)
        ]
    
    # Filter by cumprimento dates
    if cumpr_start and cumpr_end and 'data_cumprimento_suspensiva' in data_df.columns:
        cumpr_start_ts = pd.Timestamp(cumpr_start)
        cumpr_end_ts = pd.Timestamp(cumpr_end)
        filtered_df = filtered_df[
            (pd.to_datetime(filtered_df['data_cumprimento_suspensiva']) >= cumpr_start_ts) &
            (pd.to_datetime(filtered_df['data_cumprimento_suspensiva']) <= cumpr_end_ts)
        ]
    
    # Filter by retirada dates
    if ret_start and ret_end and 'data_retirada_suspensiva' in data_df.columns:
        ret_start_ts = pd.Timestamp(ret_start)
        ret_end_ts = pd.Timestamp(ret_end)
        filtered_df = filtered_df[
            (pd.to_datetime(filtered_df['data_retirada_suspensiva']) >= ret_start_ts) &
            (pd.to_datetime(filtered_df['data_retirada_suspensiva']) <= ret_end_ts)
        ]
    
    # Filter by status
    if selected_status and 'situacao_da_analise_suspensiva' in data_df.columns:
        filtered_df = filtered_df[filtered_df['situacao_da_analise_suspensiva'].isin(selected_status)]
    
    # Filter by days
    if days_filter is not None and 'dias_sem_movimentacao' in data_df.columns:
        filtered_df = filtered_df[filtered_df['dias_sem_movimentacao'] <= days_filter]
    
    # Summary metrics
    st.subheader("📊 Resumo das Operações Filtradas")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total de Operações", f"{len(filtered_df):,}")
    
    with col2:
        if 'valor_empenhado' in filtered_df.columns:
            total_value = filtered_df['valor_empenhado'].sum()
            st.metric("Valor Total", format_currency(total_value))
    
    with col3:
        if 'dias_sem_movimentacao' in filtered_df.columns:
            avg_days = filtered_df['dias_sem_movimentacao'].mean()
            st.metric("Média Dias sem Movimento", f"{avg_days:.1f}" if pd.notna(avg_days) else "N/A")
    
    with col4:
        # Count operations with suspensiva removed
        if 'data_retirada_suspensiva' in filtered_df.columns:
            retiradas = filtered_df['data_retirada_suspensiva'].notna().sum()
            st.metric("Suspensivas Retiradas", f"{retiradas:,}")
    
    with col5:
        # Count overdue operations
        if 'vencimento_da_suspensiva' in filtered_df.columns:
            today = pd.Timestamp.now()
            overdue = len(filtered_df[
                (pd.to_datetime(filtered_df['vencimento_da_suspensiva']) < today) &
                (filtered_df['data_retirada_suspensiva'].isna())
            ])
            st.metric("Vencidas", f"{overdue:,}", delta="🚨" if overdue > 0 else "✅")
    
    # Detailed operations table
    st.subheader("📋 Tabela Detalhada de Operações")
    
    if not filtered_df.empty:
        # Define columns to display (matching Power BI layout)
        detail_columns = [
            'operacao',
            'uf',
            'municipio_beneficiado',
            'repassador',
            'vencimento_da_suspensiva',
            'data_cumprimento_suspensiva',
            'data_retirada_suspensiva',
            'dias_sem_movimentacao',
            'situacao_da_analise_suspensiva',
            'situacao_atual',
            'etiquetas'
        ]
        
        if 'valor_empenhado' in filtered_df.columns:
            detail_columns.append('valor_empenhado')
        
        # Filter to only existing columns
        available_detail_columns = [col for col in detail_columns if col in filtered_df.columns]
        
        display_df = filtered_df[available_detail_columns].copy()
        
        # Sort by most critical first (highest days without movement)
        if 'dias_sem_movimentacao' in display_df.columns:
            display_df = display_df.sort_values('dias_sem_movimentacao', ascending=False)
        
        # Format columns for better display
        column_renames = {
            'operacao': 'Operação',
            'uf': 'UF',
            'municipio_beneficiado': 'Município',
            'repassador': 'Repassador',
            'vencimento_da_suspensiva': 'Vencimento',
            'data_cumprimento_suspensiva': 'Data Cumprimento',
            'data_retirada_suspensiva': 'Data Retirada',
            'dias_sem_movimentacao': 'Dias sem Movimento',
            'situacao_da_analise_suspensiva': 'Status Análise',
            'situacao_atual': 'Situação Atual',
            'etiquetas': 'Tipo de Ação',
            'valor_empenhado': 'Valor Empenhado (R$)'
        }
        
        display_df = display_df.rename(columns=column_renames)
        
        # Format currency
        if 'Valor Empenhado (R$)' in display_df.columns:
            display_df['Valor Empenhado (R$)'] = display_df['Valor Empenhado (R$)'].apply(format_currency)
        
        # Format dates
        date_columns = ['Vencimento', 'Data Cumprimento', 'Data Retirada']
        for col in date_columns:
            if col in display_df.columns:
                display_df[col] = pd.to_datetime(display_df[col]).dt.strftime('%d/%m/%Y')
                display_df[col] = display_df[col].replace('NaT', '')
        
        # Add color coding for critical operations
        def highlight_critical(row):
            if 'Dias sem Movimento' in row.index:
                days = row['Dias sem Movimento']
                if pd.isna(days):
                    return [''] * len(row)
                elif days > 90:
                    return ['background-color: #ffcccc'] * len(row)  # Red for >90 days
                elif days > 60:
                    return ['background-color: #fff3cd'] * len(row)  # Yellow for >60 days
                elif days > 40:
                    return ['background-color: #d1ecf1'] * len(row)  # Blue for >40 days
            return [''] * len(row)
        
        # Search functionality
        st.markdown("**🔍 Buscar operações:**")
        search_term = st.text_input("Digite número da operação, município ou repassador:", key="search_operations")
        
        if search_term:
            # Filter by search term
            search_columns = ['Operação', 'Município', 'Repassador', 'Situação Atual']
            search_mask = pd.Series([False] * len(display_df))
            
            for col in search_columns:
                if col in display_df.columns:
                    search_mask |= display_df[col].astype(str).str.contains(search_term, case=False, na=False)
            
            display_df = display_df[search_mask]
        
        # Pagination
        items_per_page = st.selectbox("Operações por página:", [25, 50, 100, 200], index=1, key="pagination_details")
        total_pages = len(display_df) // items_per_page + (1 if len(display_df) % items_per_page > 0 else 0)
        
        if total_pages > 1:
            page = st.selectbox(f"Página (1 de {total_pages}):", range(1, total_pages + 1), key="page_selector")
            start_idx = (page - 1) * items_per_page
            end_idx = start_idx + items_per_page
            paginated_df = display_df.iloc[start_idx:end_idx]
        else:
            paginated_df = display_df.head(items_per_page)
        
        # Display the table with styling
        styled_df = paginated_df.style.apply(highlight_critical, axis=1)
        st.dataframe(
            styled_df,
            use_container_width=True,
            height=600
        )
        
        # Export functionality
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📥 Exportar Dados Filtrados (CSV)", key="export_csv"):
                csv = display_df.to_csv(index=False)
                st.download_button(
                    label="💾 Download CSV",
                    data=csv,
                    file_name=f"suspensivas_detalhes_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            st.info(f"📊 Mostrando {len(paginated_df)} de {len(display_df)} operações")
        
        with col3:
            if len(display_df) != len(filtered_df):
                st.info(f"🔍 {len(display_df)} operações encontradas na busca")
    
    else:
        st.warning("⚠️ Nenhuma operação encontrada com os filtros aplicados")
        st.info("💡 Dica: Ajuste os filtros de data ou status para ver mais operações")

def suspensivas_regional(df, suspensivas_df):
    """Suspensivas Regional - Screen 4 from Power BI"""
    st.subheader("🗺️ Análise Regional de Suspensivas")
    
    # Use suspensivas view if available, otherwise main df
    data_df = suspensivas_df if not suspensivas_df.empty else df
    
    if data_df.empty:
        st.warning("⚠️ Nenhum dado de suspensivas disponível")
        return
    
    # Regional overview metrics
    st.subheader("📊 Visão Geral Regional")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_ops = len(data_df)
        st.metric("Total de Operações", f"{total_ops:,}")
    
    with col2:
        if 'gigov_regov' in data_df.columns:
            total_regioes = data_df['gigov_regov'].nunique()
            st.metric("Regiões (GIGOV)", f"{total_regioes}")
    
    with col3:
        if 'uf' in data_df.columns:
            total_estados = data_df['uf'].nunique()
            st.metric("Estados", f"{total_estados}")
    
    with col4:
        if 'municipio_beneficiado' in data_df.columns:
            total_municipios = data_df['municipio_beneficiado'].nunique()
            st.metric("Municípios", f"{total_municipios}")
    
    with col5:
        if 'data_retirada_suspensiva' in data_df.columns:
            suspensivas_retiradas = data_df['data_retirada_suspensiva'].notna().sum()
            st.metric("Suspensivas Retiradas", f"{suspensivas_retiradas:,}")
    
    # Regional breakdown analysis
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📈 Retirada de Suspensivas por Região (GIGOV)")
        
        if 'gigov_regov' in data_df.columns and 'data_retirada_suspensiva' in data_df.columns:
            # Create regional summary
            regional_summary = data_df.groupby('gigov_regov').agg({
                'operacao': 'count',
                'data_retirada_suspensiva': lambda x: x.notna().sum(),
                'valor_empenhado': 'sum' if 'valor_empenhado' in data_df.columns else lambda x: 0,
                'dias_sem_movimentacao': 'mean' if 'dias_sem_movimentacao' in data_df.columns else lambda x: 0
            }).reset_index()
            
            regional_summary.columns = ['Região', 'Total Operações', 'Suspensivas Retiradas', 'Valor Total', 'Média Dias sem Movimento']
            
            # Calculate completion rate
            regional_summary['Taxa Conclusão (%)'] = (
                regional_summary['Suspensivas Retiradas'] / 
                regional_summary['Total Operações'] * 100
            ).round(1)
            
            # Sort by completion rate
            regional_summary = regional_summary.sort_values('Suspensivas Retiradas', ascending=True)
            
            # Bar chart of suspensivas retiradas by region
            fig_regional = px.bar(
                regional_summary,
                x='Suspensivas Retiradas',
                y='Região',
                orientation='h',
                title="Suspensivas Retiradas por Região GIGOV",
                labels={'Suspensivas Retiradas': 'Quantidade de Suspensivas Retiradas', 'Região': 'Região GIGOV'},
                color='Taxa Conclusão (%)',
                color_continuous_scale='RdYlGn'
            )
            fig_regional.update_layout(height=400)
            st.plotly_chart(fig_regional, use_container_width=True)
        else:
            st.info("Dados de região ou datas de retirada não disponíveis")
    
    with col2:
        st.subheader("🎯 Performance Regional")
        
        if 'gigov_regov' in data_df.columns:
            # Regional performance table
            if 'regional_summary' in locals():
                # Format currency
                if 'Valor Total' in regional_summary.columns:
                    regional_summary['Valor Total (Formatado)'] = regional_summary['Valor Total'].apply(format_currency)
                
                # Display formatted table
                display_regional = regional_summary[['Região', 'Total Operações', 'Suspensivas Retiradas', 'Taxa Conclusão (%)']].copy()
                
                st.dataframe(
                    display_regional,
                    use_container_width=True,
                    height=350
                )
            
            # Regional distribution pie chart
            st.subheader("Distribuição por Região")
            
            region_counts = data_df['gigov_regov'].value_counts()
            
            fig_pie_region = px.pie(
                values=region_counts.values,
                names=region_counts.index,
                title="Operações por Região"
            )
            fig_pie_region.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig_pie_region, use_container_width=True)
    
    # Timeline analysis
    st.subheader("📅 Evolução Temporal das Suspensivas")
    
    if 'data_retirada_suspensiva' in data_df.columns:
        # Filter data with valid retirada dates
        timeline_df = data_df[data_df['data_retirada_suspensiva'].notna()].copy()
        
        if not timeline_df.empty:
            # Convert to datetime and extract year-month
            timeline_df['data_retirada_suspensiva'] = pd.to_datetime(timeline_df['data_retirada_suspensiva'])
            timeline_df['ano_mes'] = timeline_df['data_retirada_suspensiva'].dt.to_period('M')
            
            # Time series analysis
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Evolução Mensal - Retirada de Suspensivas")
                
                # Monthly timeline
                monthly_timeline = timeline_df.groupby('ano_mes').size().reset_index()
                monthly_timeline.columns = ['Mês', 'Suspensivas Retiradas']
                monthly_timeline['Mês'] = monthly_timeline['Mês'].astype(str)
                
                fig_timeline = px.line(
                    monthly_timeline,
                    x='Mês',
                    y='Suspensivas Retiradas',
                    title="Suspensivas Retiradas por Mês",
                    markers=True
                )
                fig_timeline.update_layout(height=350)
                fig_timeline.update_xaxes(tickangle=45)
                st.plotly_chart(fig_timeline, use_container_width=True)
            
            with col2:
                st.subheader("Evolução por Região")
                
                # Timeline by region
                if 'gigov_regov' in timeline_df.columns:
                    regional_timeline = timeline_df.groupby(['ano_mes', 'gigov_regov']).size().reset_index()
                    regional_timeline.columns = ['Mês', 'Região', 'Suspensivas Retiradas']
                    regional_timeline['Mês'] = regional_timeline['Mês'].astype(str)
                    
                    # Show only top 5 regions for clarity
                    top_regions = timeline_df['gigov_regov'].value_counts().head(5).index
                    regional_timeline_filtered = regional_timeline[regional_timeline['Região'].isin(top_regions)]
                    
                    fig_regional_timeline = px.line(
                        regional_timeline_filtered,
                        x='Mês',
                        y='Suspensivas Retiradas',
                        color='Região',
                        title="Evolução por Região (Top 5)",
                        markers=True
                    )
                    fig_regional_timeline.update_layout(height=350, legend=dict(orientation="h", yanchor="bottom", y=1.02))
                    fig_regional_timeline.update_xaxes(tickangle=45)
                    st.plotly_chart(fig_regional_timeline, use_container_width=True)
        else:
            st.info("Nenhuma suspensiva com data de retirada encontrada para análise temporal")
    
    # State-level analysis
    st.subheader("🗺️ Análise por Estado")
    
    if 'uf' in data_df.columns:
        # State performance summary
        state_summary = data_df.groupby('uf').agg({
            'operacao': 'count',
            'data_retirada_suspensiva': lambda x: x.notna().sum(),
            'dias_sem_movimentacao': 'mean' if 'dias_sem_movimentacao' in data_df.columns else lambda x: 0,
            'valor_empenhado': 'sum' if 'valor_empenhado' in data_df.columns else lambda x: 0
        }).reset_index()
        
        state_summary.columns = ['UF', 'Total Operações', 'Suspensivas Retiradas', 'Média Dias sem Movimento', 'Valor Total']
        
        # Calculate metrics
        state_summary['Taxa Conclusão (%)'] = (
            state_summary['Suspensivas Retiradas'] / 
            state_summary['Total Operações'] * 100
        ).round(1)
        
        # Sort by total operations
        state_summary = state_summary.sort_values('Total Operações', ascending=False)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Top states chart
            st.subheader("Estados com Mais Operações")
            
            top_states = state_summary.head(15)
            
            fig_states = px.bar(
                top_states,
                x='Total Operações',
                y='UF',
                orientation='h',
                title="Top 15 Estados por Número de Operações",
                color='Taxa Conclusão (%)',
                color_continuous_scale='RdYlGn',
                labels={'Total Operações': 'Número de Operações', 'UF': 'Estado'}
            )
            fig_states.update_layout(height=500)
            st.plotly_chart(fig_states, use_container_width=True)
        
        with col2:
            # State performance metrics
            st.subheader("Performance dos Estados")
            
            # Top performing states by completion rate
            top_completion = state_summary[state_summary['Total Operações'] >= 5].nlargest(10, 'Taxa Conclusão (%)')
            
            if not top_completion.empty:
                st.write("**🏆 Melhores Taxas de Conclusão:**")
                
                for _, row in top_completion.iterrows():
                    st.markdown(f"""
                    **{row['UF']}**: {row['Taxa Conclusão (%)']:.1f}%  
                    ({row['Suspensivas Retiradas']:.0f}/{row['Total Operações']:.0f} operações)
                    """)
            
            # States needing attention
            needs_attention = state_summary[
                (state_summary['Total Operações'] >= 5) & 
                (state_summary['Taxa Conclusão (%)'] < 20)
            ].nlargest(5, 'Total Operações')
            
            if not needs_attention.empty:
                st.write("**⚠️ Estados que Precisam de Atenção:**")
                
                for _, row in needs_attention.iterrows():
                    st.markdown(f"""
                    **{row['UF']}**: {row['Taxa Conclusão (%)']:.1f}%  
                    ({row['Total Operações']:.0f} operações, {row['Média Dias sem Movimento']:.0f} dias média)
                    """)
    
    # Detailed regional table
    st.subheader("📊 Tabela Detalhada por Região e Estado")
    
    if 'gigov_regov' in data_df.columns and 'uf' in data_df.columns:
        # Regional and state breakdown
        detailed_summary = data_df.groupby(['gigov_regov', 'uf']).agg({
            'operacao': 'count',
            'data_retirada_suspensiva': lambda x: x.notna().sum(),
            'municipio_beneficiado': 'nunique',
            'valor_empenhado': 'sum' if 'valor_empenhado' in data_df.columns else lambda x: 0,
            'dias_sem_movimentacao': 'mean' if 'dias_sem_movimentacao' in data_df.columns else lambda x: 0
        }).reset_index()
        
        detailed_summary.columns = ['Região', 'UF', 'Total Operações', 'Suspensivas Retiradas', 'Municípios', 'Valor Total', 'Média Dias']
        
        # Calculate completion rate
        detailed_summary['Taxa Conclusão (%)'] = (
            detailed_summary['Suspensivas Retiradas'] / 
            detailed_summary['Total Operações'] * 100
        ).round(1)
        
        # Format currency
        if 'Valor Total' in detailed_summary.columns:
            detailed_summary['Valor Total (Formatado)'] = detailed_summary['Valor Total'].apply(format_currency)
        
        # Sort by region and total operations
        detailed_summary = detailed_summary.sort_values(['Região', 'Total Operações'], ascending=[True, False])
        
        # Display table with formatting
        display_detailed = detailed_summary[[
            'Região', 'UF', 'Total Operações', 'Suspensivas Retiradas', 
            'Taxa Conclusão (%)', 'Municípios', 'Valor Total (Formatado)', 'Média Dias'
        ]].copy()
        
        display_detailed.columns = [
            'Região GIGOV', 'UF', 'Total Operações', 'Suspensivas Retiradas',
            'Taxa Conclusão (%)', 'Municípios', 'Valor Total', 'Média Dias sem Movimento'
        ]
        
        # Add color coding for completion rates
        def highlight_completion_rate(row):
            completion_rate = row['Taxa Conclusão (%)']
            if pd.isna(completion_rate):
                return [''] * len(row)
            elif completion_rate >= 50:
                return ['background-color: #d4edda'] * len(row)  # Green for good performance
            elif completion_rate >= 25:
                return ['background-color: #fff3cd'] * len(row)  # Yellow for moderate performance
            else:
                return ['background-color: #f8d7da'] * len(row)  # Red for needs attention
        
        styled_detailed = display_detailed.style.apply(highlight_completion_rate, axis=1)
        
        st.dataframe(
            styled_detailed,
            use_container_width=True,
            height=400
        )
        
        # Export functionality
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Exportar Análise Regional (CSV)"):
                csv = display_detailed.to_csv(index=False)
                st.download_button(
                    label="💾 Download CSV",
                    data=csv,
                    file_name=f"analise_regional_suspensivas_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            st.info(f"📊 Total: {len(display_detailed)} combinações região/estado")
    
    else:
        st.info("Dados de região ou estado não disponíveis para análise detalhada")

def suspensivas_performance(df, suspensivas_df):
    """Suspensivas Performance - Screen 5 from Power BI"""
    st.subheader("📈 Análise de Desempenho - Suspensivas")
    
    # Use suspensivas view if available, otherwise main df
    data_df = suspensivas_df if not suspensivas_df.empty else df
    
    if data_df.empty:
        st.warning("⚠️ Nenhum dado de suspensivas disponível")
        return
    
    # Performance overview metrics
    st.subheader("🎯 Indicadores de Desempenho Geral")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_ops = len(data_df)
        st.metric("Total Operações", f"{total_ops:,}")
    
    with col2:
        if 'data_retirada_suspensiva' in data_df.columns:
            completed = data_df['data_retirada_suspensiva'].notna().sum()
            completion_rate = (completed / total_ops * 100) if total_ops > 0 else 0
            st.metric("Taxa Conclusão Geral", f"{completion_rate:.1f}%", delta=f"{completed:,} concluídas")
    
    with col3:
        if 'dias_sem_movimentacao' in data_df.columns:
            avg_days = data_df['dias_sem_movimentacao'].mean()
            st.metric("Média Dias sem Movimento", f"{avg_days:.1f}" if pd.notna(avg_days) else "N/A")
    
    with col4:
        if 'vencimento_da_suspensiva' in data_df.columns:
            today = pd.Timestamp.now()
            overdue = len(data_df[
                (pd.to_datetime(data_df['vencimento_da_suspensiva']) < today) &
                (data_df['data_retirada_suspensiva'].isna())
            ])
            overdue_rate = (overdue / total_ops * 100) if total_ops > 0 else 0
            st.metric("Taxa Vencimento", f"{overdue_rate:.1f}%", delta=f"{overdue:,} vencidas")
    
    with col5:
        if 'valor_empenhado' in data_df.columns:
            total_value = data_df['valor_empenhado'].sum()
            st.metric("Valor Total", format_currency(total_value))
    
    # Performance analysis tabs
    tab1, tab2, tab3 = st.tabs([
        "📊 Por Região", "🏛️ Por Repassador", "⏱️ Tempo de Resposta"
    ])
    
    with tab1:
        performance_by_region(data_df)
    
    with tab2:
        performance_by_agency(data_df)
    
    with tab3:
        response_time_analysis(data_df)

def performance_by_region(data_df):
    """Performance analysis by region"""
    st.subheader("📊 Desempenho por Região GIGOV")
    
    if 'gigov_regov' not in data_df.columns:
        st.info("Dados de região não disponíveis")
        return
    
    # Regional performance calculation
    regional_performance = data_df.groupby('gigov_regov').agg({
        'operacao': 'count',
        'data_retirada_suspensiva': lambda x: x.notna().sum(),
        'data_cumprimento_suspensiva': lambda x: x.notna().sum(),
        'dias_sem_movimentacao': ['mean', 'median', 'max'],
        'valor_empenhado': 'sum' if 'valor_empenhado' in data_df.columns else lambda x: 0,
        'vencimento_da_suspensiva': lambda x: (pd.to_datetime(x) < pd.Timestamp.now()).sum() if x.notna().any() else 0
    }).reset_index()
    
    # Flatten column names
    regional_performance.columns = [
        'Região', 'Total Operações', 'Suspensivas Retiradas', 'Suspensivas Cumpridas',
        'Média Dias', 'Mediana Dias', 'Max Dias', 'Valor Total', 'Operações Vencidas'
    ]
    
    # Calculate performance metrics
    regional_performance['Taxa Retirada (%)'] = (
        regional_performance['Suspensivas Retiradas'] / 
        regional_performance['Total Operações'] * 100
    ).round(2)
    
    regional_performance['Taxa Cumprimento (%)'] = (
        regional_performance['Suspensivas Cumpridas'] / 
        regional_performance['Total Operações'] * 100
    ).round(2)
    
    regional_performance['Taxa Vencimento (%)'] = (
        regional_performance['Operações Vencidas'] / 
        regional_performance['Total Operações'] * 100
    ).round(2)
    
    # Performance classification
    def classify_performance(row):
        retirada_rate = row['Taxa Retirada (%)']
        if retirada_rate >= 50:
            return "🟢 Excelente"
        elif retirada_rate >= 30:
            return "🟡 Bom"
        elif retirada_rate >= 15:
            return "🟠 Regular"
        else:
            return "🔴 Crítico"
    
    regional_performance['Classificação'] = regional_performance.apply(classify_performance, axis=1)
    
    # Sort by completion rate
    regional_performance = regional_performance.sort_values('Taxa Retirada (%)', ascending=False)
    
    # Display performance table
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📋 Tabela de Desempenho Regional")
        
        # Format currency
        if 'Valor Total' in regional_performance.columns:
            regional_performance['Valor Total (Formatado)'] = regional_performance['Valor Total'].apply(format_currency)
        
        # Select display columns
        display_columns = [
            'Região', 'Total Operações', 'Taxa Retirada (%)', 'Taxa Cumprimento (%)',
            'Taxa Vencimento (%)', 'Média Dias', 'Classificação'
        ]
        
        display_regional = regional_performance[display_columns].copy()
        
        # Apply color coding
        def highlight_performance(row):
            classification = row['Classificação']
            if '🟢' in classification:
                return ['background-color: #d4edda'] * len(row)
            elif '🟡' in classification:
                return ['background-color: #fff3cd'] * len(row)
            elif '🟠' in classification:
                return ['background-color: #ffeaa7'] * len(row)
            else:
                return ['background-color: #f8d7da'] * len(row)
        
        styled_regional = display_regional.style.apply(highlight_performance, axis=1)
        
        st.dataframe(
            styled_regional,
            use_container_width=True,
            height=400
        )
    
    with col2:
        st.subheader("🏆 Ranking de Performance")
        
        # Top performers
        st.write("**🥇 Melhores Regiões:**")
        top_regions = regional_performance.head(3)
        
        for i, (_, row) in enumerate(top_regions.iterrows(), 1):
            medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"{i}º"
            st.markdown(f"""
            **{medal} {row['Região']}**  
            Taxa Retirada: {row['Taxa Retirada (%)']:.1f}%  
            ({row['Suspensivas Retiradas']:.0f}/{row['Total Operações']:.0f} operações)
            """)
        
        # Regions needing attention
        st.write("**⚠️ Regiões que Precisam de Atenção:**")
        bottom_regions = regional_performance[regional_performance['Taxa Retirada (%)'] < 25].tail(3)
        
        if not bottom_regions.empty:
            for _, row in bottom_regions.iterrows():
                st.markdown(f"""
                **{row['Região']}**  
                Taxa Retirada: {row['Taxa Retirada (%)']:.1f}%  
                Média Dias: {row['Média Dias']:.0f} dias
                """)
        else:
            st.success("✅ Todas as regiões com desempenho aceitável!")
    
    # Performance visualization
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Comparativo de Taxa de Retirada")
        
        fig_performance = px.bar(
            regional_performance,
            x='Taxa Retirada (%)',
            y='Região',
            orientation='h',
            color='Taxa Retirada (%)',
            color_continuous_scale='RdYlGn',
            title="Taxa de Retirada de Suspensivas por Região",
            labels={'Taxa Retirada (%)': 'Taxa de Retirada (%)', 'Região': 'Região GIGOV'}
        )
        fig_performance.update_layout(height=400)
        st.plotly_chart(fig_performance, use_container_width=True)
    
    with col2:
        st.subheader("Tempo Médio vs. Volume")
        
        fig_scatter = px.scatter(
            regional_performance,
            x='Total Operações',
            y='Média Dias',
            size='Taxa Retirada (%)',
            color='Classificação',
            hover_name='Região',
            title="Volume vs. Tempo Médio de Processamento",
            labels={'Total Operações': 'Número de Operações', 'Média Dias': 'Média de Dias sem Movimento'}
        )
        fig_scatter.update_layout(height=400)
        st.plotly_chart(fig_scatter, use_container_width=True)

def performance_by_agency(data_df):
    """Performance analysis by agency/ministry"""
    st.subheader("🏛️ Desempenho por Repassador/Ministério")
    
    if 'repassador' not in data_df.columns:
        st.info("Dados de repassador não disponíveis")
        return
    
    # Agency performance calculation
    agency_performance = data_df.groupby('repassador').agg({
        'operacao': 'count',
        'data_retirada_suspensiva': lambda x: x.notna().sum(),
        'data_cumprimento_suspensiva': lambda x: x.notna().sum(),
        'dias_sem_movimentacao': ['mean', 'std'],
        'valor_empenhado': 'sum' if 'valor_empenhado' in data_df.columns else lambda x: 0,
        'vencimento_da_suspensiva': lambda x: (pd.to_datetime(x) < pd.Timestamp.now()).sum() if x.notna().any() else 0
    }).reset_index()
    
    # Flatten column names
    agency_performance.columns = [
        'Repassador', 'Total Operações', 'Suspensivas Retiradas', 'Suspensivas Cumpridas',
        'Média Dias', 'Desvio Padrão Dias', 'Valor Total', 'Operações Vencidas'
    ]
    
    # Calculate performance metrics
    agency_performance['Taxa Retirada (%)'] = (
        agency_performance['Suspensivas Retiradas'] / 
        agency_performance['Total Operações'] * 100
    ).round(2)
    
    agency_performance['Taxa Eficiência'] = (
        (agency_performance['Suspensivas Retiradas'] / agency_performance['Média Dias']) * 100
    ).round(2)
    
    # Filter agencies with significant volume (>=5 operations)
    significant_agencies = agency_performance[agency_performance['Total Operações'] >= 5].copy()
    significant_agencies = significant_agencies.sort_values('Taxa Retirada (%)', ascending=False)
    
    # Performance comparison
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("📊 Comparativo de Desempenho por Ministério")
        
        if not significant_agencies.empty:
            # Top 10 agencies chart
            top_agencies = significant_agencies.head(10)
            
            fig_agency = px.bar(
                top_agencies,
                x='Taxa Retirada (%)',
                y='Repassador',
                orientation='h',
                color='Total Operações',
                title="Top 10 Repassadores - Taxa de Retirada de Suspensivas",
                labels={'Taxa Retirada (%)': 'Taxa de Retirada (%)', 'Repassador': 'Ministério/Repassador'}
            )
            fig_agency.update_layout(height=500)
            st.plotly_chart(fig_agency, use_container_width=True)
        else:
            st.info("Nenhum repassador com volume significativo de operações")
    
    with col2:
        st.subheader("🎯 Benchmarks")
        
        if not significant_agencies.empty:
            # Performance statistics
            avg_completion = significant_agencies['Taxa Retirada (%)'].mean()
            top_performer = significant_agencies.iloc[0]
            
            st.metric("Taxa Média do Setor", f"{avg_completion:.1f}%")
            
            st.markdown("**🏆 Melhor Desempenho:**")
            st.markdown(f"""
            **{top_performer['Repassador'][:30]}...**  
            Taxa: {top_performer['Taxa Retirada (%)']:.1f}%  
            Operações: {top_performer['Total Operações']:.0f}  
            Média Dias: {top_performer['Média Dias']:.0f}
            """)
            
            # Efficiency metrics
            if 'Taxa Eficiência' in significant_agencies.columns:
                most_efficient = significant_agencies.nlargest(1, 'Taxa Eficiência').iloc[0]
                st.markdown("**⚡ Mais Eficiente:**")
                st.markdown(f"""
                **{most_efficient['Repassador'][:30]}...**  
                Eficiência: {most_efficient['Taxa Eficiência']:.1f}  
                Média Dias: {most_efficient['Média Dias']:.0f}
                """)
    
    # Detailed agency table
    st.subheader("📋 Tabela Detalhada por Repassador")
    
    # Format and display table
    if 'Valor Total' in agency_performance.columns:
        agency_performance['Valor Total (Formatado)'] = agency_performance['Valor Total'].apply(format_currency)
    
    display_agency = agency_performance[[
        'Repassador', 'Total Operações', 'Suspensivas Retiradas', 'Taxa Retirada (%)',
        'Média Dias', 'Operações Vencidas'
    ]].copy()
    
    # Sort by total operations
    display_agency = display_agency.sort_values('Total Operações', ascending=False)
    
    st.dataframe(
        display_agency,
        use_container_width=True,
        height=400
    )

def response_time_analysis(data_df):
    """Response time and timing analysis"""
    st.subheader("⏱️ Análise de Tempo de Resposta")
    
    # Check for required date columns
    date_columns = ['vencimento_da_suspensiva', 'data_cumprimento_suspensiva', 'data_retirada_suspensiva']
    available_dates = [col for col in date_columns if col in data_df.columns]
    
    if not available_dates:
        st.info("Dados de datas não disponíveis para análise de tempo")
        return
    
    # Calculate timing metrics
    timing_df = data_df.copy()
    
    # Convert date columns
    for col in available_dates:
        timing_df[col] = pd.to_datetime(timing_df[col])
    
    # Calculate cycle times
    if 'vencimento_da_suspensiva' in timing_df.columns and 'data_cumprimento_suspensiva' in timing_df.columns:
        timing_df['dias_vencimento_cumprimento'] = (
            timing_df['data_cumprimento_suspensiva'] - timing_df['vencimento_da_suspensiva']
        ).dt.days
    
    if 'data_cumprimento_suspensiva' in timing_df.columns and 'data_retirada_suspensiva' in timing_df.columns:
        timing_df['dias_cumprimento_retirada'] = (
            timing_df['data_retirada_suspensiva'] - timing_df['data_cumprimento_suspensiva']
        ).dt.days
    
    if 'vencimento_da_suspensiva' in timing_df.columns and 'data_retirada_suspensiva' in timing_df.columns:
        timing_df['dias_ciclo_completo'] = (
            timing_df['data_retirada_suspensiva'] - timing_df['vencimento_da_suspensiva']
        ).dt.days
    
    # Timing analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Distribuição de Tempos de Ciclo")
        
        # Cycle time histogram
        if 'dias_ciclo_completo' in timing_df.columns:
            cycle_times = timing_df['dias_ciclo_completo'].dropna()
            cycle_times = cycle_times[cycle_times >= 0]  # Remove negative values
            
            if not cycle_times.empty:
                fig_hist = px.histogram(
                    cycle_times,
                    nbins=30,
                    title="Distribuição do Tempo de Ciclo (Vencimento → Retirada)",
                    labels={'value': 'Dias para Completar Ciclo', 'count': 'Número de Operações'}
                )
                fig_hist.update_layout(height=350)
                st.plotly_chart(fig_hist, use_container_width=True)
                
                # Timing statistics
                st.markdown("**📈 Estatísticas do Ciclo:**")
                st.markdown(f"""
                - **Média:** {cycle_times.mean():.1f} dias
                - **Mediana:** {cycle_times.median():.1f} dias
                - **P75:** {cycle_times.quantile(0.75):.1f} dias
                - **P90:** {cycle_times.quantile(0.90):.1f} dias
                """)
        else:
            st.info("Dados insuficientes para análise de ciclo completo")
    
    with col2:
        st.subheader("🎯 Metas de Tempo")
        
        # SLA analysis
        if 'dias_sem_movimentacao' in timing_df.columns:
            current_days = timing_df['dias_sem_movimentacao'].dropna()
            
            if not current_days.empty:
                # SLA compliance
                sla_30 = (current_days <= 30).sum() / len(current_days) * 100
                sla_60 = (current_days <= 60).sum() / len(current_days) * 100
                sla_90 = (current_days <= 90).sum() / len(current_days) * 100
                
                st.markdown("**⏰ Compliance com SLA:**")
                st.progress(sla_30/100, text=f"≤ 30 dias: {sla_30:.1f}%")
                st.progress(sla_60/100, text=f"≤ 60 dias: {sla_60:.1f}%")
                st.progress(sla_90/100, text=f"≤ 90 dias: {sla_90:.1f}%")
                
                # Critical operations
                critical = len(current_days[current_days > 90])
                urgent = len(current_days[current_days > 60])
                
                st.markdown("**🚨 Operações Críticas:**")
                st.error(f"Mais de 90 dias: {critical:,} operações")
                st.warning(f"Mais de 60 dias: {urgent:,} operações")
    
    # Timing trends
    if 'data_retirada_suspensiva' in timing_df.columns:
        st.subheader("📈 Tendências Temporais")
        
        # Monthly completion trends
        completed_df = timing_df[timing_df['data_retirada_suspensiva'].notna()].copy()
        
        if not completed_df.empty:
            completed_df['mes_retirada'] = completed_df['data_retirada_suspensiva'].dt.to_period('M')
            
            monthly_trends = completed_df.groupby('mes_retirada').agg({
                'operacao': 'count',
                'dias_ciclo_completo': 'mean' if 'dias_ciclo_completo' in completed_df.columns else lambda x: None
            }).reset_index()
            
            monthly_trends['mes_retirada'] = monthly_trends['mes_retirada'].astype(str)
            monthly_trends.columns = ['Mês', 'Suspensivas Retiradas', 'Tempo Médio Ciclo']
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Volume trend
                fig_volume = px.line(
                    monthly_trends,
                    x='Mês',
                    y='Suspensivas Retiradas',
                    title="Volume Mensal de Suspensivas Retiradas",
                    markers=True
                )
                fig_volume.update_layout(height=300)
                fig_volume.update_xaxes(tickangle=45)
                st.plotly_chart(fig_volume, use_container_width=True)
            
            with col2:
                # Timing trend
                if 'Tempo Médio Ciclo' in monthly_trends.columns and monthly_trends['Tempo Médio Ciclo'].notna().any():
                    fig_timing = px.line(
                        monthly_trends,
                        x='Mês',
                        y='Tempo Médio Ciclo',
                        title="Evolução do Tempo Médio de Ciclo",
                        markers=True
                    )
                    fig_timing.update_layout(height=300)
                    fig_timing.update_xaxes(tickangle=45)
                    st.plotly_chart(fig_timing, use_container_width=True)
                else:
                    st.info("Dados de tempo de ciclo não disponíveis")

def suspensivas_kpis(df, suspensivas_df):
    """Suspensivas KPIs - Screen 6 from Power BI"""
    st.subheader("🎯 Indicadores-Chave de Suspensivas")
    
    # Use suspensivas view if available, otherwise main df
    data_df = suspensivas_df if not suspensivas_df.empty else df
    
    if data_df.empty:
        st.warning("⚠️ Nenhum dado de suspensivas disponível")
        return
    
    # Calculate key timing metrics (matching Power BI KPIs)
    st.subheader("⏱️ Indicadores de Tempo de Ciclo")
    
    # Prepare data for calculations
    kpi_df = data_df.copy()
    
    # Convert date columns
    date_columns = ['vencimento_da_suspensiva', 'data_cumprimento_suspensiva', 'data_retirada_suspensiva']
    for col in date_columns:
        if col in kpi_df.columns:
            kpi_df[col] = pd.to_datetime(kpi_df[col])
    
    # Calculate timing metrics
    timing_metrics = {}
    
    # KPI 1: Average compliance time (Vencimento → Cumprimento)
    if 'vencimento_da_suspensiva' in kpi_df.columns and 'data_cumprimento_suspensiva' in kpi_df.columns:
        compliance_times = (
            kpi_df['data_cumprimento_suspensiva'] - kpi_df['vencimento_da_suspensiva']
        ).dt.days.dropna()
        compliance_times = compliance_times[compliance_times >= 0]  # Remove negative values
        
        if not compliance_times.empty:
            timing_metrics['avg_compliance_time'] = compliance_times.mean()
        else:
            timing_metrics['avg_compliance_time'] = None
    else:
        timing_metrics['avg_compliance_time'] = None
    
    # KPI 2: Average time after compliance (Cumprimento → Retirada)
    if 'data_cumprimento_suspensiva' in kpi_df.columns and 'data_retirada_suspensiva' in kpi_df.columns:
        post_compliance_times = (
            kpi_df['data_retirada_suspensiva'] - kpi_df['data_cumprimento_suspensiva']
        ).dt.days.dropna()
        post_compliance_times = post_compliance_times[post_compliance_times >= 0]
        
        if not post_compliance_times.empty:
            timing_metrics['avg_post_compliance_time'] = post_compliance_times.mean()
        else:
            timing_metrics['avg_post_compliance_time'] = None
    else:
        timing_metrics['avg_post_compliance_time'] = None
    
    # KPI 3: Average total completion time (Vencimento → Retirada)
    if 'vencimento_da_suspensiva' in kpi_df.columns and 'data_retirada_suspensiva' in kpi_df.columns:
        total_completion_times = (
            kpi_df['data_retirada_suspensiva'] - kpi_df['vencimento_da_suspensiva']
        ).dt.days.dropna()
        total_completion_times = total_completion_times[total_completion_times >= 0]
        
        if not total_completion_times.empty:
            timing_metrics['avg_total_completion_time'] = total_completion_times.mean()
        else:
            timing_metrics['avg_total_completion_time'] = None
    else:
        timing_metrics['avg_total_completion_time'] = None
    
    # KPI 4: Current average days without movement
    if 'dias_sem_movimentacao' in kpi_df.columns:
        current_days = kpi_df['dias_sem_movimentacao'].dropna()
        if not current_days.empty:
            timing_metrics['avg_days_without_movement'] = current_days.mean()
        else:
            timing_metrics['avg_days_without_movement'] = None
    else:
        timing_metrics['avg_days_without_movement'] = None
    
    # Display KPI Gauges (3 main KPIs like Power BI)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📊 Tempo Médio para Cumprimento")
        
        compliance_time = timing_metrics['avg_compliance_time']
        if compliance_time is not None:
            # Create gauge chart
            fig_gauge1 = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = compliance_time,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Dias (Vencimento → Cumprimento)"},
                delta = {'reference': 120, 'position': "top"},
                gauge = {
                    'axis': {'range': [None, 300]},
                    'bar': {'color': "#1f77b4"},
                    'steps': [
                        {'range': [0, 60], 'color': "#d4edda"},
                        {'range': [60, 120], 'color': "#fff3cd"},
                        {'range': [120, 300], 'color': "#f8d7da"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 120
                    }
                }
            ))
            fig_gauge1.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_gauge1, use_container_width=True)
            
            st.markdown(f"""
            **Métrica:** {compliance_time:.1f} dias  
            **Meta:** ≤ 120 dias  
            **Status:** {'✅ Dentro da meta' if compliance_time <= 120 else '⚠️ Acima da meta'}
            """)
        else:
            st.info("Dados insuficientes para calcular tempo de cumprimento")
    
    with col2:
        st.markdown("### 📊 Tempo Médio Pós-Cumprimento")
        
        post_compliance_time = timing_metrics['avg_post_compliance_time']
        if post_compliance_time is not None:
            # Create gauge chart
            fig_gauge2 = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = post_compliance_time,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Dias (Cumprimento → Retirada)"},
                delta = {'reference': 60, 'position': "top"},
                gauge = {
                    'axis': {'range': [None, 150]},
                    'bar': {'color': "#ff7f0e"},
                    'steps': [
                        {'range': [0, 30], 'color': "#d4edda"},
                        {'range': [30, 60], 'color': "#fff3cd"},
                        {'range': [60, 150], 'color': "#f8d7da"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 60
                    }
                }
            ))
            fig_gauge2.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_gauge2, use_container_width=True)
            
            st.markdown(f"""
            **Métrica:** {post_compliance_time:.1f} dias  
            **Meta:** ≤ 60 dias  
            **Status:** {'✅ Dentro da meta' if post_compliance_time <= 60 else '⚠️ Acima da meta'}
            """)
        else:
            st.info("Dados insuficientes para calcular tempo pós-cumprimento")
    
    with col3:
        st.markdown("### 📊 Tempo Total de Conclusão")
        
        total_time = timing_metrics['avg_total_completion_time']
        if total_time is not None:
            # Create gauge chart
            fig_gauge3 = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = total_time,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Dias (Vencimento → Retirada)"},
                delta = {'reference': 180, 'position': "top"},
                gauge = {
                    'axis': {'range': [None, 400]},
                    'bar': {'color': "#2ca02c"},
                    'steps': [
                        {'range': [0, 90], 'color': "#d4edda"},
                        {'range': [90, 180], 'color': "#fff3cd"},
                        {'range': [180, 400], 'color': "#f8d7da"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 180
                    }
                }
            ))
            fig_gauge3.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_gauge3, use_container_width=True)
            
            st.markdown(f"""
            **Métrica:** {total_time:.1f} dias  
            **Meta:** ≤ 180 dias  
            **Status:** {'✅ Dentro da meta' if total_time <= 180 else '⚠️ Acima da meta'}
            """)
        else:
            st.info("Dados insuficientes para calcular tempo total")
    
    # Additional KPIs
    st.markdown("---")
    st.subheader("📈 Indicadores Operacionais")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_ops = len(data_df)
        st.metric("Total de Operações", f"{total_ops:,}")
    
    with col2:
        if 'data_retirada_suspensiva' in data_df.columns:
            completed = data_df['data_retirada_suspensiva'].notna().sum()
            completion_rate = (completed / total_ops * 100) if total_ops > 0 else 0
            st.metric("Taxa de Conclusão", f"{completion_rate:.1f}%", delta=f"{completed:,} concluídas")
    
    with col3:
        current_avg_days = timing_metrics['avg_days_without_movement']
        if current_avg_days is not None:
            st.metric("Média Dias sem Movimento", f"{current_avg_days:.1f}", 
                     delta="⚠️ Meta: ≤45" if current_avg_days > 45 else "✅ Dentro da meta")
    
    with col4:
        if 'vencimento_da_suspensiva' in data_df.columns:
            today = pd.Timestamp.now()
            overdue = len(data_df[
                (pd.to_datetime(data_df['vencimento_da_suspensiva']) < today) &
                (data_df['data_retirada_suspensiva'].isna())
            ])
            overdue_rate = (overdue / total_ops * 100) if total_ops > 0 else 0
            st.metric("Operações Vencidas", f"{overdue:,}", delta=f"{overdue_rate:.1f}%")
    
    with col5:
        if 'valor_empenhado' in data_df.columns:
            total_value = data_df['valor_empenhado'].sum()
            completed_value = data_df[data_df['data_retirada_suspensiva'].notna()]['valor_empenhado'].sum()
            value_completion_rate = (completed_value / total_value * 100) if total_value > 0 else 0
            st.metric("Taxa Valor Executado", f"{value_completion_rate:.1f}%", delta=format_currency(completed_value))
    
    # Performance trends
    st.subheader("📊 Tendências de Performance dos KPIs")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Monthly KPI trends
        if 'data_retirada_suspensiva' in data_df.columns:
            monthly_kpis = calculate_monthly_kpis(data_df)
            
            if not monthly_kpis.empty:
                st.subheader("Evolução Mensal dos KPIs")
                
                fig_kpi_trend = px.line(
                    monthly_kpis,
                    x='Mês',
                    y=['Tempo Médio Cumprimento', 'Tempo Médio Pós-Cumprimento', 'Tempo Total Médio'],
                    title="Evolução dos Tempos de Ciclo",
                    labels={'value': 'Dias', 'variable': 'Indicador'}
                )
                fig_kpi_trend.update_layout(height=350)
                fig_kpi_trend.update_xaxes(tickangle=45)
                st.plotly_chart(fig_kpi_trend, use_container_width=True)
    
    with col2:
        # SLA compliance over time
        if 'data_retirada_suspensiva' in data_df.columns:
            sla_trends = calculate_sla_trends(data_df)
            
            if not sla_trends.empty:
                st.subheader("Evolução do Compliance SLA")
                
                fig_sla_trend = px.line(
                    sla_trends,
                    x='Mês',
                    y=['SLA 30 dias (%)', 'SLA 60 dias (%)', 'SLA 90 dias (%)'],
                    title="Compliance com SLA ao Longo do Tempo",
                    labels={'value': 'Percentual (%)', 'variable': 'SLA'}
                )
                fig_sla_trend.update_layout(height=350)
                fig_sla_trend.update_xaxes(tickangle=45)
                st.plotly_chart(fig_sla_trend, use_container_width=True)
    
    # KPI comparison by region/agency
    st.subheader("🎯 Comparativo de KPIs por Segmento")
    
    tab1, tab2 = st.tabs(["Por Região", "Por Repassador"])
    
    with tab1:
        kpi_by_region(data_df, timing_metrics)
    
    with tab2:
        kpi_by_agency(data_df, timing_metrics)

def calculate_monthly_kpis(data_df):
    """Calculate monthly KPI trends"""
    try:
        # Filter completed operations
        completed_df = data_df[data_df['data_retirada_suspensiva'].notna()].copy()
        
        if completed_df.empty:
            return pd.DataFrame()
        
        # Convert dates
        completed_df['data_retirada_suspensiva'] = pd.to_datetime(completed_df['data_retirada_suspensiva'])
        completed_df['vencimento_da_suspensiva'] = pd.to_datetime(completed_df['vencimento_da_suspensiva'])
        completed_df['data_cumprimento_suspensiva'] = pd.to_datetime(completed_df['data_cumprimento_suspensiva'])
        
        # Calculate timing metrics
        completed_df['tempo_cumprimento'] = (completed_df['data_cumprimento_suspensiva'] - completed_df['vencimento_da_suspensiva']).dt.days
        completed_df['tempo_pos_cumprimento'] = (completed_df['data_retirada_suspensiva'] - completed_df['data_cumprimento_suspensiva']).dt.days
        completed_df['tempo_total'] = (completed_df['data_retirada_suspensiva'] - completed_df['vencimento_da_suspensiva']).dt.days
        
        # Group by month
        completed_df['mes'] = completed_df['data_retirada_suspensiva'].dt.to_period('M')
        
        monthly_kpis = completed_df.groupby('mes').agg({
            'tempo_cumprimento': 'mean',
            'tempo_pos_cumprimento': 'mean',
            'tempo_total': 'mean'
        }).reset_index()
        
        monthly_kpis['Mês'] = monthly_kpis['mes'].astype(str)
        monthly_kpis['Tempo Médio Cumprimento'] = monthly_kpis['tempo_cumprimento'].round(1)
        monthly_kpis['Tempo Médio Pós-Cumprimento'] = monthly_kpis['tempo_pos_cumprimento'].round(1)
        monthly_kpis['Tempo Total Médio'] = monthly_kpis['tempo_total'].round(1)
        
        return monthly_kpis[['Mês', 'Tempo Médio Cumprimento', 'Tempo Médio Pós-Cumprimento', 'Tempo Total Médio']]
    
    except Exception:
        return pd.DataFrame()

def calculate_sla_trends(data_df):
    """Calculate SLA compliance trends"""
    try:
        # Use current days without movement as proxy
        if 'dias_sem_movimentacao' not in data_df.columns:
            return pd.DataFrame()
        
        # Group by month (using a proxy date or current date)
        # This is simplified - in reality you'd want actual monthly snapshots
        today = pd.Timestamp.now()
        monthly_data = []
        
        for i in range(6):  # Last 6 months
            month_date = today - pd.DateOffset(months=i)
            month_str = month_date.strftime('%Y-%m')
            
            # Calculate SLA compliance (simplified)
            current_days = data_df['dias_sem_movimentacao'].dropna()
            if not current_days.empty:
                sla_30 = (current_days <= 30).mean() * 100
                sla_60 = (current_days <= 60).mean() * 100
                sla_90 = (current_days <= 90).mean() * 100
                
                monthly_data.append({
                    'Mês': month_str,
                    'SLA 30 dias (%)': sla_30,
                    'SLA 60 dias (%)': sla_60,
                    'SLA 90 dias (%)': sla_90
                })
        
        return pd.DataFrame(monthly_data).sort_values('Mês')
    
    except Exception:
        return pd.DataFrame()

def kpi_by_region(data_df, timing_metrics):
    """KPI comparison by region"""
    if 'gigov_regov' not in data_df.columns:
        st.info("Dados de região não disponíveis")
        return
    
    st.subheader("KPIs por Região GIGOV")
    
    # Calculate regional KPIs
    regional_kpis = data_df.groupby('gigov_regov').agg({
        'operacao': 'count',
        'data_retirada_suspensiva': lambda x: x.notna().sum(),
        'dias_sem_movimentacao': 'mean' if 'dias_sem_movimentacao' in data_df.columns else lambda x: 0
    }).reset_index()
    
    regional_kpis.columns = ['Região', 'Total Operações', 'Suspensivas Concluídas', 'Média Dias sem Movimento']
    
    # Calculate completion rate
    regional_kpis['Taxa Conclusão (%)'] = (
        regional_kpis['Suspensivas Concluídas'] / regional_kpis['Total Operações'] * 100
    ).round(1)
    
    # Display comparison chart
    fig_regional_kpi = px.bar(
        regional_kpis,
        x='Região',
        y='Taxa Conclusão (%)',
        color='Média Dias sem Movimento',
        title="Taxa de Conclusão vs. Tempo Médio por Região",
        labels={'Taxa Conclusão (%)': 'Taxa de Conclusão (%)', 'Região': 'Região GIGOV'}
    )
    fig_regional_kpi.update_layout(height=400)
    st.plotly_chart(fig_regional_kpi, use_container_width=True)
    
    # Regional KPI table
    st.dataframe(regional_kpis, use_container_width=True)

def kpi_by_agency(data_df, timing_metrics):
    """KPI comparison by agency"""
    if 'repassador' not in data_df.columns:
        st.info("Dados de repassador não disponíveis")
        return
    
    st.subheader("KPIs por Repassador (Top 10)")
    
    # Calculate agency KPIs
    agency_kpis = data_df.groupby('repassador').agg({
        'operacao': 'count',
        'data_retirada_suspensiva': lambda x: x.notna().sum(),
        'dias_sem_movimentacao': 'mean' if 'dias_sem_movimentacao' in data_df.columns else lambda x: 0
    }).reset_index()
    
    agency_kpis.columns = ['Repassador', 'Total Operações', 'Suspensivas Concluídas', 'Média Dias sem Movimento']
    
    # Calculate completion rate
    agency_kpis['Taxa Conclusão (%)'] = (
        agency_kpis['Suspensivas Concluídas'] / agency_kpis['Total Operações'] * 100
    ).round(1)
    
    # Filter to significant agencies and top 10
    significant_agencies = agency_kpis[agency_kpis['Total Operações'] >= 5]
    top_agencies = significant_agencies.nlargest(10, 'Total Operações')
    
    if not top_agencies.empty:
        # Display comparison chart
        fig_agency_kpi = px.scatter(
            top_agencies,
            x='Total Operações',
            y='Taxa Conclusão (%)',
            size='Média Dias sem Movimento',
            hover_name='Repassador',
            title="Volume vs. Taxa de Conclusão por Repassador",
            labels={'Total Operações': 'Número de Operações', 'Taxa Conclusão (%)': 'Taxa de Conclusão (%)'}
        )
        fig_agency_kpi.update_layout(height=400)
        st.plotly_chart(fig_agency_kpi, use_container_width=True)
        
        # Agency KPI table
        st.dataframe(top_agencies, use_container_width=True)
    else:
        st.info("Nenhum repassador com volume significativo de operações")

def licitacao_module(df, vrpl_df):
    """Licitação/VRPL module - 3 screens from Power BI"""
    st.header("🏗️ Gestão da Carteira Contratada - VRPL")
    st.info("🚧 Módulo Licitação/VRPL - Planejado para desenvolvimento")
    
    # Show basic data availability
    if not df.empty:
        vrpl_columns = [col for col in df.columns if any(term in col.lower() for term in ['vrpl', 'licitacao', 'licitação', 'edital', 'ail'])]
        if vrpl_columns:
            st.write(f"📋 Colunas VRPL disponíveis: {len(vrpl_columns)}")
            with st.expander("Ver colunas VRPL"):
                st.write(vrpl_columns)

def obras_module(df, obras_df):
    """Obras module - 4 screens from Power BI"""
    st.header("🏠 Gestão da Carteira Contratada - Obras")
    
    if df.empty:
        st.warning("⚠️ Nenhum dado disponível")
        return
    
    # Sub-navigation for the 4 obras screens
    sub_tab1, sub_tab2, sub_tab3, sub_tab4 = st.tabs([
        "💰 Visão Financeira", "🗺️ Por Localização", "📊 Análise Visual", "📋 Detalhes"
    ])
    
    with sub_tab1:
        obras_financial_overview(df, obras_df)
    
    with sub_tab2:
        obras_geographic_breakdown(df, obras_df)
    
    with sub_tab3:
        obras_visual_analytics(df, obras_df)
    
    with sub_tab4:
        obras_detailed_operations(df, obras_df)

def obras_financial_overview(df, obras_df):
    """Obras Financial Overview by Ministry - Screen 1 from Power BI"""
    st.subheader("💰 Visão Financeira por Ministério")
    
    # Use obras view if available, otherwise main df
    data_df = obras_df if not obras_df.empty else df
    
    if data_df.empty:
        st.warning("⚠️ Nenhum dado financeiro disponível")
        return
    
    # Check for required financial columns
    financial_columns = ['valor_empenhado', 'valor_pago', 'valor_desbloqueado']
    available_financial = [col for col in financial_columns if col in data_df.columns]
    
    if not available_financial:
        st.error("❌ Colunas financeiras não encontradas nos dados")
        return
    
    # Portfolio summary metrics
    st.subheader("📊 Resumo do Portfolio Financeiro")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_ops = len(data_df)
        st.metric("Total de Operações", f"{total_ops:,}")
    
    with col2:
        if 'valor_empenhado' in data_df.columns:
            total_empenhado = data_df['valor_empenhado'].sum()
            st.metric("Valor Empenhado", format_currency(total_empenhado))
    
    with col3:
        if 'valor_pago' in data_df.columns:
            total_pago = data_df['valor_pago'].sum()
            st.metric("Valor Pago", format_currency(total_pago))
        elif 'valor_desbloqueado' in data_df.columns:
            total_desbloqueado = data_df['valor_desbloqueado'].sum()
            st.metric("Valor Desbloqueado", format_currency(total_desbloqueado))
    
    with col4:
        if 'valor_empenhado' in data_df.columns and 'valor_pago' in data_df.columns:
            total_empenhado = data_df['valor_empenhado'].sum()
            total_pago = data_df['valor_pago'].sum()
            if total_empenhado > 0:
                exec_rate = (total_pago / total_empenhado) * 100
                st.metric("Taxa Execução", f"{exec_rate:.1f}%")
        elif 'valor_empenhado' in data_df.columns and 'valor_desbloqueado' in data_df.columns:
            total_empenhado = data_df['valor_empenhado'].sum()
            total_desbloqueado = data_df['valor_desbloqueado'].sum()
            if total_empenhado > 0:
                desb_rate = (total_desbloqueado / total_empenhado) * 100
                st.metric("Taxa Desbloqueio", f"{desb_rate:.1f}%")
    
    with col5:
        if 'repassador' in data_df.columns:
            total_ministerios = data_df['repassador'].nunique()
            st.metric("Ministérios", f"{total_ministerios}")
    
    # Financial breakdown by Ministry (matching Power BI table)
    st.subheader("💼 Breakdown Financeiro por Ministério")
    
    if 'repassador' in data_df.columns:
        # Group by ministry and calculate financial metrics
        ministry_summary = data_df.groupby('repassador').agg({
            'operacao': 'count',
            'valor_empenhado': 'sum' if 'valor_empenhado' in data_df.columns else lambda x: 0,
            'valor_pago': 'sum' if 'valor_pago' in data_df.columns else lambda x: 0,
            'valor_desbloqueado': 'sum' if 'valor_desbloqueado' in data_df.columns else lambda x: 0
        }).reset_index()
        
        ministry_summary.columns = ['Repassador', 'Qtde Operações', 'Valor Empenhado', 'Valor Pago', 'Valor Desbloqueado']
        
        # Ensure numeric types for calculations
        numeric_columns = ['Valor Empenhado', 'Valor Pago', 'Valor Desbloqueado']
        for col in numeric_columns:
            if col in ministry_summary.columns:
                ministry_summary[col] = pd.to_numeric(ministry_summary[col], errors='coerce').fillna(0)
        
        # Calculate percentages safely
        ministry_summary['% Pago'] = 0.0
        ministry_summary['% Desbloqueado'] = 0.0
        
        # Only calculate percentages where Valor Empenhado > 0
        empenhado_mask = ministry_summary['Valor Empenhado'] > 0
        if empenhado_mask.any():
            ministry_summary.loc[empenhado_mask, '% Pago'] = (
                ministry_summary.loc[empenhado_mask, 'Valor Pago'] / 
                ministry_summary.loc[empenhado_mask, 'Valor Empenhado'] * 100
            ).round(2)
            
            ministry_summary.loc[empenhado_mask, '% Desbloqueado'] = (
                ministry_summary.loc[empenhado_mask, 'Valor Desbloqueado'] / 
                ministry_summary.loc[empenhado_mask, 'Valor Empenhado'] * 100
            ).round(2)
        
        # Sort by total value
        ministry_summary = ministry_summary.sort_values('Valor Empenhado', ascending=False)
        
        # Format currency columns
        currency_columns = ['Valor Empenhado', 'Valor Pago', 'Valor Desbloqueado']
        for col in currency_columns:
            if col in ministry_summary.columns:
                ministry_summary[f'{col} (Formatado)'] = ministry_summary[col].apply(format_currency)
        
        # Display formatted table
        display_columns = ['Repassador', 'Qtde Operações']
        if 'Valor Empenhado (Formatado)' in ministry_summary.columns:
            display_columns.extend(['Valor Empenhado (Formatado)', 'Valor Pago (Formatado)', 'Valor Desbloqueado (Formatado)', '% Pago', '% Desbloqueado'])
        
        display_df = ministry_summary[display_columns].copy()
        display_df.columns = ['Ministério/Repassador', 'Qtde Operações', 'Valor Empenhado', 'Valor Pago', 'Valor Desbloqueado', '% Pago', '% Desbloqueado']
        
        st.dataframe(
            display_df,
            use_container_width=True,
            height=400
        )
        
        # Financial distribution chart
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Distribuição do Portfolio por Ministério")
            
            # Pie chart of portfolio distribution
            top_ministries = ministry_summary.head(8)
            
            fig_pie = px.pie(
                top_ministries,
                values='Valor Empenhado',
                names='Repassador',
                title="Valor Empenhado por Ministério"
            )
            fig_pie.update_layout(height=400)
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            st.subheader("Execução Financeira por Ministério")
            
            # Bar chart of execution rates
            execution_data = ministry_summary[ministry_summary['Valor Empenhado'] > 0].head(10)
            
            fig_bar = px.bar(
                execution_data,
                x='% Pago',
                y='Repassador',
                orientation='h',
                title="Taxa de Execução (% Pago) por Ministério",
                labels={'% Pago': 'Percentual Pago (%)', 'Repassador': 'Ministério'}
            )
            fig_bar.update_layout(height=400)
            st.plotly_chart(fig_bar, use_container_width=True)
    
    else:
        st.info("Dados de repassador não disponíveis para análise por ministério")

def obras_geographic_breakdown(df, obras_df):
    """Obras Geographic Breakdown - Screen 2 from Power BI"""
    st.subheader("🗺️ Breakdown Financeiro por Localização")
    
    data_df = obras_df if not obras_df.empty else df
    
    if data_df.empty:
        st.warning("⚠️ Nenhum dado disponível")
        return
    
    # Geographic analysis by State and Municipality
    if 'uf' in data_df.columns and 'municipio_beneficiado' in data_df.columns:
        
        # State-level summary
        st.subheader("📍 Análise por Estado")
        
        state_summary = data_df.groupby('uf').agg({
            'operacao': 'count',
            'municipio_beneficiado': 'nunique',
            'valor_empenhado': 'sum' if 'valor_empenhado' in data_df.columns else lambda x: 0,
            'valor_desbloqueado': 'sum' if 'valor_desbloqueado' in data_df.columns else lambda x: 0
        }).reset_index()
        
        state_summary.columns = ['UF', 'Qtde Operações', 'Qtde Municípios', 'Valor Empenhado', 'Valor Desbloqueado']
        
        # Ensure numeric types
        numeric_columns = ['Valor Empenhado', 'Valor Desbloqueado']
        for col in numeric_columns:
            if col in state_summary.columns:
                state_summary[col] = pd.to_numeric(state_summary[col], errors='coerce').fillna(0)
        
        # Calculate percentage safely
        state_summary['% Desbloqueado'] = 0.0
        empenhado_mask = state_summary['Valor Empenhado'] > 0
        if empenhado_mask.any():
            state_summary.loc[empenhado_mask, '% Desbloqueado'] = (
                state_summary.loc[empenhado_mask, 'Valor Desbloqueado'] / 
                state_summary.loc[empenhado_mask, 'Valor Empenhado'] * 100
            ).round(2)
        
        state_summary = state_summary.sort_values('Valor Empenhado', ascending=False)
        
        # Format currency
        state_summary['Valor Empenhado (Formatado)'] = state_summary['Valor Empenhado'].apply(format_currency)
        state_summary['Valor Desbloqueado (Formatado)'] = state_summary['Valor Desbloqueado'].apply(format_currency)
        
        display_state_df = state_summary[['UF', 'Qtde Operações', 'Qtde Municípios', 'Valor Empenhado (Formatado)', 'Valor Desbloqueado (Formatado)', '% Desbloqueado']].copy()
        
        st.dataframe(
            display_state_df,
            use_container_width=True,
            height=300
        )
        
        # Municipality-level details
        st.subheader("🏙️ Análise por Município")
        
        # Filter by state
        selected_states = st.multiselect(
            "Filtrar por Estados:",
            options=sorted(data_df['uf'].unique()),
            default=sorted(data_df['uf'].unique())[:5]  # Show top 5 by default
        )
        
        if selected_states:
            filtered_municipal_df = data_df[data_df['uf'].isin(selected_states)]
            
            municipal_summary = filtered_municipal_df.groupby(['uf', 'municipio_beneficiado']).agg({
                'operacao': 'count',
                'valor_empenhado': 'sum' if 'valor_empenhado' in filtered_municipal_df.columns else lambda x: 0,
                'valor_desbloqueado': 'sum' if 'valor_desbloqueado' in filtered_municipal_df.columns else lambda x: 0
            }).reset_index()
            
            municipal_summary.columns = ['UF', 'Município', 'Qtde Operações', 'Valor Empenhado', 'Valor Desbloqueado']
            
            # Ensure numeric types
            numeric_columns = ['Valor Empenhado', 'Valor Desbloqueado']
            for col in numeric_columns:
                if col in municipal_summary.columns:
                    municipal_summary[col] = pd.to_numeric(municipal_summary[col], errors='coerce').fillna(0)
            
            # Calculate percentage safely
            municipal_summary['% Desbloqueado'] = 0.0
            empenhado_mask = municipal_summary['Valor Empenhado'] > 0
            if empenhado_mask.any():
                municipal_summary.loc[empenhado_mask, '% Desbloqueado'] = (
                    municipal_summary.loc[empenhado_mask, 'Valor Desbloqueado'] / 
                    municipal_summary.loc[empenhado_mask, 'Valor Empenhado'] * 100
                ).round(2)
            
            municipal_summary = municipal_summary.sort_values('Valor Empenhado', ascending=False).head(20)
            
            # Format currency
            municipal_summary['Valor Empenhado (Formatado)'] = municipal_summary['Valor Empenhado'].apply(format_currency)
            municipal_summary['Valor Desbloqueado (Formatado)'] = municipal_summary['Valor Desbloqueado'].apply(format_currency)
            
            display_municipal_df = municipal_summary[['UF', 'Município', 'Qtde Operações', 'Valor Empenhado (Formatado)', 'Valor Desbloqueado (Formatado)', '% Desbloqueado']].copy()
            
            st.dataframe(
                display_municipal_df,
                use_container_width=True,
                height=400
            )
        
        # Geographic visualization
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Distribuição por Estado")
            
            top_states = state_summary.head(10)
            fig_state = px.bar(
                top_states,
                x='Valor Empenhado',
                y='UF',
                orientation='h',
                title="Valor Empenhado por Estado",
                labels={'Valor Empenhado': 'Valor Empenhado (R$)', 'UF': 'Estado'}
            )
            fig_state.update_layout(height=400)
            st.plotly_chart(fig_state, use_container_width=True)
        
        with col2:
            st.subheader("Taxa de Execução por Estado")
            
            exec_states = state_summary[state_summary['Valor Empenhado'] > 0].head(10)
            fig_exec = px.scatter(
                exec_states,
                x='Valor Empenhado',
                y='% Desbloqueado',
                size='Qtde Operações',
                hover_name='UF',
                title="Execução vs. Valor por Estado",
                labels={'Valor Empenhado': 'Valor Empenhado (R$)', '% Desbloqueado': 'Taxa Desbloqueio (%)'}
            )
            fig_exec.update_layout(height=400)
            st.plotly_chart(fig_exec, use_container_width=True)
    
    else:
        st.info("Dados geográficos não disponíveis")

def obras_visual_analytics(df, obras_df):
    """Obras Visual Analytics - Screen 3 from Power BI"""
    st.subheader("📊 Análise Visual de Obras")
    
    st.info("🚧 Painel de análise de Obras em desenvolvimento")
    st.markdown("""
    **Funcionalidades planejadas:**
    - Gráficos de emissão de ordem de serviço vs. meta
    - Média percentual de obras informadas vs. executadas
    - Análises temporais de progresso
    """)
    
    # Show available construction-related data
    data_df = obras_df if not obras_df.empty else df
    
    if not data_df.empty:
        construction_columns = [col for col in data_df.columns if any(term in col.lower() for term in ['obra', 'percentual', 'execucao', 'inicio'])]
        
        if construction_columns:
            with st.expander("📋 Dados de Construção Disponíveis"):
                st.write(f"**Colunas encontradas:** {len(construction_columns)}")
                st.write(construction_columns)
                
                # Show sample data if available
                sample_data = data_df[construction_columns].head(5)
                if not sample_data.empty:
                    st.write("**Amostra dos dados:**")
                    st.dataframe(sample_data)

def obras_detailed_operations(df, obras_df):
    """Obras Detailed Operations - Screen 4 from Power BI"""
    st.subheader("📋 Operações Detalhadas - Obras")
    
    data_df = obras_df if not obras_df.empty else df
    
    if data_df.empty:
        st.warning("⚠️ Nenhum dado disponível")
        return
    
    # Filters
    st.subheader("🔍 Filtros")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'uf' in data_df.columns:
            available_ufs = sorted([uf for uf in data_df['uf'].dropna().unique() if uf and str(uf) != 'nan'])
            selected_ufs = st.multiselect("Estados:", options=available_ufs, default=available_ufs[:10] if len(available_ufs) > 10 else available_ufs)
        else:
            selected_ufs = []
    
    with col2:
        if 'repassador' in data_df.columns:
            available_repassadores = sorted([rep for rep in data_df['repassador'].dropna().unique() if rep and str(rep) != 'nan'])
            selected_repassadores = st.multiselect("Repassador:", options=available_repassadores, default=available_repassadores[:5] if len(available_repassadores) > 5 else available_repassadores)
        else:
            selected_repassadores = []
    
    with col3:
        if 'valor_empenhado' in data_df.columns:
            min_value = float(data_df['valor_empenhado'].min()) if pd.notna(data_df['valor_empenhado'].min()) else 0
            max_value = float(data_df['valor_empenhado'].max()) if pd.notna(data_df['valor_empenhado'].max()) else 1000000
            
            value_range = st.slider(
                "Faixa de Valor Empenhado (R$):",
                min_value=min_value,
                max_value=max_value,
                value=(min_value, max_value),
                format="%.0f"
            )
        else:
            value_range = None
    
    # Apply filters
    filtered_df = data_df.copy()
    
    if selected_ufs and 'uf' in data_df.columns:
        filtered_df = filtered_df[filtered_df['uf'].isin(selected_ufs)]
    
    if selected_repassadores and 'repassador' in data_df.columns:
        filtered_df = filtered_df[filtered_df['repassador'].isin(selected_repassadores)]
    
    if value_range and 'valor_empenhado' in data_df.columns:
        filtered_df = filtered_df[
            (filtered_df['valor_empenhado'] >= value_range[0]) &
            (filtered_df['valor_empenhado'] <= value_range[1])
        ]
    
    # Summary of filtered data
    st.subheader("📊 Resumo dos Dados Filtrados")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Operações", f"{len(filtered_df):,}")
    
    with col2:
        if 'valor_empenhado' in filtered_df.columns:
            total_empenhado = filtered_df['valor_empenhado'].sum()
            st.metric("Valor Total", format_currency(total_empenhado))
    
    with col3:
        if 'uf' in filtered_df.columns:
            estados_count = filtered_df['uf'].nunique()
            st.metric("Estados", f"{estados_count}")
    
    with col4:
        if 'municipio_beneficiado' in filtered_df.columns:
            municipios_count = filtered_df['municipio_beneficiado'].nunique()
            st.metric("Municípios", f"{municipios_count}")
    
    # Detailed table
    st.subheader("📋 Tabela Detalhada")
    
    if not filtered_df.empty:
        # Select columns for display
        detail_columns = [
            'operacao',
            'uf',
            'municipio_beneficiado',
            'repassador',
            'valor_empenhado',
            'valor_desbloqueado',
            'situacao_atual'
        ]
        
        # Add construction-specific columns if available
        construction_cols = [col for col in filtered_df.columns if any(term in col.lower() for term in ['obra', 'percentual', 'execucao'])]
        detail_columns.extend(construction_cols[:3])  # Add first 3 construction columns
        
        # Filter to existing columns
        available_detail_columns = [col for col in detail_columns if col in filtered_df.columns]
        
        display_df = filtered_df[available_detail_columns].copy()
        
        # Sort by value
        if 'valor_empenhado' in display_df.columns:
            display_df = display_df.sort_values('valor_empenhado', ascending=False)
        
        # Format column names
        column_renames = {
            'operacao': 'Operação',
            'uf': 'UF',
            'municipio_beneficiado': 'Município',
            'repassador': 'Repassador',
            'valor_empenhado': 'Valor Empenhado (R$)',
            'valor_desbloqueado': 'Valor Desbloqueado (R$)',
            'situacao_atual': 'Situação Atual'
        }
        
        display_df = display_df.rename(columns=column_renames)
        
        # Format currency
        currency_columns = ['Valor Empenhado (R$)', 'Valor Desbloqueado (R$)']
        for col in currency_columns:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(lambda x: format_currency(x) if pd.notna(x) else 'N/A')
        
        # Pagination
        items_per_page = st.selectbox("Itens por página:", [25, 50, 100], index=1)
        total_pages = len(display_df) // items_per_page + (1 if len(display_df) % items_per_page > 0 else 0)
        
        if total_pages > 1:
            page = st.selectbox(f"Página (1 de {total_pages}):", range(1, total_pages + 1))
            start_idx = (page - 1) * items_per_page
            end_idx = start_idx + items_per_page
            paginated_df = display_df.iloc[start_idx:end_idx]
        else:
            paginated_df = display_df.head(items_per_page)
        
        st.dataframe(
            paginated_df,
            use_container_width=True,
            height=500
        )
        
        st.info(f"Mostrando {len(paginated_df)} de {len(display_df)} operações")
    
    else:
        st.warning("⚠️ Nenhuma operação encontrada com os filtros aplicados")

def overview_module(df, summary_df):
    """Executive Overview module"""
    st.header("📊 Visão Geral Executiva do Portfolio PAC")
    
    if df.empty:
        st.warning("⚠️ Nenhum dado disponível")
        return
    
    # Executive KPIs
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="kpi-number">{format_number(len(df))}</div>
            <div>Total Operações</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if 'valor_empenhado' in df.columns:
            total_empenhado = df['valor_empenhado'].sum()
            st.markdown(f"""
            <div class="metric-card">
                <div class="kpi-number">{format_currency(total_empenhado)}</div>
                <div>Valor Empenhado</div>
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        if 'uf' in df.columns:
            estados = df['uf'].nunique()
            st.markdown(f"""
            <div class="metric-card">
                <div class="kpi-number">{estados}</div>
                <div>Estados Atendidos</div>
            </div>
            """, unsafe_allow_html=True)
    
    with col4:
        if 'municipio_beneficiado' in df.columns:
            municipios = df['municipio_beneficiado'].nunique()
            st.markdown(f"""
            <div class="metric-card">
                <div class="kpi-number">{municipios}</div>
                <div>Municípios</div>
            </div>
            """, unsafe_allow_html=True)
    
    with col5:
        if 'repassador' in df.columns:
            ministerios = df['repassador'].nunique()
            st.markdown(f"""
            <div class="metric-card">
                <div class="kpi-number">{ministerios}</div>
                <div>Ministérios</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Data structure information
    st.subheader("📋 Estrutura dos Dados")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Total de registros:** {format_number(len(df))}")
        st.write(f"**Total de colunas:** {len(df.columns)}")
        
        # Show column categories
        suspensiva_cols = [col for col in df.columns if 'suspensiv' in col.lower()]
        vrpl_cols = [col for col in df.columns if any(term in col.lower() for term in ['vrpl', 'ail', 'edital'])]
        financial_cols = [col for col in df.columns if any(term in col.lower() for term in ['valor', 'empenhado', 'pago'])]
        
        st.write(f"**Colunas Suspensivas:** {len(suspensiva_cols)}")
        st.write(f"**Colunas VRPL:** {len(vrpl_cols)}")
        st.write(f"**Colunas Financeiras:** {len(financial_cols)}")
    
    with col2:
        # Portfolio distribution
        if 'repassador' in df.columns and 'valor_empenhado' in df.columns:
            st.subheader("Distribuição do Portfolio")
            
            ministry_values = df.groupby('repassador')['valor_empenhado'].sum().sort_values(ascending=True).tail(10)
            
            if not ministry_values.empty:
                fig_ministry = px.bar(
                    x=ministry_values.values / 1000000000,
                    y=ministry_values.index,
                    orientation='h',
                    title="Portfolio por Ministério (R$ Bilhões)",
                    labels={'x': 'Valor Empenhado (R$ Bilhões)', 'y': 'Ministério'}
                )
                fig_ministry.update_layout(height=400)
                st.plotly_chart(fig_ministry, use_container_width=True)
if __name__ == "__main__":
    main()
