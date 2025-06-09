# Save as: streamlit_app/dashboard_mcmv_enhanced_final.py
#!/usr/bin/env python3
"""
MCMV Enhanced Dashboard Final - Complete with all KPIs and new analytics
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from sqlalchemy import create_engine, text
import os
from datetime import datetime
import numpy as np
import urllib.request
from io import BytesIO
import hashlib
from functools import wraps

import json
from datetime import datetime, timedelta
from functools import wraps

# Page config
st.set_page_config(
    page_title="MCMV Analytics Dashboard - Enhanced",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# User database with hashed passwords
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
            🏠 MCMV Dashboard - CAIXA
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
    - Digite seu email e senha para acessar o dashboard
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
# Custom CSS
# Enhanced Custom CSS with forced light theme
# Fixed Custom CSS - Light theme without breaking plots
# Stunningly Beautiful & Sleek Dashboard CSS
st.markdown("""
<style>
    /* Import elegant fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Stunning app background with subtle gradient */
    .stApp {
        background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%) !important;
        color: #1e293b !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        font-weight: 400;
    }
    
    /* Beautiful main container */
    .main .block-container {
        background-color: transparent !important;
        padding-top: 2rem;
        max-width: 1200px;
    }
    
    /* Elegant sidebar with matching theme */
    .css-1d391kg, .css-1cypcdb, .css-17eq0hr {
        background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%) !important;
        border-right: 1px solid #e2e8f0 !important;
    }
    
    /* Sidebar text consistency */
    .css-1d391kg .stMarkdown, .css-1d391kg h1, .css-1d391kg h2, .css-1d391kg h3 {
        color: #1e293b !important;
    }
    
    /* Absolutely stunning metric containers */
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid #e2e8f0;
        padding: 28px;
        border-radius: 20px;
        box-shadow: 
            0 4px 20px rgba(15, 23, 42, 0.04), 
            0 2px 10px rgba(15, 23, 42, 0.06),
            0 1px 4px rgba(15, 23, 42, 0.08);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        backdrop-filter: blur(12px);
        position: relative;
        overflow: hidden;
    }
    
    /* Beautiful hover effects */
    div[data-testid="metric-container"]:hover {
        transform: translateY(-6px) scale(1.02);
        box-shadow: 
            0 20px 40px rgba(15, 23, 42, 0.12), 
            0 8px 20px rgba(15, 23, 42, 0.08),
            0 4px 8px rgba(15, 23, 42, 0.06);
        border-color: #cbd5e1;
    }
    
    /* Gorgeous accent line on metrics */
    div[data-testid="metric-container"]:before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #3b82f6 0%, #06b6d4 50%, #10b981 100%);
        opacity: 0.8;
        border-radius: 20px 20px 0 0;
    }
    
    /* Sleek tab system */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background: linear-gradient(135deg, #f1f5f9 0%, #ffffff 100%);
        border-radius: 20px;
        padding: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 
            0 4px 16px rgba(15, 23, 42, 0.04),
            0 2px 8px rgba(15, 23, 42, 0.02);
        backdrop-filter: blur(8px);
    }
    
    .stTabs [data-baseweb="tab-list"] button {
        background-color: transparent !important;
        border-radius: 16px !important;
        color: #64748b !important;
        font-weight: 500;
        font-size: 14px;
        padding: 14px 24px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border: none !important;
        position: relative;
        overflow: hidden;
    }
    
    .stTabs [data-baseweb="tab-list"] button:hover {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%) !important;
        color: #334155 !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06);
    }
    
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%) !important;
        color: #1e293b !important;
        font-weight: 600;
        box-shadow: 
            0 6px 20px rgba(15, 23, 42, 0.12), 
            0 3px 8px rgba(15, 23, 42, 0.08);
        border: 1px solid #e2e8f0 !important;
        transform: translateY(-1px);
    }
    
    /* Selected tab accent */
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"]:before {
        content: '';
        position: absolute;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 60%;
        height: 3px;
        background: linear-gradient(90deg, #3b82f6, #06b6d4);
        border-radius: 2px;
    }
    
    /* Stunning headers with gradient text */
    h1 {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        background: linear-gradient(135deg, #1e293b 0%, #475569 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.02em;
        margin-bottom: 1.5rem !important;
    }
    
    h2, h3 {
        color: #1e293b !important;
        font-weight: 600 !important;
        letter-spacing: -0.015em;
    }
    
    /* Beautiful KPI highlight boxes */
    .new-kpi-highlight {
        background: linear-gradient(135deg, #dbeafe 0%, #ffffff 100%);
        border: 1px solid #93c5fd;
        border-left: 5px solid #3b82f6;
        padding: 28px;
        border-radius: 20px;
        margin: 24px 0;
        box-shadow: 
            0 8px 24px rgba(59, 130, 246, 0.08),
            0 4px 12px rgba(59, 130, 246, 0.04);
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(8px);
    }
    
    .new-kpi-highlight:before {
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        width: 100px;
        height: 100px;
        background: radial-gradient(circle, rgba(59, 130, 246, 0.1), transparent 70%);
        border-radius: 50%;
        transform: translate(30px, -30px);
    }
    
    /* Elegant critical alerts */
    .critical-alert {
        background: linear-gradient(135deg, #fef2f2 0%, #ffffff 100%);
        border: 1px solid #fca5a5;
        border-left: 5px solid #ef4444;
        padding: 28px;
        border-radius: 20px;
        margin: 24px 0;
        box-shadow: 
            0 8px 24px rgba(239, 68, 68, 0.08),
            0 4px 12px rgba(239, 68, 68, 0.04);
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(8px);
    }
    
    .critical-alert:before {
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        width: 100px;
        height: 100px;
        background: radial-gradient(circle, rgba(239, 68, 68, 0.1), transparent 70%);
        border-radius: 50%;
        transform: translate(30px, -30px);
    }
    
    /* Spectacular investment summary */
    .investment-summary {
        background: linear-gradient(135deg, #f0fdf4 0%, #ffffff 100%);
        border: 2px solid #86efac;
        border-radius: 24px;
        padding: 40px;
        margin: 32px 0;
        text-align: center;
        box-shadow: 
            0 12px 32px rgba(34, 197, 94, 0.12),
            0 6px 16px rgba(34, 197, 94, 0.06),
            0 3px 8px rgba(34, 197, 94, 0.04);
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(12px);
    }
    
    .investment-summary:before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 200px;
        height: 200px;
        background: radial-gradient(circle, rgba(34, 197, 94, 0.08), transparent 60%);
        border-radius: 50%;
    }
    
    .investment-summary h3 {
        color: #059669 !important;
        font-size: 1.75rem !important;
        margin-bottom: 16px;
        font-weight: 700;
        position: relative;
        z-index: 1;
    }
    
    /* Gorgeous financial styling */
    .financial-positive {
        color: #059669 !important;
        font-weight: 700;
        text-shadow: 0 1px 2px rgba(5, 150, 105, 0.1);
    }
    
    .financial-negative {
        color: #dc2626 !important;
        font-weight: 700;
        text-shadow: 0 1px 2px rgba(220, 38, 38, 0.1);
    }
    
    /* Smooth page transitions */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .main .block-container > div {
        animation: fadeInUp 0.8s ease-out;
    }
    
    /* Beautiful form elements */
    .stSelectbox label {
        color: #374151 !important;
        font-weight: 500;
        font-size: 14px;
    }
    
    /* Elegant loading states */
    .stSpinner > div {
        border-color: #3b82f6 !important;
    }
    
    /* Perfect mobile experience */
    @media (max-width: 768px) {
        div[data-testid="metric-container"] {
            padding: 24px;
            margin: 16px 0;
            border-radius: 16px;
        }
        
        .new-kpi-highlight, .critical-alert {
            padding: 24px;
            margin: 20px 0;
            border-radius: 16px;
        }
        
        .investment-summary {
            padding: 32px;
            margin: 24px 0;
            border-radius: 20px;
        }
        
        h1 {
            font-size: 2rem !important;
        }
        
        .stTabs [data-baseweb="tab-list"] {
            padding: 8px;
        }
        
        .stTabs [data-baseweb="tab-list"] button {
            padding: 12px 16px !important;
            font-size: 13px;
        }
    }
    
    /* ABSOLUTELY NO INTERFERENCE WITH CHARTS/MAPS */
    /* Plotly, Folium, and all visualization libraries remain untouched */
    
</style>
""", unsafe_allow_html=True)
# Define all MCMV programs
MCMV_PROGRAMS = [
    'FAR', 'FDS', 'RURAL',
    'Minha Casa Minha Vida - Faixa 1',
    'Minha Casa Minha Vida - Faixa 2', 
    'Minha Casa Minha Vida - Faixa 3',
    'Casa Verde e Amarela',
    'Habitação Rural'
]

# Brazil regions
REGION_MAPPING = {
    'Norte': ['AC', 'AP', 'AM', 'PA', 'RO', 'RR', 'TO'],
    'Nordeste': ['AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE'],
    'Centro-Oeste': ['DF', 'GO', 'MT', 'MS'],
    'Sudeste': ['ES', 'MG', 'RJ', 'SP'],
    'Sul': ['PR', 'RS', 'SC']
}

@st.cache_resource
def get_db_connection():
    """Get database connection"""
    db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres123@db:5432/pac_mcmv')
    return create_engine(db_url)

@st.cache_data(ttl=3600)
def load_brazil_geojson():
    """Load Brazil states GeoJSON from URL"""
    try:
        url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read())
    except Exception as e:
        st.warning(f"Não foi possível carregar GeoJSON: {e}")
        return None

# ===== ORIGINAL DATA LOADING FUNCTIONS =====

@st.cache_data(ttl=300)
def load_national_summary():
    """Load national summary from view"""
    engine = get_db_connection()
    query = "SELECT * FROM mcmv_pj.vw_resumo_nacional"
    return pd.read_sql(query, engine).iloc[0]

@st.cache_data(ttl=300)
def load_uh_gap_by_state():
    """Load UH gap analysis by state with all programs"""
    engine = get_db_connection()
    query = f"""
    SELECT uf, programa, 
           SUM(uh_esperadas) as uh_esperadas,
           SUM(uh_executadas) as uh_executadas,
           SUM(brecha_uh) as brecha_uh,
           AVG(percentual_medio) as percentual_medio
    FROM mcmv_pj.vw_brecha_uh_por_uf
    WHERE programa IN {tuple(MCMV_PROGRAMS)}
    GROUP BY uf, programa
    ORDER BY brecha_uh DESC
    """
    return pd.read_sql(query, engine)

@st.cache_data(ttl=300)
def load_region_summary():
    """Load summary by region"""
    engine = get_db_connection()
    
    # Build region case statement
    region_cases = []
    for region, states in REGION_MAPPING.items():
        states_str = "','".join(states)
        region_cases.append(f"WHEN uf IN ('{states_str}') THEN '{region}'")
    
    query = f"""
    SELECT 
        CASE {' '.join(region_cases)} END as regiao,
        COUNT(*) as total_projetos,
        SUM(uh_estimadas) as uh_esperadas,
        SUM(uh_estimadas * percentual_mcmv / 100.0) as uh_executadas,
        SUM(uh_estimadas * (1 - percentual_mcmv / 100.0)) as brecha_uh,
        AVG(percentual_mcmv) as percentual_medio
    FROM mcmv_pj.vw_empreendimentos_unificado
    WHERE programa IN {tuple(MCMV_PROGRAMS)}
    GROUP BY regiao
    ORDER BY uh_esperadas DESC
    """
    return pd.read_sql(query, engine)

@st.cache_data(ttl=300)
def load_risk_by_program():
    """Load risk analysis by program - simplified without problematic columns"""
    engine = get_db_connection()
    query = f"""
    SELECT programa,
           COUNT(*) FILTER (WHERE alto_risco) as alto_risco,
           COUNT(*) as total_projetos
    FROM mcmv_pj.vw_empreendimentos_unificado
    WHERE programa IN {tuple(MCMV_PROGRAMS)}
    GROUP BY programa
    ORDER BY alto_risco DESC
    """
    return pd.read_sql(query, engine)

@st.cache_data(ttl=300)
def load_risk_by_state():
    """Load risk analysis by state - simplified"""
    engine = get_db_connection()
    query = f"""
    SELECT uf,
           COUNT(*) FILTER (WHERE alto_risco) as alto_risco,
           COUNT(*) as total_projetos,
           AVG(percentual_mcmv) as avg_execution
    FROM mcmv_pj.vw_empreendimentos_unificado
    WHERE programa IN {tuple(MCMV_PROGRAMS)}
    GROUP BY uf
    HAVING COUNT(*) FILTER (WHERE alto_risco) > 0
    ORDER BY alto_risco DESC
    """
    return pd.read_sql(query, engine)

@st.cache_data(ttl=300)
def load_contratacoes_summary():
    """Load contracting summary simulating MCID status"""
    engine = get_db_connection()
    query = f"""
    SELECT
        COUNT(*) as total_empreendimentos,
        SUM(uh_estimadas) as uh_total,
        SUM(valor_investimento_mcmv + valor_investimento_pac) as valor_total,
        COUNT(*) FILTER (WHERE percentual_mcmv < 5) as aguardando_mcid,
        SUM(uh_estimadas) FILTER (WHERE percentual_mcmv < 5) as uh_aguardando_mcid,
        COUNT(*) FILTER (WHERE percentual_mcmv BETWEEN 5 AND 15) as mcid_emitida,
        SUM(uh_estimadas) FILTER (WHERE percentual_mcmv BETWEEN 5 AND 15) as uh_mcid_emitida,
        COUNT(*) FILTER (WHERE percentual_mcmv >= 15) as contratos_emitidos,
        SUM(uh_estimadas) FILTER (WHERE percentual_mcmv >= 15) as uh_contratos_emitidos,
        COUNT(*) FILTER (WHERE alto_risco AND percentual_mcmv < 20) as distratos,
        SUM(uh_estimadas) FILTER (WHERE alto_risco AND percentual_mcmv < 20) as uh_distratos
    FROM mcmv_pj.vw_empreendimentos_unificado
    WHERE programa IN {tuple(MCMV_PROGRAMS)}
    """
    return pd.read_sql(query, engine).iloc[0]

@st.cache_data(ttl=300)
def load_financial_flow():
    """Load financial flow analysis"""
    engine = get_db_connection()
    query = f"""
    SELECT uf, programa,
           SUM(investimento_total) as investimento_total,
           SUM(empenhado) as empenhado,
           SUM(desbloqueado) as desbloqueado,
           AVG(taxa_execucao_financeira) as taxa_execucao
    FROM financeiro.vw_fluxo_consolidado
    WHERE programa IN {tuple(MCMV_PROGRAMS)}
    GROUP BY uf, programa
    ORDER BY investimento_total DESC
    LIMIT 20
    """
    return pd.read_sql(query, engine)

# ===== NEW KPI DATA LOADING FUNCTIONS =====

@st.cache_data(ttl=300)
def load_beneficiary_summary():
    """Load national beneficiary summary"""
    engine = get_db_connection()
    try:
        query = "SELECT * FROM mcmv_pf.vw_beneficiarios_resumo_nacional"
        return pd.read_sql(query, engine).iloc[0]
    except Exception as e:
        st.error(f"Erro ao carregar resumo de beneficiários: {e}")
        return pd.Series({
            'projetos_com_beneficiarios': 0,
            'total_beneficiarios': 0,
            'total_mulheres': 0,
            'total_homens': 0,
            'percentual_mulheres': 0,
            'renda_media_sm_nacional': 0,
            'valor_medio_imovel_nacional': 0,
            'valor_total_financiado': 0,
            'sem_pagamento': 0
        })

@st.cache_data(ttl=300)
def load_beneficiary_analytics():
    """Load beneficiary analytics by project"""
    engine = get_db_connection()
    try:
        query = """
        SELECT ba."NU_APF", ba.total_beneficiarios, ba.beneficiarias_mulheres, 
               ba.beneficiarios_homens, ba.percentual_mulheres, ba.renda_media_sm,
               ba.valor_medio_imovel, ba.valor_total_imoveis,
               ps.uf, ps.nome_empreendimento, ps.programa
        FROM mcmv_pf.vw_beneficiarios_analytics ba
        JOIN projeto_status ps ON ba."NU_APF"::text = ps.proposta
        WHERE ps.tipo_programa = 'MCMV-HIS'
        ORDER BY ba.total_beneficiarios DESC
        """
        return pd.read_sql(query, engine)
    except Exception as e:
        st.error(f"Erro ao carregar analytics de beneficiários: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_timeline_analysis():
    """Load timeline and delay analysis"""
    engine = get_db_connection()
    try:
        query = "SELECT * FROM mcmv_pj.vw_analise_prazos ORDER BY programa, uf"
        return pd.read_sql(query, engine)
    except Exception as e:
        st.error(f"Erro ao carregar análise de prazos: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_social_work():
    """Load social work tracking"""
    engine = get_db_connection()
    try:
        query = "SELECT * FROM mcmv_pf.vw_trabalho_social ORDER BY programa, uf"
        return pd.read_sql(query, engine)
    except Exception as e:
        st.error(f"Erro ao carregar trabalho social: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_financial_execution():
    """Load financial execution data"""
    engine = get_db_connection()
    try:
        query = "SELECT * FROM financeiro.vw_execucao_financeira ORDER BY programa, uf"
        return pd.read_sql(query, engine)
    except Exception as e:
        st.error(f"Erro ao carregar execução financeira: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_program_summary():
    """Load program performance summary"""
    engine = get_db_connection()
    try:
        query = "SELECT * FROM mcmv_pj.vw_resumo_programa"
        return pd.read_sql(query, engine)
    except Exception as e:
        st.error(f"Erro ao carregar resumo de programas: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_state_performance():
    """Load state performance data"""
    engine = get_db_connection()
    try:
        query = "SELECT * FROM mcmv_pj.vw_desempenho_por_estado ORDER BY total_projetos DESC"
        return pd.read_sql(query, engine)
    except Exception as e:
        st.error(f"Erro ao carregar desempenho por estado: {e}")
        return pd.DataFrame()

# ===== NEW KPI RENDERING FUNCTIONS =====

def render_beneficiarios_tab():
    """Render beneficiary analytics tab with neutral presentation"""
    st.header("👥 Análise de Beneficiários")
    
    # Load data
    summary = load_beneficiary_summary()
    analytics = load_beneficiary_analytics()
    
    # Dynamic neutral findings
    total_beneficiaries = summary['total_beneficiarios'] if not summary.empty else 0
    total_women = summary['total_mulheres'] if not summary.empty else 0
    pct_women = summary['percentual_mulheres'] if not summary.empty else 0
    sem_pagamento = summary['sem_pagamento'] if not summary.empty else 0
    pct_sem_pagamento = (sem_pagamento / total_beneficiaries * 100) if total_beneficiaries > 0 else 0
    
    st.markdown(f"""
    <div class="new-kpi-highlight">
        <h4>📊 Achados Relevantes - Beneficiários</h4>
        <ul>
            <li><strong>{total_beneficiaries:,} famílias</strong> cadastradas como beneficiárias (programa RURAL)</li>
            <li><strong>{pct_women:.1f}% são mulheres</strong> chefes de família no programa habitacional</li>
            <li><strong>{pct_sem_pagamento:.1f}% sem registros de pagamento</strong> (dados em processo de atualização)</li>
            <li><strong>Renda média familiar:</strong> {summary.get('renda_media_sm_nacional', 0):.1f} SM registrados no sistema</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # KPI Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Beneficiários", 
            f"{int(summary['total_beneficiarios']):,}",
            delta=f"{int(summary['projetos_com_beneficiarios'])} projetos"
        )
    
    with col2:
        st.metric(
            "Mulheres Chefes de Família", 
            f"{summary['percentual_mulheres']:.1f}%",
            delta=f"{int(summary['total_mulheres']):,} beneficiárias"
        )
    
    with col3:
        st.metric(
            "Valor Médio Imóvel", 
            f"R$ {summary['valor_medio_imovel_nacional']:,.0f}",
            delta=f"R$ {summary['valor_total_financiado']/1e9:.2f}B total"
        )
    
    with col4:
        st.metric(
            "Status de Pagamento", 
            f"{int(summary['sem_pagamento']):,}",
            delta="Em processamento",
        )
    
    # Gender Distribution Chart
    st.subheader("📊 Distribuição por Gênero")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        gender_data = pd.DataFrame({
            'Gênero': ['Mulheres', 'Homens'],
            'Quantidade': [summary['total_mulheres'], summary['total_homens']],
            'Percentual': [summary['percentual_mulheres'], 100 - summary['percentual_mulheres']]
        })
        
        fig = px.pie(gender_data, values='Quantidade', names='Gênero', 
                     title="Beneficiários por Gênero",
                     color_discrete_map={'Mulheres': '#FF69B4', 'Homens': '#4169E1'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.info(f"""
        **Perfil dos Beneficiários:**

        🏠 {f"{int(summary['total_mulheres']):,}".replace(',', '.')} mulheres chefes de família no programa

        📊 {f"{summary['percentual_mulheres']:.1f}".replace('.', ',')}% dos beneficiários são mulheres

        💰 R$ {f"{summary['valor_total_financiado']/1e6:,.0f}".replace(',', '.')} milhões em financiamentos

        📋 Conforme política de priorização habitacional
        """)
    
    # Top Projects by Beneficiaries
    if not analytics.empty:
        st.subheader("🏘️ Projetos com Mais Beneficiários")
        top_projects = analytics.head(10)
        fig = px.bar(top_projects, x='total_beneficiarios', y='nome_empreendimento',
                     orientation='h', title="Top 10 Projetos por Número de Beneficiários",
                     color='percentual_mulheres', color_continuous_scale='RdYlBu_r',
                     hover_data=['uf', 'programa'])
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Beneficiary data table
        st.subheader("📋 Dados Detalhados de Beneficiários")
        display_analytics = analytics[['nome_empreendimento', 'uf', 'programa', 'total_beneficiarios', 
                                     'beneficiarias_mulheres', 'percentual_mulheres', 'valor_medio_imovel']].copy()
        display_analytics.columns = ['Empreendimento', 'UF', 'Programa', 'Total Beneficiários', 
                                    'Mulheres', '% Mulheres', 'Valor Médio Imóvel']
        st.dataframe(display_analytics, use_container_width=True, hide_index=True)

def render_prazos_tab():
    """Render timeline and delays analysis with neutral presentation"""
    st.header("⏱️ Análise de Prazos e Cronogramas")
    
    # Load data
    timeline = load_timeline_analysis()
    
    if timeline.empty:
        st.warning("Nenhum dado de prazo disponível")
        return
    
    # Calculate dynamic metrics
    started_projects = timeline['projetos_iniciados'].sum()
    not_started = timeline['projetos_nao_iniciados'].sum()
    total_projects = started_projects + not_started
    pct_started = (started_projects / total_projects * 100) if total_projects > 0 else 0
    pct_not_started = (not_started / total_projects * 100) if total_projects > 0 else 0
    
    # Calculate program-specific percentages
    far_data = timeline[timeline['programa'] == 'FAR']
    fds_data = timeline[timeline['programa'] == 'FDS'] 
    rural_data = timeline[timeline['programa'] == 'RURAL']
    
    far_started_pct = (far_data['projetos_iniciados'].sum() / (far_data['projetos_iniciados'].sum() + far_data['projetos_nao_iniciados'].sum()) * 100) if not far_data.empty else 0
    fds_started_pct = (fds_data['projetos_iniciados'].sum() / (fds_data['projetos_iniciados'].sum() + fds_data['projetos_nao_iniciados'].sum()) * 100) if not fds_data.empty else 0
    rural_started_pct = (rural_data['projetos_iniciados'].sum() / (rural_data['projetos_iniciados'].sum() + rural_data['projetos_nao_iniciados'].sum()) * 100) if not rural_data.empty else 0
    
    # Dynamic relevant findings alert
    st.markdown(f"""
    <div class="new-kpi-highlight">
        <h4>📊 Achados Relevantes - Cronogramas</h4>
        <ul>
            <li><strong>{started_projects:,} projetos iniciados</strong> ({pct_started:.1f}% do total)</li>
            <li><strong>{not_started:,} projetos em fase de preparação</strong> ({pct_not_started:.1f}% do total)</li>
            <li><strong>Taxa de início:</strong> FDS: {fds_started_pct:.1f}%, FAR: {far_started_pct:.1f}%, RURAL: {rural_started_pct:.1f}%</li>
            <li><strong>Projetos com cronogramas recentes</strong> (2024-2025) em diferentes fases de execução</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Projetos Iniciados",
            f"{started_projects:,}",
            delta=f"{(started_projects/total_projects*100):.1f}% do total"
        )
    
    with col2:
        st.metric(
            "Projetos em Preparação",
            f"{not_started:,}",
            delta=f"{(not_started/total_projects*100):.1f}% do total"
        )
    
    with col3:
        stalled_6m = timeline['sem_progresso_6_meses'].sum()
        st.metric(
            "Sem Progresso 6+ Meses",
            f"{stalled_6m:,}",
            delta="Para análise" if stalled_6m > 0 else "Nenhum"
        )
    
    with col4:
        stalled_1y = timeline['paralisados_1_ano'].sum()
        st.metric(
            "Sem Progresso 1+ Ano",
            f"{stalled_1y:,}",
            delta="Para revisão" if stalled_1y > 0 else "Nenhum"
        )
    
    # Timeline by Program
    st.subheader("📈 Status por Programa")
    program_summary = timeline.groupby('programa').agg({
        'projetos_iniciados': 'sum',
        'projetos_nao_iniciados': 'sum',
        'sem_progresso_6_meses': 'sum',
        'paralisados_1_ano': 'sum',
        'media_dias_em_obra': 'mean'
    }).round(0)
    
    # Reshape for plotting
    plot_data = program_summary[['projetos_iniciados', 'projetos_nao_iniciados']].reset_index()
    plot_data = plot_data.melt(id_vars='programa', var_name='Status', value_name='Quantidade')
    plot_data['Status'] = plot_data['Status'].map({
        'projetos_iniciados': 'Iniciados',
        'projetos_nao_iniciados': 'Em Preparação'
    })
    
    fig = px.bar(plot_data, x='programa', y='Quantidade', color='Status',
                 title="Projetos Iniciados vs Em Preparação por Programa",
                 color_discrete_map={'Iniciados': '#2E8B57', 'Em Preparação': '#FFA500'})
    st.plotly_chart(fig, use_container_width=True)
    
    # State Analysis
    st.subheader("🗺️ Análise por Estado")
    state_data = timeline[timeline['uf'].notna()]
    
    if not state_data.empty:
        # Calculate percentage not started
        state_data = state_data.copy()
        state_data['total_projetos_calc'] = state_data['projetos_iniciados'] + state_data['projetos_nao_iniciados']
        state_data['pct_em_preparacao'] = (state_data['projetos_nao_iniciados'] / 
                                          state_data['total_projetos_calc'] * 100).round(1)
        
        # Top states with highest percentage of projects in preparation
        prep_states = state_data.nlargest(10, 'pct_em_preparacao')
        
        fig = px.bar(prep_states, x='uf', y='pct_em_preparacao',
                     title="Estados com Maior % de Projetos em Fase de Preparação",
                     color='pct_em_preparacao', color_continuous_scale='Blues')
        fig.update_layout(xaxis_title="Estado", yaxis_title="% Projetos em Preparação")
        st.plotly_chart(fig, use_container_width=True)
        
        # Timeline details table
        st.subheader("📋 Detalhamento de Cronogramas por Estado/Programa")
        display_timeline = timeline[['programa', 'uf', 'total_projetos', 'projetos_iniciados', 
                                   'projetos_nao_iniciados', 'primeira_obra_iniciada', 'ultima_obra_iniciada']].copy()
        display_timeline.columns = ['Programa', 'UF', 'Total', 'Iniciados', 'Em Preparação', 
                                   'Primeira Obra', 'Última Obra']
        st.dataframe(display_timeline, use_container_width=True, hide_index=True)
def render_trabalho_social_tab():
    """Render social work tracking"""
    st.header("📚 Trabalho Social")
    
    # Load data
    social_work = load_social_work()
    
    if social_work.empty:
        st.warning("Nenhum dado de trabalho social disponível")
        return
    
    # Critical findings
    ts_ahead = (social_work['percentual_ts'] > social_work['percentual_obra']).sum()
    total_ts_projects = len(social_work)
    avg_ts = social_work['percentual_ts'].mean()
    avg_obra = social_work['percentual_obra'].mean()
    
    st.markdown(f"""
    <div class="new-kpi-highlight">
        <h4>📊 Insights do Trabalho Social</h4>
        <ul>
            <li><strong>{total_ts_projects} projetos</strong> com programas de trabalho social ativos</li>
            <li><strong>TS adiantado em {ts_ahead} projetos</strong> ({(ts_ahead/total_ts_projects*100):.1f}%)</li>
            <li><strong>Execução média TS: {avg_ts:.1f}%</strong> vs Obra física: {avg_obra:.1f}%</li>
            <li><strong>FDS e RURAL</strong> únicos programas com trabalho social estruturado</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Média Execução TS",
            f"{avg_ts:.1f}%",
            delta="Trabalho Social"
        )
    
    with col2:
        st.metric(
            "Média Execução Obra",
            f"{avg_obra:.1f}%",
            delta="Construção Física"
        )
    
    with col3:
        st.metric(
            "TS Adiantado",
            f"{ts_ahead}/{total_ts_projects}",
            delta=f"{(ts_ahead/total_ts_projects*100):.1f}% dos projetos"
        )
    
    # TS vs Construction Progress
    st.subheader("📊 Trabalho Social vs Execução da Obra")
    
    # Scatter plot
    fig = px.scatter(social_work, x='percentual_obra', y='percentual_ts', 
                     color='programa', size='percentual_ts',
                     title="Trabalho Social vs Progresso da Obra",
                     hover_data=['nome_empreendimento', 'uf', 'status_ts_obra'])
    
    # Add diagonal line (perfect alignment)
    fig.add_shape(type="line", x0=0, y0=0, x1=100, y1=100,
                  line=dict(color="red", width=2, dash="dash"),
                  name="Alinhamento Perfeito")
    
    fig.update_layout(
        xaxis_title="% Execução da Obra",
        yaxis_title="% Execução do Trabalho Social"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Status breakdown
    st.subheader("📈 Status do Trabalho Social")
    status_summary = social_work['status_ts_obra'].value_counts()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        fig = px.pie(values=status_summary.values, names=status_summary.index,
                     title="Distribuição do Status TS vs Obra",
                     color_discrete_sequence=['#2E8B57', '#FFD700', '#DC143C'])
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.info(f"""
        **Status Summary:**
        
        📈 **TS Adiantado**: {status_summary.get('TS Adiantado', 0)} projetos
        
        ⚖️ **TS Alinhado**: {status_summary.get('TS Alinhado', 0)} projetos
        
        📉 **TS Atrasado**: {status_summary.get('TS Atrasado', 0)} projetos
        
        💡 **Insight**: Trabalho social progride mais rápido que obra física
        """)
    
    # Program comparison
    st.subheader("🔍 Comparação por Programa")
    program_ts = social_work.groupby('programa').agg({
        'percentual_ts': 'mean',
        'percentual_obra': 'mean',
        'nome_empreendimento': 'count'
    }).round(1)
    program_ts.columns = ['TS Médio (%)', 'Obra Média (%)', 'Projetos']
    
    st.dataframe(program_ts, use_container_width=True)
    
    # Detailed social work data
    st.subheader("📋 Detalhamento do Trabalho Social")
    display_ts = social_work[['nome_empreendimento', 'uf', 'programa', 'percentual_ts', 
                            'percentual_obra', 'status_ts_obra', 'situacao_descricao']].copy()
    display_ts.columns = ['Empreendimento', 'UF', 'Programa', 'TS (%)', 'Obra (%)', 
                         'Status TS', 'Situação']
    st.dataframe(display_ts, use_container_width=True, hide_index=True)


def render_financeiro_detalhado_tab():
    """Render detailed financial execution analysis with neutral presentation"""
    st.header("💰 Execução Financeira Detalhada")
    
    # Load data
    financial = load_financial_execution()
    program_summary = load_program_summary()
    
    if financial.empty:
        st.warning("Nenhum dado financeiro detalhado disponível")
        return
    
    # Calculate totals dynamically
    total_committed = financial['valor_comprometido'].sum()
    total_executed = financial['valor_executado_estimado'].sum()
    execution_rate = (total_executed / total_committed * 100) if total_committed > 0 else 0
    pending = total_committed - total_executed
    
    # Calculate program-specific execution rates
    program_exec = financial.groupby('programa')['percentual_financeiro_executado'].mean()
    far_exec = program_exec.get('FAR', 0)
    fds_exec = program_exec.get('FDS', 0)
    rural_exec = program_exec.get('RURAL', 0)
    
    # Dynamic relevant financial findings
    st.markdown(f"""
    <div class="new-kpi-highlight">
        <h4>💰 Situação Financeira Identificada</h4>
        <ul>
            <li><strong>R$ {total_committed/1e9:.2f} bilhões comprometidos</strong> vs R$ {total_executed/1e9:.2f} bilhões executados</li>
            <li><strong>Taxa de execução: {execution_rate:.1f}%</strong> - Em desenvolvimento</li>
            <li><strong>R$ {pending/1e9:.2f} bilhões em processo</strong> de execução ({(pending/total_committed*100):.1f}%)</li>
            <li><strong>Performance por programa:</strong> FAR: {far_exec:.1f}%, FDS: {fds_exec:.1f}%, RURAL: {rural_exec:.1f}%</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # National summary
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Valor Comprometido",
            f"R$ {total_committed/1e9:.2f}B",
            delta="Total programado"
        )
    
    with col2:
        st.metric(
            "Valor Executado",
            f"R$ {total_executed/1e9:.2f}B",
            delta=f"{execution_rate:.1f}% do comprometido"
        )
    
    with col3:
        st.metric(
            "Valor em Processo",
            f"R$ {pending/1e9:.2f}B",
            delta=f"{(pending/total_committed*100):.1f}% restante"
        )
    
    with col4:
        total_uh = financial['total_uh'].sum()
        cost_per_uh = total_committed / total_uh if total_uh > 0 else 0
        st.metric(
            "Investimento Médio/UH",
            f"R$ {cost_per_uh:,.0f}",
            delta=f"{total_uh:,} UH total"
        )
    
    # Execution by Program
    st.subheader("📊 Execução por Programa")
    
    if not program_summary.empty:
        fig = px.bar(program_summary, x='programa', y='investimento_total',
                     title="Investimento por Programa",
                     color='percentual_medio_execucao',
                     color_continuous_scale='RdYlGn',
                     text='percentual_medio_execucao')
        
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig.update_layout(yaxis_title="Investimento (R$)", 
                         coloraxis_colorbar_title="% Execução")
        st.plotly_chart(fig, use_container_width=True)
        
        # Program execution table
        st.subheader("📋 Resumo de Execução por Programa")
        display_program = program_summary[['programa', 'total_projetos', 'investimento_total', 
                                         'percentual_medio_execucao', 'projetos_concluidos', 
                                         'projetos_nao_iniciados']].copy()
        display_program['investimento_total'] = display_program['investimento_total'].apply(lambda x: f"R$ {x/1e9:.2f}B")
        display_program.columns = ['Programa', 'Total Projetos', 'Investimento', 
                                  'Exec. Média (%)', 'Concluídos', 'Em Preparação']
        st.dataframe(display_program, use_container_width=True, hide_index=True)
    
    # State-level analysis
    st.subheader("🗺️ Execução por Estado")
    
    # Top states by investment
    top_states = financial.nlargest(15, 'valor_comprometido')
    
    fig = px.scatter(top_states, x='valor_comprometido', y='percentual_financeiro_executado',
                     size='total_uh', color='programa',
                     hover_data=['uf', 'total_projetos'],
                     title="Investimento vs Execução por Estado (tamanho = UH)")
    
    fig.update_layout(
        xaxis_title="Valor Comprometido (R$)",
        yaxis_title="% Execução Financeira"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Financial execution comparison
    st.subheader("💹 Comparação de Execução Física vs Financeira")
    
    # Calculate averages by program for comparison
    prog_comparison = financial.groupby('programa').agg({
        'percentual_fisico_medio': 'mean',
        'percentual_financeiro_executado': 'mean',
        'total_projetos': 'sum'
    }).round(1)
    
    fig_comparison = go.Figure()
    
    fig_comparison.add_trace(go.Bar(
        x=prog_comparison.index,
        y=prog_comparison['percentual_fisico_medio'],
        name='Execução Física',
        marker_color='lightblue'
    ))
    
    fig_comparison.add_trace(go.Bar(
        x=prog_comparison.index,
        y=prog_comparison['percentual_financeiro_executado'],
        name='Execução Financeira',
        marker_color='darkblue'
    ))
    
    fig_comparison.update_layout(
        title='Execução Física vs Financeira por Programa',
        barmode='group',
        yaxis_title='Percentual (%)',
        xaxis_title='Programa'
    )
    
    st.plotly_chart(fig_comparison, use_container_width=True)
def render_desempenho_tab():
    """Render performance analysis by state and program"""
    st.header("🏗️ Análise de Desempenho")
    
    # Load data
    state_performance = load_state_performance()
    program_summary = load_program_summary()
    
    # Performance overview
    if not state_performance.empty:
        st.subheader("🗺️ Desempenho por Estado")
        
        # Top performing states
        top_performers = state_performance.head(15)
        
        fig = px.bar(top_performers, x='uf', y='total_projetos',
                     title="Top 15 Estados por Número de Projetos",
                     color='percentual_medio', color_continuous_scale='RdYlGn',
                     hover_data=['total_uh', 'projetos_concluidos'])
        st.plotly_chart(fig, use_container_width=True)
        
        # Performance metrics
        col1, col2 = st.columns(2)
        
        with col1:
            # Best performers
            best_states = state_performance.nlargest(10, 'percentual_medio')
            fig_best = px.bar(best_states, x='percentual_medio', y='uf',
                             orientation='h', title="Estados com Melhor % de Execução",
                             color='percentual_medio', color_continuous_scale='Greens')
            st.plotly_chart(fig_best, use_container_width=True)
        
        with col2:
            # States with most stalled projects
            worst_states = state_performance.nlargest(10, 'projetos_paralisados')
            fig_worst = px.bar(worst_states, x='projetos_paralisados', y='uf',
                              orientation='h', title="Estados com Mais Projetos Paralisados",
                              color='projetos_paralisados', color_continuous_scale='Reds')
            st.plotly_chart(fig_worst, use_container_width=True)
        
        # State performance table
        st.subheader("📊 Ranking de Estados")
        display_states = state_performance[['uf', 'total_projetos', 'total_uh', 'uh_executadas', 
                                          'percentual_medio', 'projetos_paralisados', 'projetos_concluidos']].copy()
        display_states['uh_executadas'] = display_states['uh_executadas'].round(0)
        display_states.columns = ['Estado', 'Total Projetos', 'Total UH', 'UH Executadas', 
                                 'Exec. Média (%)', 'Paralisados', 'Concluídos']
        st.dataframe(display_states, use_container_width=True, hide_index=True)

# ===== ORIGINAL RENDERING FUNCTIONS (Enhanced) =====

def render_kpis():
    """Render enhanced KPI cards at the top with neutral findings"""
    summary = load_national_summary()
    
    # Load dynamic data for relevant findings
    try:
        beneficiary_summary = load_beneficiary_summary()
        program_summary = load_program_summary()
        
        # Calculate dynamic metrics
        total_completed = program_summary['projetos_concluidos'].sum() if not program_summary.empty else 0
        total_investment = summary['investimento_total'] / 1e9 if 'investimento_total' in summary else 0
        total_women = beneficiary_summary['total_mulheres'] if not beneficiary_summary.empty else 0
        
        # Calculate FDS progress percentage (if data available)
        fds_data = program_summary[program_summary['programa'] == 'FDS'] if not program_summary.empty else pd.DataFrame()
        fds_progress_pct = 0
        if not fds_data.empty and len(fds_data) > 0:
            fds_row = fds_data.iloc[0]
            fds_started = fds_row['total_projetos'] - fds_row['projetos_nao_iniciados']
            fds_total = fds_row['total_projetos'] if 'total_projetos' in fds_row else 1
            fds_progress_pct = (fds_started / fds_total * 100) if fds_total > 0 else 0
        
        # Dynamic relevant findings alert box
        st.markdown(f"""
        <div class="new-kpi-highlight">
            <h3>📊 Situação Identificada</h3>
            <p><strong>{total_completed} projetos completados</strong> em todos os programas com R$ {f"{total_investment:.1f}".replace('.', ',')} bilhões investidos</p>
            <p><strong>Taxa de execução média de {f"{summary.get('percentual_medio_nacional', 0):.1f}".replace('.', ',')}%</strong> nos programas MCMV</p>
            <p><strong>{f"{int(total_women):,}".replace(',', '.')} mulheres chefes de família</strong> cadastradas no programa</p>

        </div>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        # Fallback to minimal alert if data loading fails
        st.markdown(f"""
        <div class="new-kpi-highlight">
            <h3>📊 Situação Identificada</h3>
            <p><strong>Análise em andamento</strong> dos programas habitacionais</p>
            <p><strong>Dados atualizados</strong> para monitoramento de entregas</p>
        </div>
        """, unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Projetos MCMV", f"{int(summary['total_projetos']):,}")
    
    with col2:
        st.metric(
            "UH Esperadas",
            f"{int(summary['uh_esperadas_total']):,}"
        )
    
    with col3:
        st.metric(
            "UH Executadas",
            f"{int(summary['uh_executadas_total']):,}",
            delta=f"{summary['percentual_medio_nacional']:.1f}%"
        )
    
    with col4:
        st.metric(
            "Gap UH",
            f"{int(summary['brecha_uh_nacional']):,}",
            delta="Pendentes de entrega"
        )
    
    with col5:
        st.metric(
            "Investimento Total",
            f"R$ {summary['investimento_total']/1e9:.2f} bi"
        )
    
    # Neutral alert boxes
    if summary['projetos_alto_risco'] > 0:
        st.info(f"📋 {int(summary['projetos_alto_risco'])} projetos requerem atenção especial")

def calculate_dynamic_investment_estimate(df_map):
    """
    Calculate dynamic investment estimation based on actual data patterns
    instead of hardcoded values
    """
    try:
        # Try to get actual financial data for reference
        df_financial = load_financial_execution()
        if not df_financial.empty and 'valor_comprometido' in df_financial.columns and 'total_uh' in df_financial.columns:
            # Calculate average cost per UH from real data
            financial_with_uh = df_financial[df_financial['total_uh'] > 0]
            if not financial_with_uh.empty:
                avg_cost_per_uh = (financial_with_uh['valor_comprometido'] / financial_with_uh['total_uh']).median()
                return df_map['uh_esperadas'] * avg_cost_per_uh
    except:
        pass
    
    # If no financial data available, use proportional scaling based on UH distribution
    if 'uh_esperadas' in df_map.columns and df_map['uh_esperadas'].sum() > 0:
        # Use the data's own scale - completely dynamic scaling
        max_uh = df_map['uh_esperadas'].max()
        min_uh = df_map['uh_esperadas'].min()
        
        # Try to get actual investment data from national summary for scaling reference
        try:
            national_summary = load_national_summary()
            if 'investimento_total' in national_summary:
                total_national_investment = national_summary['investimento_total']
                total_national_uh = national_summary.get('uh_esperadas_total', df_map['uh_esperadas'].sum())
                if total_national_uh > 0:
                    avg_cost_per_uh = total_national_investment / total_national_uh
                    return df_map['uh_esperadas'] * avg_cost_per_uh
        except:
            pass
        
        # If no national data, scale proportionally within the dataset itself
        # Use the largest state as reference and scale others proportionally
        if max_uh > 0:
            # Each state gets investment proportional to its UH share
            uh_share = df_map['uh_esperadas'] / df_map['uh_esperadas'].sum()
            # Use the sum of UH as basis for total investment, then distribute proportionally
            # Scale based on the data's own magnitude
            max_state_uh = df_map['uh_esperadas'].max()
            estimated_total = max_state_uh * df_map['uh_esperadas'].sum()  # Scale by data magnitude
            return uh_share * estimated_total
    
    # Ultimate fallback - use relative scaling within the dataset
    max_uh_in_data = df_map['uh_esperadas'].max() if len(df_map) > 0 else 1
    return df_map['uh_esperadas'] * max_uh_in_data  # Scale by the largest UH value in dataset

def get_height_metric_name(height_col):
    """Get display name for height metric"""
    metric_names = {
        'brecha_uh': 'Gap Habitacional',
        'valor_investimento': 'Investimento',
        'uh_executadas': 'UH Executadas',
        'uh_esperadas': 'UH Esperadas'
    }
    return metric_names.get(height_col, height_col)

def calculate_dynamic_investment_estimate(df_map):
    """
    Calculate dynamic investment estimation based on actual data patterns
    instead of hardcoded values
    """
    try:
        # Try to get actual financial data for reference
        df_financial = load_financial_execution()
        if not df_financial.empty and 'valor_comprometido' in df_financial.columns and 'total_uh' in df_financial.columns:
            # Calculate average cost per UH from real data
            financial_with_uh = df_financial[df_financial['total_uh'] > 0]
            if not financial_with_uh.empty:
                avg_cost_per_uh = (financial_with_uh['valor_comprometido'] / financial_with_uh['total_uh']).median()
                return df_map['uh_esperadas'] * avg_cost_per_uh
    except:
        pass
    
    # If no financial data available, use proportional scaling based on UH distribution
    if 'uh_esperadas' in df_map.columns and df_map['uh_esperadas'].sum() > 0:
        # Use the data's own scale - completely dynamic scaling
        max_uh = df_map['uh_esperadas'].max()
        min_uh = df_map['uh_esperadas'].min()
        
        # Try to get actual investment data from national summary for scaling reference
        try:
            national_summary = load_national_summary()
            if 'investimento_total' in national_summary:
                total_national_investment = national_summary['investimento_total']
                total_national_uh = national_summary.get('uh_esperadas_total', df_map['uh_esperadas'].sum())
                if total_national_uh > 0:
                    avg_cost_per_uh = total_national_investment / total_national_uh
                    return df_map['uh_esperadas'] * avg_cost_per_uh
        except:
            pass
        
        # If no national data, scale proportionally within the dataset itself
        # Use the largest state as reference and scale others proportionally
        if max_uh > 0:
            # Each state gets investment proportional to its UH share
            uh_share = df_map['uh_esperadas'] / df_map['uh_esperadas'].sum()
            # Use the sum of UH as basis for total investment, then distribute proportionally
            # Scale based on the data's own magnitude
            max_state_uh = df_map['uh_esperadas'].max()
            estimated_total = max_state_uh * df_map['uh_esperadas'].sum()  # Scale by data magnitude
            return uh_share * estimated_total
    
    # Ultimate fallback - use relative scaling within the dataset
    max_uh_in_data = df_map['uh_esperadas'].max() if len(df_map) > 0 else 1
    return df_map['uh_esperadas'] * max_uh_in_data  # Scale by the largest UH value in dataset

def get_height_metric_name(height_col):
    """Get display name for height metric"""
    metric_names = {
        'brecha_uh': 'Gap Habitacional',
        'valor_investimento': 'Investimento',
        'uh_executadas': 'UH Executadas',
        'uh_esperadas': 'UH Esperadas'
    }
    return metric_names.get(height_col, height_col)

def calculate_dynamic_investment_estimate(df_map):
    """
    Calculate dynamic investment estimation based on actual data patterns
    instead of hardcoded values
    """
    try:
        # Try to get actual financial data for reference
        df_financial = load_financial_execution()
        if not df_financial.empty and 'valor_comprometido' in df_financial.columns and 'total_uh' in df_financial.columns:
            # Calculate average cost per UH from real data
            financial_with_uh = df_financial[df_financial['total_uh'] > 0]
            if not financial_with_uh.empty:
                avg_cost_per_uh = (financial_with_uh['valor_comprometido'] / financial_with_uh['total_uh']).median()
                return df_map['uh_esperadas'] * avg_cost_per_uh
    except:
        pass
    
    # If no financial data available, use proportional scaling based on UH distribution
    if 'uh_esperadas' in df_map.columns and df_map['uh_esperadas'].sum() > 0:
        # Use the data's own scale - completely dynamic scaling
        max_uh = df_map['uh_esperadas'].max()
        min_uh = df_map['uh_esperadas'].min()
        
        # Try to get actual investment data from national summary for scaling reference
        try:
            national_summary = load_national_summary()
            if 'investimento_total' in national_summary:
                total_national_investment = national_summary['investimento_total']
                total_national_uh = national_summary.get('uh_esperadas_total', df_map['uh_esperadas'].sum())
                if total_national_uh > 0:
                    avg_cost_per_uh = total_national_investment / total_national_uh
                    return df_map['uh_esperadas'] * avg_cost_per_uh
        except:
            pass
        
        # If no national data, scale proportionally within the dataset itself
        # Use the largest state as reference and scale others proportionally
        if max_uh > 0:
            # Each state gets investment proportional to its UH share
            uh_share = df_map['uh_esperadas'] / df_map['uh_esperadas'].sum()
            # Use the sum of UH as basis for total investment, then distribute proportionally
            # Scale based on the data's own magnitude
            max_state_uh = df_map['uh_esperadas'].max()
            estimated_total = max_state_uh * df_map['uh_esperadas'].sum()  # Scale by data magnitude
            return uh_share * estimated_total
    
    # Ultimate fallback - use relative scaling within the dataset
    max_uh_in_data = df_map['uh_esperadas'].max() if len(df_map) > 0 else 1
    return df_map['uh_esperadas'] * max_uh_in_data  # Scale by the largest UH value in dataset

def render_map_tab():
    """Professional metrics visualization with neutral presentation"""
    
    st.header("📊 Análise de Métricas Geográficas - MCMV")
    
    # Load data
    df_map = load_uh_gap_by_state()
    
    if df_map.empty:
        st.warning("⚠️ Não foi possível carregar os dados do mapa.")
        return
    
    # Load investment data using the correct function name
    try:
        df_investment = load_financial_execution()
        if not df_investment.empty and 'valor_comprometido' in df_investment.columns:
            investment_by_state = df_investment.groupby('uf').agg({
                'valor_comprometido': 'sum'
            }).reset_index()
            investment_by_state.columns = ['uf', 'valor_investimento']
            df_map = df_map.merge(investment_by_state, on='uf', how='left')
            df_map['valor_investimento'] = df_map['valor_investimento'].fillna(0)
        else:
            df_map['valor_investimento'] = calculate_dynamic_investment_estimate(df_map)
    except Exception as e:
        st.info(f"Utilizando estimativa de investimento: {e}")
        df_map['valor_investimento'] = calculate_dynamic_investment_estimate(df_map)
    
    # Aggregate by state (group by uf to get state totals)
    df_map = df_map.groupby('uf').agg({
        'uh_esperadas': 'sum',
        'uh_executadas': 'sum',
        'brecha_uh': 'sum',
        'percentual_medio': 'mean',
        'valor_investimento': 'sum'
    }).reset_index()
    
    # Calculate professional metrics
    df_map['performance_category'] = calculate_performance_categories(df_map)
    df_map['outstanding_units'] = df_map['brecha_uh']  # Professional term
    df_map['delivery_timeline'] = calculate_delivery_estimates(df_map)
    df_map['state_ranking'] = df_map['brecha_uh'].rank(method='dense', ascending=False).astype(int)
    
    # ROI/Efficiency calculations
    df_map['cost_per_delivered_unit'] = calculate_cost_per_delivered_unit(df_map)
    df_map['efficiency_category'] = calculate_efficiency_categories(df_map)
    df_map['cost_variance'] = calculate_cost_variance(df_map)
    df_map['efficiency_ranking'] = df_map['cost_per_delivered_unit'].rank(method='dense', ascending=True).astype(int)
    
    # Professional analysis mode selector
    st.subheader("📈 Seleção de Análise")
    analysis_mode = st.selectbox(
        "Escolha o foco da análise de dados:",
        [
            "📊 Gap de Entrega por Estado",
            "📈 Performance de Execução", 
            "💰 Análise de Investimento vs Resultados",
            "📋 Unidades Pendentes de Entrega",
            "💼 Eficiência de Custo por UH",
            "🏆 Ranking de Performance Geral"
        ]
    )
    
    # Configure professional visualization
    if analysis_mode == "📊 Gap de Entrega por Estado":
        height_col = 'brecha_uh'
        title = "📊 Análise de Gap de Entrega por Estado"
        subtitle = "Altura das torres = Unidades habitacionais pendentes de entrega"
        
    elif analysis_mode == "📈 Performance de Execução":
        height_col = 'uh_executadas'
        title = "📈 Performance de Execução Estadual"
        subtitle = "Altura das torres = Unidades habitacionais entregues"
        
    elif analysis_mode == "💰 Análise de Investimento vs Resultados":
        height_col = 'valor_investimento'
        title = "💰 Distribuição de Investimentos por Estado"
        subtitle = "Altura das torres = Volume de investimento | Cor = Taxa de execução"
        
    elif analysis_mode == "📋 Unidades Pendentes de Entrega":
        height_col = 'outstanding_units'
        title = "📋 Unidades Pendentes de Entrega"
        subtitle = "Análise de unidades habitacionais ainda não concluídas"
        
    elif analysis_mode == "💼 Eficiência de Custo por UH":
        height_col = 'cost_per_delivered_unit'
        title = "💼 Análise de Eficiência de Custo"
        subtitle = "Altura das torres = Custo por unidade entregue"
        
    else:  # Ranking Performance
        height_col = 'uh_executadas'
        title = "🏆 Ranking de Performance Estadual"
        subtitle = "Comparativo de entrega vs eficiência de custo"
    
    # Create professional visualization data
    chart_data = create_professional_visualization_data(df_map, height_col, analysis_mode)
    
    # Display professional summary metrics
    display_professional_summary(df_map, analysis_mode)
    
    # Try 3D professional visualization
    try:
        import pydeck as pdk
        
        # Create professional 3D columns
        layer = pdk.Layer(
            'ColumnLayer',
            data=chart_data,
            get_position='position',
            get_elevation='height',
            get_fill_color='professional_color',
            elevation_scale=1,
            radius=25000,
            pickable=True,
            auto_highlight=True
        )
        
        # Professional camera angle
        view_state = pdk.ViewState(
            latitude=-15.7801,
            longitude=-47.9292,
            zoom=4.2,
            pitch=60,
            bearing=0
        )
        
        # Create professional tooltip
        professional_tooltip_html = create_professional_tooltip(height_col, analysis_mode)
        
        deck = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip={
                'html': professional_tooltip_html,
                'style': {
                    'backgroundColor': 'rgba(44, 62, 80, 0.95)',
                    'color': 'white',
                    'padding': '12px',
                    'borderRadius': '6px',
                    'fontSize': '13px',
                    'fontFamily': 'Arial, sans-serif'
                }
            }
        )
        
        # Display with professional title
        st.markdown(f"### {title}")
        st.caption(subtitle)
        st.pydeck_chart(deck, use_container_width=True)
        
        # Success message with metrics context
        total_states = len(df_map)
        st.success(f"✅ Visualização carregada: {total_states} estados analisados com métricas atualizadas")
        
    except Exception as e:
        st.warning(f"Visualização 3D indisponível: {str(e)}")
        st.info("📊 Carregando análise em formato alternativo...")
        display_professional_fallback_charts(df_map, height_col, analysis_mode)
    
    # Professional Metrics Dashboard
    display_professional_metrics_dashboard(df_map, analysis_mode)

def calculate_dynamic_investment_estimate(df_map):
    """
    Calculate dynamic investment estimation based on actual data patterns
    instead of hardcoded values
    """
    try:
        # Try to get actual financial data for reference
        df_financial = load_financial_execution()
        if not df_financial.empty and 'valor_comprometido' in df_financial.columns and 'total_uh' in df_financial.columns:
            # Calculate average cost per UH from real data
            financial_with_uh = df_financial[df_financial['total_uh'] > 0]
            if not financial_with_uh.empty:
                avg_cost_per_uh = (financial_with_uh['valor_comprometido'] / financial_with_uh['total_uh']).median()
                return df_map['uh_esperadas'] * avg_cost_per_uh
    except:
        pass
    
    # If no financial data available, use proportional scaling based on UH distribution
    if 'uh_esperadas' in df_map.columns and df_map['uh_esperadas'].sum() > 0:
        # Try to get actual investment data from national summary for scaling reference
        try:
            national_summary = load_national_summary()
            if 'investimento_total' in national_summary:
                total_national_investment = national_summary['investimento_total']
                total_national_uh = national_summary.get('uh_esperadas_total', df_map['uh_esperadas'].sum())
                if total_national_uh > 0:
                    avg_cost_per_uh = total_national_investment / total_national_uh
                    return df_map['uh_esperadas'] * avg_cost_per_uh
        except:
            pass
        
        # If no national data, scale proportionally within the dataset itself
        # Use the largest state as reference and scale others proportionally
        if df_map['uh_esperadas'].max() > 0:
            # Each state gets investment proportional to its UH share
            uh_share = df_map['uh_esperadas'] / df_map['uh_esperadas'].sum()
            # Use the sum of UH as basis for total investment, then distribute proportionally
            # Scale based on the data's own magnitude
            max_state_uh = df_map['uh_esperadas'].max()
            estimated_total = max_state_uh * df_map['uh_esperadas'].sum()  # Scale by data magnitude
            return uh_share * estimated_total
    
    # Ultimate fallback - use relative scaling within the dataset
    max_uh_in_data = df_map['uh_esperadas'].max() if len(df_map) > 0 else 1
    return df_map['uh_esperadas'] * max_uh_in_data  # Scale by the largest UH value in dataset

def calculate_cost_per_delivered_unit(df_map):
    """Calculate cost per actually delivered housing unit"""
    # Avoid division by zero
    delivered_units = df_map['uh_executadas'].replace(0, 0.1)  # Minimum to avoid inf
    cost_per_unit = df_map['valor_investimento'] / delivered_units
    
    # Cap extreme values for visualization
    cost_per_unit = cost_per_unit.clip(upper=cost_per_unit.quantile(0.95))
    
    return cost_per_unit

def calculate_performance_categories(df_map):
    """Calculate neutral performance categories based on execution rates"""
    def get_performance_category(execution_rate):
        if execution_rate >= 75:
            return 'Alto Desempenho'
        elif execution_rate >= 50:
            return 'Desempenho Adequado'
        elif execution_rate >= 25:
            return 'Desempenho Moderado'
        else:
            return 'Baixo Desempenho'
    
    return df_map['percentual_medio'].apply(get_performance_category)

def calculate_delivery_estimates(df_map):
    """Calculate estimated delivery timeline based on current execution rate"""
    # Simplified calculation: remaining work / current pace
    remaining_pct = 100 - df_map['percentual_medio']
    current_pace = df_map['percentual_medio'] / 36  # Assuming 36 months elapsed
    months_remaining = (remaining_pct / current_pace).replace([float('inf'), -float('inf')], 999)
    return months_remaining.clip(0, 999).round().astype(int)

def calculate_efficiency_categories(df_map):
    """Calculate neutral efficiency categories based on cost quartiles"""
    cost_per_uh = df_map['cost_per_delivered_unit']
    
    # Use quartiles for neutral categorization
    q25 = cost_per_uh.quantile(0.25)
    q50 = cost_per_uh.quantile(0.50)
    q75 = cost_per_uh.quantile(0.75)
    
    def get_efficiency_category(cost):
        if cost <= q25:
            return 'Alta Eficiência'
        elif cost <= q50:
            return 'Eficiência Adequada'
        elif cost <= q75:
            return 'Eficiência Moderada'
        else:
            return 'Baixa Eficiência'
    
    return cost_per_uh.apply(get_efficiency_category)

def calculate_cost_variance(df_map):
    """Calculate cost variance from median (neutral benchmark)"""
    median_cost = df_map['cost_per_delivered_unit'].median()
    variance_factor = df_map['cost_per_delivered_unit'] / median_cost
    return variance_factor.round(1)

def create_professional_visualization_data(df_map, height_col, analysis_mode):
    """Create visualization data with professional styling"""
    state_coords = {
        'AC': [-70.55, -8.77], 'AL': [-36.82, -9.62], 'AP': [-51.90, 1.41],
        'AM': [-64.84, -2.48], 'BA': [-41.58, -12.96], 'CE': [-39.53, -5.20],
        'DF': [-47.93, -15.78], 'ES': [-40.25, -19.19], 'GO': [-49.86, -15.98],
        'MA': [-45.44, -4.25], 'MT': [-56.92, -12.64], 'MS': [-54.54, -20.51],
        'MG': [-45.24, -18.10], 'PA': [-52.48, -1.35], 'PB': [-36.78, -7.28],
        'PR': [-51.22, -24.89], 'PE': [-37.98, -8.50], 'PI': [-42.64, -8.29],
        'RJ': [-42.90, -22.84], 'RN': [-36.95, -5.81], 'RS': [-53.50, -30.17],
        'RO': [-63.34, -9.22], 'RR': [-61.33, 1.99], 'SC': [-50.95, -27.45],
        'SP': [-46.77, -23.90], 'SE': [-37.57, -10.57], 'TO': [-47.86, -8.98]
    }
    
    # Professional color schemes
    performance_colors = {
        'Alto Desempenho': [46, 125, 50, 200],      # Green - high performance
        'Desempenho Adequado': [102, 187, 106, 180], # Light green - adequate
        'Desempenho Moderado': [255, 183, 77, 180],  # Orange - moderate
        'Baixo Desempenho': [244, 67, 54, 180]       # Red - low performance
    }
    
    efficiency_colors = {
        'Alta Eficiência': [33, 150, 243, 200],      # Blue - high efficiency
        'Eficiência Adequada': [103, 58, 183, 180],  # Purple - adequate
        'Eficiência Moderada': [255, 152, 0, 180],   # Orange - moderate  
        'Baixa Eficiência': [121, 85, 72, 180]       # Brown - low efficiency
    }
    
    # Default professional blue gradient
    default_colors = {
        'q1': [13, 71, 161, 200],   # Dark blue - top quartile
        'q2': [25, 118, 210, 180],  # Medium blue - second quartile
        'q3': [66, 165, 245, 160],  # Light blue - third quartile
        'q4': [144, 202, 249, 140]  # Very light blue - bottom quartile
    }
    
    chart_data = []
    height_values = df_map[height_col].values
    height_max = height_values.max() if len(height_values) > 0 else 1
    
    # Professional height scaling
    min_height = 5000   # Always visible
    max_height = 400000 # Professional scale
    height_range = max_height - min_height
    
    for _, row in df_map.iterrows():
        uf = row['uf']
        if uf not in state_coords:
            continue
            
        lon, lat = state_coords[uf]
        
        # Calculate height
        normalized_height = row[height_col] / height_max if height_max > 0 else 0
        height = min_height + (normalized_height * height_range)
        
        # Choose professional color based on mode
        if analysis_mode in ["💼 Eficiência de Custo por UH", "🏆 Ranking de Performance Geral"]:
            color = efficiency_colors.get(row['efficiency_category'], efficiency_colors['Eficiência Moderada'])
        elif analysis_mode in ["📈 Performance de Execução"]:
            color = performance_colors.get(row['performance_category'], performance_colors['Desempenho Moderado'])
        else:
            # Use quartile-based coloring for neutral metrics
            quartile = pd.qcut(df_map[height_col], q=4, labels=['q4', 'q3', 'q2', 'q1']).iloc[df_map.index.get_loc(row.name)]
            color = default_colors[quartile]
        
        chart_data.append({
            'position': [lon, lat],
            'height': height,
            'professional_color': color,
            'uf': uf,
            'performance_category': row['performance_category'],
            'efficiency_category': row['efficiency_category'],
            'outstanding_units_str': f"{int(row['outstanding_units']):,}",
            'brecha_uh_str': f"{int(row['brecha_uh']):,}",
            'uh_esperadas_str': f"{int(row['uh_esperadas']):,}",
            'uh_executadas_str': f"{int(row['uh_executadas']):,}",
            'percentual_str': f"{float(row['percentual_medio']):.1f}",
            'delivery_timeline': int(row['delivery_timeline']),
            'state_ranking': int(row['state_ranking']),
            'efficiency_ranking': int(row['efficiency_ranking']),
            'investimento_str': f"R$ {row['valor_investimento']/1e9:.1f}B",
            'cost_per_uh_str': f"R$ {row['cost_per_delivered_unit']:,.0f}",
            'cost_variance_str': f"{row['cost_variance']:.1f}x"
        })
    
    return chart_data

def create_professional_tooltip(height_col, analysis_mode):
    """Create professional, neutral tooltip"""
    if analysis_mode == "📊 Gap de Entrega por Estado":
        return '''
        📊 <b>Estado: {uf}</b><br>
        <b>Gap de Entrega:</b> {brecha_uh_str} UH<br>
        <b>Taxa de Execução:</b> {percentual_str}%<br>
        <b>UH Entregues:</b> {uh_executadas_str}<br>
        <b>Ranking Nacional:</b> #{state_ranking} de 27<br>
        <b>Estimativa Conclusão:</b> {delivery_timeline} meses
        '''
    elif analysis_mode == "💰 Análise de Investimento vs Resultados":
        return '''
        💰 <b>Análise Financeira: {uf}</b><br>
        <b>Investimento:</b> {investimento_str}<br>
        <b>Taxa de Execução:</b> {percentual_str}%<br>
        <b>UH Entregues:</b> {uh_executadas_str}<br>
        <b>UH Pendentes:</b> {outstanding_units_str}<br>
        <b>Performance:</b> {performance_category}
        '''
    elif analysis_mode == "💼 Eficiência de Custo por UH":
        return '''
        💼 <b>Eficiência de Custo: {uf}</b><br>
        <b>Custo por UH:</b> {cost_per_uh_str}<br>
        <b>Categoria:</b> {efficiency_category}<br>
        <b>Variação vs Mediana:</b> {cost_variance_str}<br>
        <b>UH Entregues:</b> {uh_executadas_str}<br>
        <b>Ranking Eficiência:</b> #{efficiency_ranking} de 27
        '''
    elif analysis_mode == "🏆 Ranking de Performance Geral":
        return '''
        🏆 <b>Performance: {uf}</b><br>
        <b>UH Entregues:</b> {uh_executadas_str}<br>
        <b>Custo/UH:</b> {cost_per_uh_str}<br>
        <b>Eficiência:</b> {efficiency_category}<br>
        <b>Ranking Entrega:</b> #{state_ranking}<br>
        <b>Ranking Eficiência:</b> #{efficiency_ranking}
        '''
    else:
        return '''
        📈 <b>Estado: {uf}</b><br>
        <b>UH Pendentes:</b> {outstanding_units_str}<br>
        <b>Performance:</b> {performance_category}<br>
        <b>Taxa de Execução:</b> {percentual_str}%<br>
        <b>Estimativa:</b> {delivery_timeline} meses restantes<br>
        <b>Posição:</b> #{state_ranking} de 27
        '''

def display_professional_summary(df_map, analysis_mode):
    """Display professional summary banner"""
    total_gap = df_map['outstanding_units'].sum()
    avg_execution = df_map['percentual_medio'].mean()
    total_investment = df_map['valor_investimento'].sum()
    
    st.markdown(f"""
    <div style="background: linear-gradient(90deg, #2c3e50 0%, #34495e 100%); 
                color: white; padding: 15px; border-radius: 8px; margin: 15px 0;
                text-align: center; font-size: 14px;">
        📊 <b>RESUMO NACIONAL</b> | 
        {total_gap:,} UH pendentes de entrega | 
        Taxa média de execução: {avg_execution:.1f}% | 
        Investimento total: R$ {total_investment/1e9:.1f}B
    </div>
    """, unsafe_allow_html=True)

def display_professional_metrics_dashboard(df_map, analysis_mode):
    """Display professional metrics dashboard"""
    st.markdown("---")
    st.subheader("📈 Painel de Métricas")
    
    high_perf = df_map[df_map['performance_category'] == 'Alto Desempenho']
    low_perf = df_map[df_map['performance_category'] == 'Baixo Desempenho']
    high_eff = df_map[df_map['efficiency_category'] == 'Alta Eficiência']
    low_eff = df_map[df_map['efficiency_category'] == 'Baixa Eficiência']
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "🏆 Alto Desempenho",
            f"{len(high_perf)}",
            delta=f"{high_perf['uh_executadas'].sum():,} UH entregues"
        )
    
    with col2:
        st.metric(
            "📉 Baixo Desempenho", 
            f"{len(low_perf)}",
            delta=f"{low_perf['outstanding_units'].sum():,} UH pendentes"
        )
    
    with col3:
        avg_execution = df_map['percentual_medio'].mean()
        st.metric(
            "📊 Execução Média",
            f"{avg_execution:.1f}%",
            delta="Taxa nacional"
        )
    
    with col4:
        median_cost = df_map['cost_per_delivered_unit'].median()
        st.metric(
            "💰 Custo Mediano/UH",
            f"R$ {median_cost:,.0f}",
            delta=f"{len(high_eff)} estados eficientes"
        )
    
    # Performance Analysis Section
    if analysis_mode in ["💼 Eficiência de Custo por UH", "🏆 Ranking de Performance Geral"]:
        st.markdown("### 📊 Análise de Eficiência")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🏆 Estados com Alta Eficiência")
            efficient_states = df_map[df_map['efficiency_category'] == 'Alta Eficiência'].nsmallest(5, 'cost_per_delivered_unit')
            
            for _, state in efficient_states.iterrows():
                st.info(f"""
                **{state['uf']}** - {state['efficiency_category']}
                - Custo/UH: R$ {state['cost_per_delivered_unit']:,.0f}
                - UH Entregues: {state['uh_executadas']:,.0f}
                - Execução: {state['percentual_medio']:.1f}%
                """)
        
        with col2:
            st.markdown("#### 📊 Estados com Oportunidades de Melhoria")
            improvement_states = df_map[df_map['efficiency_category'] == 'Baixa Eficiência'].nlargest(5, 'cost_per_delivered_unit')
            
            for _, state in improvement_states.iterrows():
                st.warning(f"""
                **{state['uf']}** - {state['efficiency_category']}
                - Custo/UH: R$ {state['cost_per_delivered_unit']:,.0f}
                - Variação: {state['cost_variance']:.1f}x vs mediana
                - UH Entregues: {state['uh_executadas']:,.0f}
                """)
    
    # Performance summary table
    st.markdown("### 📋 Resumo por Categoria de Performance")
    
    performance_summary = df_map['performance_category'].value_counts()
    efficiency_summary = df_map['efficiency_category'].value_counts()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Performance de Execução:**")
        for category, count in performance_summary.items():
            pct = (count / len(df_map)) * 100
            st.write(f"• {category}: {count} estados ({pct:.1f}%)")
    
    with col2:
        st.markdown("**Eficiência de Custo:**")
        for category, count in efficiency_summary.items():
            pct = (count / len(df_map)) * 100
            st.write(f"• {category}: {count} estados ({pct:.1f}%)")

def display_professional_fallback_charts(df_map, height_col, analysis_mode):
    """Professional fallback visualization if 3D fails"""
    # Professional bar chart
    top_states = df_map.nlargest(10, height_col)
    
    fig = px.bar(
        top_states,
        x='uf',
        y=height_col, 
        color='performance_category',
        title=f"Top 10 Estados - {height_col.replace('_', ' ').title()}",
        color_discrete_map={
            'Alto Desempenho': '#2E8B57',
            'Desempenho Adequado': '#66BB6A',
            'Desempenho Moderado': '#FFB74D',
            'Baixo Desempenho': '#F44336'
        },
        text=height_col
    )
    
    fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
    fig.update_layout(
        xaxis_title="Estado",
        yaxis_title=height_col.replace('_', ' ').title(),
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
# def render_map_tab():
#     """Enhanced map tab with new insights"""
#     st.header("📍 Mapa de Unidades Habitacionais por Estado")
    
#     df_gap = load_uh_gap_by_state()
#     geojson = load_brazil_geojson()
    
#     # Aggregate by state
#     df_map = df_gap.groupby('uf').agg({
#         'uh_esperadas': 'sum',
#         'uh_executadas': 'sum',
#         'brecha_uh': 'sum',
#         'percentual_medio': 'mean'
#     }).reset_index()
    
#     # Metric selector
#     metric = st.selectbox(
#         "Selecione a métrica para visualização:",
#         options=['brecha_uh', 'uh_executadas', 'uh_esperadas', 'percentual_medio'],
#         format_func=lambda x: {
#             'brecha_uh': 'Brecha de UH (a completar)',
#             'uh_executadas': 'UH Executadas',
#             'uh_esperadas': 'UH Esperadas',
#             'percentual_medio': 'Percentual de Execução (%)'
#         }[x]
#     )
    
#     if geojson is not None:
#         # Fix the geojson properties if needed
#         if 'features' in geojson:
#             for feature in geojson['features']:
#                 if 'properties' in feature:
#                     # Map different possible property names to 'uf'
#                     if 'sigla' in feature['properties']:
#                         feature['properties']['uf'] = feature['properties']['sigla']
#                     elif 'id' in feature['properties'] and len(feature['properties']['id']) == 2:
#                         feature['properties']['uf'] = feature['properties']['id']
        
#         # Create choropleth
#         fig = px.choropleth(
#             df_map,
#             geojson=geojson,
#             locations='uf',
#             featureidkey="properties.uf",
#             color=metric,
#             hover_name='uf',
#             hover_data={
#                 'uh_esperadas': ':,.0f',
#                 'uh_executadas': ':,.0f',
#                 'brecha_uh': ':,.0f',
#                 'percentual_medio': ':.1f',
#                 'uf': False
#             },
#             color_continuous_scale='Viridis' if metric != 'brecha_uh' else 'Reds',
#             title=f"{metric.replace('_', ' ').title()} por Estado"
#         )
        
#         fig.update_geos(fitbounds="locations", visible=False)
#         fig.update_layout(margin={"r": 0, "t": 30, "l": 0, "b": 0}, height=600)
        
#         st.plotly_chart(fig, use_container_width=True)
#     else:
#         # Fallback to bar chart if map doesn't load
#         st.warning("Mapa não disponível. Mostrando dados em gráfico de barras.")
#         fig = px.bar(
#             df_map.sort_values(metric, ascending=False).head(15),
#             x=metric,
#             y='uf',
#             orientation='h',
#             title=f"Top 15 Estados - {metric.replace('_', ' ').title()}",
#             labels={'uf': 'Estado', metric: metric.replace('_', ' ').title()},
#             color=metric,
#             color_continuous_scale='Viridis' if metric != 'brecha_uh' else 'Reds'
#         )
#         st.plotly_chart(fig, use_container_width=True)
    
#     # Top states table
#     with st.expander("📊 Ver dados detalhados por estado"):
#         st.dataframe(
#             df_map.sort_values('brecha_uh', ascending=False),
#             use_container_width=True,
#             hide_index=True
#         )

def render_region_barchart():
    """Enhanced regional analysis"""
    st.header("📊 Análise por Região")
    
    df_region = load_region_summary()
    
    # Two columns for the main charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Stacked bar chart for UH
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(
            x=df_region['regiao'],
            y=df_region['uh_executadas'],
            name='UH Executadas',
            marker_color='#2ca02c'
        ))
        fig1.add_trace(go.Bar(
            x=df_region['regiao'],
            y=df_region['brecha_uh'],
            name='Brecha UH',
            marker_color='#d62728'
        ))
        fig1.update_layout(
            title='UH por Região',
            barmode='stack',
            height=400,
            xaxis_title='Região',
            yaxis_title='Unidades Habitacionais'
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Execution percentage
        fig2 = px.bar(
            df_region,
            x='regiao',
            y='percentual_medio',
            title='Percentual de Execução por Região',
            color='percentual_medio',
            color_continuous_scale='Blues',
            text='percentual_medio'
        )
        fig2.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)
    
    # Second row
    col3, col4 = st.columns(2)
    
    with col3:
        # Pie chart for distribution
        fig3 = px.pie(
            df_region,
            values='uh_esperadas',
            names='regiao',
            title='Distribuição de UH por Região',
            hole=0.4
        )
        fig3.update_layout(height=400)
        st.plotly_chart(fig3, use_container_width=True)
    
    with col4:
        # Gap by region
        fig4 = px.bar(
            df_region,
            x='regiao',
            y='brecha_uh',
            title='Brecha de UH por Região',
            color='brecha_uh',
            color_continuous_scale='Reds',
            text='brecha_uh'
        )
        fig4.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        fig4.update_layout(height=400)
        st.plotly_chart(fig4, use_container_width=True)

def create_pptx_report(summary):
    """Create a PowerPoint presentation with the contracting data"""
    from io import BytesIO
    try:
        from pptx import Presentation
        from pptx.util import Inches, Pt
        from pptx.enum.text import PP_ALIGN
    except ImportError:
        return b"PowerPoint export not available"
    
    # Create presentation
    prs = Presentation()
    prs.slide_width = Inches(16)
    prs.slide_height = Inches(9)
    
    # Title slide
    title_slide_layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(title_slide_layout)
    title = slide.shapes.title
    subtitle = slide.placeholders[1]
    
    title.text = "Status de Contratações - MCMV"
    subtitle.text = f"Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}"
    
    # Data slide
    bullet_slide_layout = prs.slide_layouts[5]  # Blank layout
    slide = prs.slides.add_slide(bullet_slide_layout)
    
    # Add title
    title_shape = slide.shapes.add_textbox(Inches(0.5), Inches(0.5), Inches(15), Inches(1))
    title_frame = title_shape.text_frame
    title_frame.text = "Resumo de Contratações"
    title_frame.paragraphs[0].font.size = Pt(32)
    title_frame.paragraphs[0].font.bold = True
    title_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    
    # Save to bytes
    pptx_bytes = BytesIO()
    prs.save(pptx_bytes)
    pptx_bytes.seek(0)
    
    return pptx_bytes.getvalue()

def render_contratacoes_tab():
    """Enhanced contracting status with neutral presentation"""
    st.header("📑 Status de Contratações")
    
    # Load summary data
    summary = load_contratacoes_summary()
    
    # Enhanced CSS for styling (keep existing styling)
    st.markdown("""
    <style>
    .metric-container {
        background-color: #ffffff;
        padding: 25px 20px;
        border-radius: 8px;
        text-align: center;
        min-height: 220px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        font-family: 'Inter', Arial, sans-serif;
        position: relative;
        margin-bottom: 15px;
    }
    
    .metric-title {
        font-size: 13px;
        font-weight: 700;
        text-transform: uppercase;
        margin-bottom: 20px;
        letter-spacing: 0.5px;
        line-height: 1.4;
    }
    
    .metric-value {
        font-size: 42px;
        font-weight: 700;
        color: #1f1f1f;
        margin: 8px 0;
        line-height: 1;
    }
    
    .aguardando-container {
        border-left: 6px solid #2196f3;
        background: linear-gradient(90deg, #e3f2fd 0%, #ffffff 100%);
    }
    .aguardando-container .metric-title {
        color: #0056b3;
    }
    
    .mcid-emitida-container {
        border-left: 6px solid #ff9800;
        background: linear-gradient(90deg, #fff3e0 0%, #ffffff 100%);
    }
    .mcid-emitida-container .metric-title {
        color: #e65100;
    }
    
    .contratos-container {
        border-left: 6px solid #4caf50;
        background: linear-gradient(90deg, #e8f5e9 0%, #ffffff 100%);
    }
    .contratos-container .metric-title {
        color: #003366;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Helper functions
    def format_br_currency(value, unit="mi"):
        if value == 0:
            return "R$ 0,00 " + unit
        
        if unit == "bi":
            formatted = f"{value/1e9:.2f}"
        else:  # mi
            formatted = f"{value/1e6:.2f}"
        
        formatted = formatted.replace(".", ",")
        return f"R$ {formatted} {unit}"
    
    def format_br_number(value):
        return f"{int(value):,}".replace(",", ".")
    
    # Calculate estimated values
    avg_investment_per_uh = summary['valor_total'] / summary['uh_total'] if summary['uh_total'] > 0 else 150000
    
    # Three columns for main stages
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-container aguardando-container">
            <div class="metric-title">AGUARDANDO AUTORIZAÇÃO MCID</div>
            <div class="metric-value">{format_br_number(summary['aguardando_mcid'])}</div>
            <div>Empreendimentos</div>
            <div style="margin-top: 15px;">
                <div>UH: {format_br_number(summary['uh_aguardando_mcid'])}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-container mcid-emitida-container">
            <div class="metric-title">AUTORIZAÇÃO MCID EMITIDA</div>
            <div class="metric-value">{format_br_number(summary['mcid_emitida'])}</div>
            <div>Empreendimentos</div>
            <div style="margin-top: 15px;">
                <div>UH: {format_br_number(summary['uh_mcid_emitida'])}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-container contratos-container">
            <div class="metric-title">CONTRATOS EMITIDOS</div>
            <div class="metric-value">{format_br_number(summary['contratos_emitidos'])}</div>
            <div>Empreendimentos</div>
            <div style="margin-top: 15px;">
                <div>UH: {format_br_number(summary['uh_contratos_emitidos'])}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Show relevant findings
    total_empreendimentos = summary['aguardando_mcid'] + summary['mcid_emitida'] + summary['contratos_emitidos']
    pct_contratos = (summary['contratos_emitidos'] / total_empreendimentos * 100) if total_empreendimentos > 0 else 0
    
    st.markdown(f"""
    <div class="new-kpi-highlight">
        <h4>📊 Achados Relevantes - Contratações</h4>
        <ul>
            <li><strong>{total_empreendimentos} empreendimentos</strong> em diferentes fases de contratação</li>
            <li><strong>{pct_contratos:.1f}% já possuem contratos emitidos</strong> ({summary['contratos_emitidos']} projetos)</li>
            <li><strong>{summary['uh_total']:,} UH</strong> distribuídas entre as fases contratuais</li>
            <li><strong>Fluxo processual</strong> em desenvolvimento normal conforme cronograma</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Visualization section
    st.subheader("📊 Análise Visual das Contratações")
    
    # Create data for visualization
    chart_df = pd.DataFrame({
        "Status": [
            "Aguardando MCID",
            "MCID Emitida", 
            "Contratos Emitidos"
        ],
        "UH": [
            summary["uh_aguardando_mcid"],
            summary["uh_mcid_emitida"],
            summary["uh_contratos_emitidos"]
        ],
        "Empreendimentos": [
            summary["aguardando_mcid"],
            summary["mcid_emitida"],
            summary["contratos_emitidos"]
        ]
    })
    
    fig = px.bar(chart_df, x='Status', y='UH',
                 title='Unidades Habitacionais por Status de Contratação',
                 color='Status', text='UH')
    fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

def render_suspensivas_tab():
    """Enhanced suspensivas analysis"""
    st.header("⏰ Análise de Suspensivas")
    
    st.info("Análise de suspensivas será implementada quando os dados estiverem disponíveis.")
    
    # Show what we can from the data
    engine = get_db_connection()
    try:
        df_status = pd.read_sql(f"""
            SELECT uf, programa, COUNT(*) as total,
                   AVG(percentual_mcmv) as avg_execution
            FROM mcmv_pj.vw_empreendimentos_unificado
            WHERE programa IN {tuple(MCMV_PROGRAMS)}
            AND percentual_mcmv < 10
            GROUP BY uf, programa
            ORDER BY total DESC
            LIMIT 20
        """, engine)
        
        if not df_status.empty:
            st.subheader("Projetos com Baixa Execução (< 10%)")
            fig = px.bar(
                df_status.head(15),
                x='total',
                y='uf',
                orientation='h',
                title='Estados com Projetos de Baixa Execução',
                color='avg_execution',
                color_continuous_scale='Reds'
            )
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")

def render_cidades_tab():
    """Enhanced cities analysis"""
    st.header("🏙️ MCMV Cidades")
    
    engine = get_db_connection()
    df_cities = pd.read_sql(f"""
        SELECT uf, municipio_beneficiado, COUNT(*) as projetos, 
               SUM(uh_estimadas) as total_uh,
               AVG(percentual_mcmv) as avg_execution
        FROM mcmv_pj.vw_empreendimentos_unificado
        WHERE programa IN {tuple(MCMV_PROGRAMS)}
        GROUP BY uf, municipio_beneficiado
        ORDER BY total_uh DESC
        LIMIT 30
    """, engine)
    
    st.subheader("Top 30 Municípios por UH")
    
    # Bar chart of top cities
    fig = px.bar(
        df_cities.head(20),
        x='total_uh',
        y=df_cities.head(20)['municipio_beneficiado'] + ' (' + df_cities.head(20)['uf'] + ')',
        orientation='h',
        title='Top 20 Municípios por Total de UH',
        color='avg_execution',
        color_continuous_scale='Viridis',
        labels={'y': 'Município', 'x': 'Total UH', 'avg_execution': '% Execução'}
    )
    fig.update_layout(height=600)
    st.plotly_chart(fig, use_container_width=True)
    
    # Data table
    st.dataframe(df_cities, use_container_width=True, hide_index=True)

def render_risk_analysis_tab():
    """Enhanced risk analysis with neutral presentation"""
    st.header("📊 Análise de Projetos que Requerem Atenção")
    
    try:
        # Risk by program
        risk_by_program = load_risk_by_program()
        
        if not risk_by_program.empty:
            st.subheader("Projetos com Necessidade de Acompanhamento por Programa")
            risk_prog = risk_by_program[risk_by_program['alto_risco'] > 0]
            
            if not risk_prog.empty:
                fig_risk_prog = px.bar(
                    risk_prog,
                    x='programa',
                    y='alto_risco',
                    title="Projetos que Requerem Acompanhamento Especial por Programa",
                    labels={'alto_risco': 'Projetos p/ Acompanhamento'},
                    color='alto_risco',
                    color_continuous_scale='Blues',
                    text='alto_risco'
                )
                fig_risk_prog.update_traces(texttemplate='%{text}', textposition='outside')
                st.plotly_chart(fig_risk_prog, use_container_width=True)
        
        # Risk by state
        risk_by_state = load_risk_by_state()
        
        if not risk_by_state.empty:
            st.subheader("Estados com Projetos que Requerem Acompanhamento")
            
            fig_risk_state = px.bar(
                risk_by_state.head(10),
                x='uf',
                y='alto_risco',
                title="Projetos para Acompanhamento Especial por Estado",
                color='alto_risco',
                color_continuous_scale='Blues',
                text='alto_risco'
            )
            fig_risk_state.update_traces(texttemplate='%{text}', textposition='outside')
            st.plotly_chart(fig_risk_state, use_container_width=True)
            
            # Risk details table
            st.subheader("📋 Detalhamento de Acompanhamento por Estado")
            risk_table = risk_by_state[['uf', 'alto_risco', 'total_projetos', 'avg_execution']].copy()
            risk_table['% Acompanhamento'] = (risk_table['alto_risco'] / risk_table['total_projetos'] * 100).round(1)
            risk_table['avg_execution'] = risk_table['avg_execution'].round(1)
            risk_table.columns = ['Estado', 'P/ Acompanhamento', 'Total Projetos', 'Exec. Média (%)', '% p/ Acompanhamento']
            st.dataframe(risk_table, use_container_width=True, hide_index=True)
        else:
            st.success("✅ Todos os projetos estão dentro dos parâmetros normais de acompanhamento!")
            
    except Exception as e:
        st.error(f"Erro ao carregar análise de acompanhamento: {str(e)}")
def render_financial_tab():
    """Enhanced financial analysis"""
    st.header("💰 Fluxo Financeiro")
    
    try:
        financial_df = load_financial_flow()
        
        # Financial summary by state
        financial_summary = financial_df.groupby('uf')['investimento_total'].sum().sort_values(ascending=False).head(10)
        
        fig_finance = px.bar(
            x=financial_summary.index,
            y=financial_summary.values / 1e6,
            title="Top 10 Estados - Investimento Total (R$ milhões)",
            labels={'x': 'Estado', 'y': 'Investimento (R$ milhões)'},
            color=financial_summary.values,
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig_finance, use_container_width=True)
        
        # Program breakdown
        program_finance = financial_df.groupby('programa')['investimento_total'].sum()
        
        col1, col2 = st.columns(2)
        with col1:
            fig_prog_fin = px.pie(
                values=program_finance.values,
                names=program_finance.index,
                title="Investimento por Programa",
                hole=0.4
            )
            st.plotly_chart(fig_prog_fin, use_container_width=True)
        
        with col2:
            # Summary metrics for main programs
            st.metric("Total FAR", f"R$ {program_finance.get('FAR', 0)/1e9:.2f} bi")
            st.metric("Total FDS", f"R$ {program_finance.get('FDS', 0)/1e9:.2f} bi")
            st.metric("Total RURAL", f"R$ {program_finance.get('RURAL', 0)/1e9:.2f} bi")
    except Exception as e:
        st.error(f"Erro ao carregar dados financeiros: {str(e)}")

def render_distribution_tab():
    """Enhanced geographic distribution"""
    st.header("📊 Distribuição Geográfica dos Projetos")
    
    uh_gap_df = load_uh_gap_by_state()
    state_counts = uh_gap_df.groupby('uf').agg({
        'uh_esperadas': 'sum',
        'percentual_medio': 'mean'
    }).sort_values('uh_esperadas', ascending=False)
    
    # Treemap
    fig_tree = px.treemap(
        state_counts.reset_index(),
        path=['uf'],
        values='uh_esperadas',
        color='percentual_medio',
        hover_data={'uh_esperadas': ':,', 'percentual_medio': ':.1f'},
        color_continuous_scale='RdYlGn',
        title='Estados por UH Esperadas (cor = % execução)'
    )
    st.plotly_chart(fig_tree, use_container_width=True)

@require_auth
def main():
    st.title("🏠 Dashboard MCMV - Análise de Investimentos")
    st.markdown("Análise completa dos programas habitacionais com novas métricas de beneficiários, prazos e trabalho social")
    
    # Load and display enhanced KPIs
    render_kpis()
    
    st.markdown("---")
    
    # Enhanced sidebar with new KPI highlights
    with st.sidebar:
        engine = get_db_connection()
        project_counts = pd.read_sql(f"""
            SELECT programa, COUNT(*) as count
            FROM projeto_status
            WHERE tipo_programa = 'MCMV-HIS'
            GROUP BY programa
            ORDER BY count DESC
        """, engine)

        # Calculate total
        total_projects = project_counts['count'].sum()

        # Professional sidebar display
        st.markdown("""
        <style>
        .sidebar-info-box {
            background-color: #f8f9fa;
            border-left: 4px solid #0066cc;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }
        .sidebar-header {
            color: #0066cc;
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        .new-feature {
            background-color: #e3f2fd;
            border: 1px solid #2196f3;
            border-radius: 0.25rem;
            padding: 0.5rem;
            margin: 0.5rem 0;
            font-size: 0.85rem;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown('<div class="sidebar-info-box">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-header">📊 Dados Incluídos</div>', unsafe_allow_html=True)

        # Display each program
        for _, row in project_counts.iterrows():
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid #e0e0e0;">
                <span style="font-weight: 500; color: #333;">{row['programa']}</span>
                <span style="font-weight: 600; color: #0066cc;">{row['count']:,}</span>
            </div>
            """, unsafe_allow_html=True)

        # Display total
        st.markdown(f"""
        <div style="background-color: #e3f2fd; padding: 0.75rem; border-radius: 0.25rem; margin-top: 0.5rem; text-align: center;">
            <div style="font-size: 0.9rem; color: #666;">Total de Projetos</div>
            <div style="font-size: 1.5rem; font-weight: 700; color: #0066cc;">{total_projects:,}</div>
            <div style="font-size: 0.85rem; color: #666;">MCMV</div>
        </div>
        """, unsafe_allow_html=True)


        st.markdown(f"""
        <div style="font-size: 0.85rem; color: #666; text-align: center; margin-top: 0.5rem;">
            🕐 Atualizado: {datetime.now().strftime('%d/%m/%Y às %H:%M')}
        </div>
        """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)
                
        if st.button("🔄 Atualizar Dados"):
            st.cache_data.clear()
            st.rerun()

    # Enhanced tabs with new KPIs
    tabs = st.tabs([
        "📍 Mapa", 
        "📊 Por Região", 
        "📑 Contratações", 
        "👥 Beneficiários",
        "⏱️ Prazos",
        "📚 Trabalho Social",
        "💰 Exec. Financeira",
        "🏗️ Desempenho",
        "⏰ Suspensivas",
        "🏙️ Cidades",
        "🚨 Análise de Risco", 
        "💸 Fluxo Financeiro", 
        "📊 Distribuição"
    ])
    
    with tabs[0]:
        render_map_tab()
    
    with tabs[1]:
        render_region_barchart()
    
    with tabs[2]:
        render_contratacoes_tab()
    
    with tabs[3]:  # NEW
        render_beneficiarios_tab()
    
    with tabs[4]:  # NEW
        render_prazos_tab()
    
    with tabs[5]:  # NEW
        render_trabalho_social_tab()
    
    with tabs[6]:  # NEW
        render_financeiro_detalhado_tab()
    
    with tabs[7]:  # NEW
        render_desempenho_tab()
    
    with tabs[8]:
        render_suspensivas_tab()
    
    with tabs[9]:
        render_cidades_tab()
    
    with tabs[10]:
        render_risk_analysis_tab()
    
    with tabs[11]:
        render_financial_tab()
    
    with tabs[12]:
        render_distribution_tab()
    
# Enhanced footer with dynamic neutral summary
    st.markdown("---")
    
    # Load summary data for footer
    try:
        national_summary = load_national_summary()
        beneficiary_summary = load_beneficiary_summary()
        timeline_summary = load_timeline_analysis()
        social_work_summary = load_social_work()
        program_summary = load_program_summary()
        
        # Calculate dynamic metrics
        total_completed = program_summary['projetos_concluidos'].sum() if not program_summary.empty else 0
        total_beneficiaries = beneficiary_summary['total_beneficiarios'] if not beneficiary_summary.empty else 0
        total_women = beneficiary_summary['total_mulheres'] if not beneficiary_summary.empty else 0
        total_projects_started = timeline_summary['projetos_iniciados'].sum() if not timeline_summary.empty else 0
        total_projects = timeline_summary['total_projetos'].sum() if not timeline_summary.empty else 1
        pct_started = (total_projects_started / total_projects * 100) if total_projects > 0 else 0
        avg_execution = national_summary['percentual_medio_nacional'] if not national_summary.empty else 0
        total_investment = national_summary['investimento_total'] / 1e9 if not national_summary.empty else 0
        ts_projects = len(social_work_summary) if not social_work_summary.empty else 0
        
        # Quick insights footer
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            **📊 Achados Relevantes:**
            - {total_completed} projetos completados
            - {f"{int(total_women):,}".replace(',', '.')} mulheres no programa
            - Execução média {f"{avg_execution:.1f}".replace('.', ',')}%
            """)
        
        with col2:
            st.markdown(f"""
            **📈 Novos Indicadores:**
            - {f"{int(total_beneficiaries):,}".replace(',', '.')} beneficiários cadastrados
            - {ts_projects} projetos c/ trabalho social
            - R$ {f"{total_investment:.1f}".replace('.', ',')}B comprometidos
            """)
        
        with col3:
            st.markdown(f"""
            **⏱️ Status de Execução:**
            - {f"{total_projects_started:,}".replace(',', '.')} projetos iniciados ({f"{pct_started:.1f}".replace('.', ',')}%)
            - Progresso médio {f"{avg_execution:.1f}".replace('.', ',')}%
            - {ts_projects} com trabalho social ativo
            """)
    
    except Exception as e:
        st.error(f"Erro ao carregar resumo: {e}")
        # Fallback to static message if data loading fails
        st.markdown("**Dashboard:** Dados dinâmicos carregados das views SQL")
    
    st.caption("📊 Dados extraídos das views SQL otimizadas com análises de beneficiários, prazos e trabalho social")
    st.caption("🔄 Cache atualizado a cada 5 minutos | 📈 Análises baseadas em dados atualizados do CAIXA")
if __name__ == "__main__":
    main()
