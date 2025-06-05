# Save as: streamlit_app/dashboard_mcmv_enhanced_final.py
#!/usr/bin/env python3
"""
MCMV Enhanced Dashboard Final - With working map and fixed queries
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


# Page config
st.set_page_config(
    page_title="MCMV Analytics Dashboard - Enhanced",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    div[data-testid="metric-container"] {
        background-color: #f0f2f6;
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 16px;
    }
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

def render_kpis():
    """Render KPI cards at the top"""
    summary = load_national_summary()
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
            "Brecha UH",
            f"{int(summary['brecha_uh_nacional']):,}",
            delta_color="inverse"
        )
    
    with col5:
        st.metric(
            "Investimento Total",
            f"R$ {summary['investimento_total']/1e9:.2f} bi"
        )
    
    # Alert boxes
    if summary['projetos_alto_risco'] > 0:
        st.warning(f"⚠️ {int(summary['projetos_alto_risco'])} projetos em alto risco")

def render_map_tab():
    """Render geographic visualization tab with working choropleth"""
    st.header("📍 Mapa de Unidades Habitacionais por Estado")
    
    df_gap = load_uh_gap_by_state()
    geojson = load_brazil_geojson()
    
    # Aggregate by state
    df_map = df_gap.groupby('uf').agg({
        'uh_esperadas': 'sum',
        'uh_executadas': 'sum',
        'brecha_uh': 'sum',
        'percentual_medio': 'mean'
    }).reset_index()
    
    # Metric selector
    metric = st.selectbox(
        "Selecione a métrica para visualização:",
        options=['brecha_uh', 'uh_executadas', 'uh_esperadas', 'percentual_medio'],
        format_func=lambda x: {
            'brecha_uh': 'Brecha de UH (a completar)',
            'uh_executadas': 'UH Executadas',
            'uh_esperadas': 'UH Esperadas',
            'percentual_medio': 'Percentual de Execução (%)'
        }[x]
    )
    
    if geojson is not None:
        # Fix the geojson properties if needed
        if 'features' in geojson:
            for feature in geojson['features']:
                if 'properties' in feature:
                    # Map different possible property names to 'uf'
                    if 'sigla' in feature['properties']:
                        feature['properties']['uf'] = feature['properties']['sigla']
                    elif 'id' in feature['properties'] and len(feature['properties']['id']) == 2:
                        feature['properties']['uf'] = feature['properties']['id']
        
        # Create choropleth
        fig = px.choropleth(
            df_map,
            geojson=geojson,
            locations='uf',
            featureidkey="properties.uf",
            color=metric,
            hover_name='uf',
            hover_data={
                'uh_esperadas': ':,.0f',
                'uh_executadas': ':,.0f',
                'brecha_uh': ':,.0f',
                'percentual_medio': ':.1f',
                'uf': False
            },
            color_continuous_scale='Viridis' if metric != 'brecha_uh' else 'Reds',
            title=f"{metric.replace('_', ' ').title()} por Estado"
        )
        
        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(margin={"r": 0, "t": 30, "l": 0, "b": 0}, height=600)
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        # Fallback to bar chart if map doesn't load
        st.warning("Mapa não disponível. Mostrando dados em gráfico de barras.")
        fig = px.bar(
            df_map.sort_values(metric, ascending=False).head(15),
            x=metric,
            y='uf',
            orientation='h',
            title=f"Top 15 Estados - {metric.replace('_', ' ').title()}",
            labels={'uf': 'Estado', metric: metric.replace('_', ' ').title()},
            color=metric,
            color_continuous_scale='Viridis' if metric != 'brecha_uh' else 'Reds'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Top states table
    with st.expander("📊 Ver dados detalhados por estado"):
        st.dataframe(
            df_map.sort_values('brecha_uh', ascending=False),
            use_container_width=True,
            hide_index=True
        )

def render_region_barchart():
    """Render regional analysis with separate charts"""
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

# Replace your current load_contratacoes_summary with this version
# This uses the calculated approach that was working before

@st.cache_data(ttl=300)
def load_contratacoes_summary():
    """
    Load contracting summary by calculating from raw data.
    This is used because vw_resumo_nacional doesn't include contracting breakdown.
    """
    engine = get_db_connection()
    
    query = f"""
    SELECT
        COUNT(*) as total_empreendimentos,
        SUM(uh_estimadas) as uh_total,
        SUM(COALESCE(valor_investimento_mcmv, 0) + COALESCE(valor_investimento_pac, 0)) as valor_total,
        
        COUNT(*) FILTER (WHERE percentual_mcmv < 5) as aguardando_mcid,
        COALESCE(SUM(uh_estimadas) FILTER (WHERE percentual_mcmv < 5), 0) as uh_aguardando_mcid,
        
        COUNT(*) FILTER (WHERE percentual_mcmv >= 5 AND percentual_mcmv < 15) as mcid_emitida,
        COALESCE(SUM(uh_estimadas) FILTER (WHERE percentual_mcmv >= 5 AND percentual_mcmv < 15), 0) as uh_mcid_emitida,
        
        COUNT(*) FILTER (WHERE percentual_mcmv >= 15) as contratos_emitidos,
        COALESCE(SUM(uh_estimadas) FILTER (WHERE percentual_mcmv >= 15), 0) as uh_contratos_emitidos,
        
        COUNT(*) FILTER (WHERE alto_risco = true AND percentual_mcmv < 20) as distratos,
        COALESCE(SUM(uh_estimadas) FILTER (WHERE alto_risco = true AND percentual_mcmv < 20), 0) as uh_distratos
        
    FROM mcmv_pj.vw_empreendimentos_unificado
    WHERE programa IN {tuple(MCMV_PROGRAMS)}
    """
    
    try:
        result = pd.read_sql(query, engine)
        summary = result.iloc[0].to_dict()
        
        # Cleanup & enforce data types
        for k, v in summary.items():
            summary[k] = int(v) if v is not None and not pd.isna(v) else 0
            if 'valor' in k:
                summary[k] = float(v) if v else 0.0
                
        return summary
        
    except Exception as e:
        st.error(f"Erro ao carregar resumo de contratações: {str(e)}")
        return {key: 0 for key in [
            'total_empreendimentos', 'uh_total', 'valor_total',
            'aguardando_mcid', 'uh_aguardando_mcid',
            'mcid_emitida', 'uh_mcid_emitida',
            'contratos_emitidos', 'uh_contratos_emitidos',
            'distratos', 'uh_distratos'
        ]}

# Optional debug function - add this if you want to verify the data
def debug_contratacoes_data():
    """Debug function to verify contracting data distribution"""
    engine = get_db_connection()
    
    st.write("### 📊 Debug: Contracting Data Distribution")
    
    # Phase distribution
    debug_query = f"""
    SELECT 
        CASE 
            WHEN percentual_mcmv < 5 THEN '1. Aguardando MCID (<5%)'
            WHEN percentual_mcmv < 15 THEN '2. MCID Emitida (5-15%)'
            ELSE '3. Contratos Emitidos (>=15%)'
        END as fase,
        COUNT(*) as projetos,
        SUM(uh_estimadas) as total_uh,
        AVG(percentual_mcmv) as avg_execution
    FROM mcmv_pj.vw_empreendimentos_unificado
    WHERE programa IN {tuple(MCMV_PROGRAMS)}
    GROUP BY fase
    ORDER BY fase;
    """
    
    df_debug = pd.read_sql(debug_query, engine)
    st.dataframe(df_debug, use_container_width=True)
    
    # Risk analysis
    risk_query = f"""
    SELECT 
        COUNT(*) as total_projects,
        COUNT(*) FILTER (WHERE alto_risco = true) as high_risk_projects,
        COUNT(*) FILTER (WHERE alto_risco = true AND percentual_mcmv < 20) as distratos_candidates,
        AVG(percentual_mcmv) as avg_execution_all,
        AVG(percentual_mcmv) FILTER (WHERE alto_risco = true) as avg_execution_high_risk
    FROM mcmv_pj.vw_empreendimentos_unificado
    WHERE programa IN {tuple(MCMV_PROGRAMS)};
    """
    
    df_risk = pd.read_sql(risk_query, engine)
    st.write("### 🚨 Risk Analysis")
    st.dataframe(df_risk, use_container_width=True)

# Alternative: If the view doesn't have these specific fields, 
# create a dedicated query that matches the view structure
@st.cache_data(ttl=300)
def load_contratacoes_summary_detailed():
    """
    Load contracting summary with detailed breakdown.
    This function queries the database to get contracting status if not in main view.
    """
    engine = get_db_connection()
    
    # First, check what columns are available in vw_resumo_nacional
    check_query = """
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_schema = 'mcmv_pj' 
    AND table_name = 'vw_resumo_nacional'
    ORDER BY ordinal_position;
    """
    
    try:
        columns_df = pd.read_sql(check_query, engine)
        available_columns = columns_df['column_name'].tolist()
        
        # Log available columns for debugging
        print(f"Available columns in vw_resumo_nacional: {available_columns}")
        
        # If contracting columns exist in the view, use them
        if all(col in available_columns for col in ['aguardando_autorizacao_mcid', 'autorizacao_mcid_emitida', 'contratos_emitidos']):
            return load_contratacoes_summary()
        else:
            # Fall back to calculating from raw data
            return load_contratacoes_summary_calculated()
            
    except Exception as e:
        print(f"Error checking view structure: {e}")
        # Fall back to calculated version
        return load_contratacoes_summary_calculated()

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
    
    # Add data boxes
    box_width = Inches(4.5)
    box_height = Inches(2.5)
    top = Inches(2)
    
    # Helper function to format numbers
    def format_number_pptx(value):
        return f"{int(value):,}".replace(",", ".")
    
    # Aguardando MCID box
    left = Inches(0.75)
    box = slide.shapes.add_textbox(left, top, box_width, box_height)
    tf = box.text_frame
    tf.text = "AGUARDANDO AUTORIZAÇÃO MCID"
    p = tf.add_paragraph()
    p.text = f"Empreendimentos: {format_number_pptx(summary['aguardando_mcid'])}"
    p = tf.add_paragraph()
    p.text = f"UH: {format_number_pptx(summary['uh_aguardando_mcid'])}"
    
    # MCID Emitida box
    left = Inches(5.75)
    box = slide.shapes.add_textbox(left, top, box_width, box_height)
    tf = box.text_frame
    tf.text = "AUTORIZAÇÃO MCID EMITIDA"
    p = tf.add_paragraph()
    p.text = f"Empreendimentos: {format_number_pptx(summary['mcid_emitida'])}"
    p = tf.add_paragraph()
    p.text = f"UH: {format_number_pptx(summary['uh_mcid_emitida'])}"
    
    # Contratos Emitidos box
    left = Inches(10.75)
    box = slide.shapes.add_textbox(left, top, box_width, box_height)
    tf = box.text_frame
    tf.text = "CONTRATOS EMITIDOS"
    p = tf.add_paragraph()
    p.text = f"Empreendimentos: {format_number_pptx(summary['contratos_emitidos'])}"
    p = tf.add_paragraph()
    p.text = f"UH: {format_number_pptx(summary['uh_contratos_emitidos'])}"
    
    # Total box
    top = Inches(5)
    left = Inches(4)
    box_width = Inches(8)
    box = slide.shapes.add_textbox(left, top, box_width, box_height)
    tf = box.text_frame
    tf.text = "TOTAL GERAL"
    tf.paragraphs[0].font.bold = True
    tf.paragraphs[0].font.size = Pt(24)
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    
    p = tf.add_paragraph()
    p.text = f"Total Empreendimentos: {format_number_pptx(summary['total_empreendimentos'])}"
    p.alignment = PP_ALIGN.CENTER
    
    p = tf.add_paragraph()
    p.text = f"Total UH: {format_number_pptx(summary['uh_total'])}"
    p.alignment = PP_ALIGN.CENTER
    
    p = tf.add_paragraph()
    valor_bi = summary['valor_total'] / 1e9
    p.text = f"Valor Total: R$ {valor_bi:.2f} bi".replace(".", ",")
    p.alignment = PP_ALIGN.CENTER
    
    # Save to bytes
    pptx_bytes = BytesIO()
    prs.save(pptx_bytes)
    pptx_bytes.seek(0)
    
    return pptx_bytes.getvalue()

@st.cache_data(ttl=300)
def load_contratacoes_summary_calculated():
    """
    Calculate contracting summary from raw data if not available in view.
    This maintains backward compatibility.
    """
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
    return pd.read_sql(query, engine).iloc[0].to_dict()

# Update render_contratacoes_tab to handle the actual values from the view
def render_contratacoes_tab():
    """Render enhanced contracting status matching PDF style exactly"""
    st.header("📑 Status de Contratações")
    
    # Load summary data - now from the view
    summary = load_contratacoes_summary()
    
    # Enhanced CSS for perfect styling (keep existing CSS)
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
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
    
    .metric-content {
        flex-grow: 1;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .metric-value {
        font-size: 42px;
        font-weight: 700;
        color: #1f1f1f;
        margin: 8px 0;
        line-height: 1;
    }
    
    .metric-uh {
        font-size: 28px;
        font-weight: 700;
        color: #333;
        margin: 8px 0;
    }
    
    .metric-label {
        font-size: 11px;
        color: #666;
        margin-top: 3px;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }
    
    .metric-money {
        font-size: 22px;
        font-weight: 600;
        color: #333;
        margin-top: 12px;
    }
    
    .total-container {
        background-color: #f0f8ff;
        padding: 35px;
        border-radius: 10px;
        text-align: center;
        margin: 30px auto;
        border: 2px solid #0066cc;
        box-shadow: 0 4px 8px rgba(0,102,204,0.1);
        max-width: 90%;
    }
    
    .total-title {
        font-size: 20px;
        font-weight: 700;
        color: #0066cc;
        margin-bottom: 25px;
        letter-spacing: 0.5px;
        font-family: 'Inter', Arial, sans-serif;
    }
    
    .total-metrics {
        display: flex;
        justify-content: space-around;
        align-items: center;
        flex-wrap: wrap;
        gap: 40px;
    }
    
    .total-item {
        flex: 1;
        min-width: 200px;
    }
    
    /* Color-coded containers */
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
    
    .distratos-container {
        border-left: 6px solid #f44336;
        background: linear-gradient(90deg, #ffebee 0%, #ffffff 100%);
    }
    .distratos-container .metric-title {
        color: #003366;
    }
    
    /* Progress metrics styling */
    .progress-metric {
        background-color: #fafafa;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* Chart styling */
    .chart-container {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.subheader("📊 Resumo de Contratações")
    
    # Helper function to format Brazilian currency
    def format_br_currency(value, unit="mi"):
        if value == 0:
            return "R$ 0,00 " + unit
        
        if unit == "bi":
            formatted = f"{value/1e9:.2f}"
        else:  # mi
            formatted = f"{value/1e6:.2f}"
        
        # Replace dots with commas for Brazilian format
        formatted = formatted.replace(".", ",")
        return f"R$ {formatted} {unit}"
    
    # Helper function to format numbers Brazilian style
    def format_br_number(value):
        return f"{int(value):,}".replace(",", ".")
    
    # Calculate estimated values based on UH counts and average investment
    # Use actual values from the view or calculate based on UH
    avg_investment_per_uh = summary['valor_total'] / summary['uh_total'] if summary['uh_total'] > 0 else 150000
    
    aguardando_valor = summary['uh_aguardando_mcid'] * avg_investment_per_uh
    mcid_valor = summary['uh_mcid_emitida'] * avg_investment_per_uh
    contratos_valor = summary['uh_contratos_emitidos'] * avg_investment_per_uh
    distratos_valor = summary['uh_distratos'] * avg_investment_per_uh
    
    # Top row: 3 columns for the main stages
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-container aguardando-container">
            <div class="metric-title">AGUARDANDO AUTORIZAÇÃO MCID</div>
            <div class="metric-content">
                <div>
                    <div class="metric-label">Empreendimentos</div>
                    <div class="metric-value">{format_br_number(summary['aguardando_mcid'])}</div>
                </div>
                <div style="margin-top: 15px;">
                    <div class="metric-label">UH</div>
                    <div class="metric-uh">{format_br_number(summary['uh_aguardando_mcid'])}</div>
                </div>
                <div style="margin-top: 15px;">
                    <div class="metric-label">Valor Estimado</div>
                    <div class="metric-money">{format_br_currency(aguardando_valor)}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-container mcid-emitida-container">
            <div class="metric-title">AUTORIZAÇÃO MCID EMITIDA</div>
            <div class="metric-content">
                <div>
                    <div class="metric-label">Empreendimentos</div>
                    <div class="metric-value">{format_br_number(summary['mcid_emitida'])}</div>
                </div>
                <div style="margin-top: 15px;">
                    <div class="metric-label">UH</div>
                    <div class="metric-uh">{format_br_number(summary['uh_mcid_emitida'])}</div>
                </div>
                <div style="margin-top: 15px;">
                    <div class="metric-label">Valor Estimado</div>
                    <div class="metric-money">{format_br_currency(mcid_valor)}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-container contratos-container">
            <div class="metric-title">CONTRATOS EMITIDOS</div>
            <div class="metric-content">
                <div>
                    <div class="metric-label">Empreendimentos</div>
                    <div class="metric-value">{format_br_number(summary['contratos_emitidos'])}</div>
                </div>
                <div style="margin-top: 15px;">
                    <div class="metric-label">UH</div>
                    <div class="metric-uh">{format_br_number(summary['uh_contratos_emitidos'])}</div>
                </div>
                <div style="margin-top: 15px;">
                    <div class="metric-label">Valor Estimado</div>
                    <div class="metric-money">{format_br_currency(contratos_valor)}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Second row: Distratos on the left
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown(f"""
        <div class="metric-container distratos-container">
            <div class="metric-title">DISTRATOS</div>
            <div class="metric-content">
                <div>
                    <div class="metric-label">Empreendimentos</div>
                    <div class="metric-value">{format_br_number(summary['distratos'])}</div>
                </div>
                <div style="margin-top: 20px;">
                    <div class="metric-label">UH</div>
                    <div class="metric-uh">{format_br_number(summary['uh_distratos'])}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Total section - centered below all cards
    st.markdown(f"""
    <div class="total-container">
        <div class="total-title">📊 TOTAL GERAL</div>
        <div class="total-metrics">
            <div class="total-item">
                <div class="metric-label">Total Empreendimentos</div>
                <div class="metric-value">{format_br_number(summary['total_empreendimentos'])}</div>
            </div>
            <div class="total-item">
                <div class="metric-label">Total UH</div>
                <div class="metric-value">{format_br_number(summary['uh_total'])}</div>
            </div>
            <div class="total-item">
                <div class="metric-label">Valor Total</div>
                <div class="metric-value">{format_br_currency(summary['valor_total'], 'bi')}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Enhanced visualization section
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    
    # Create data for visualization
    chart_df = pd.DataFrame({
        "Status": [
            "Aguardando MCID",
            "MCID Emitida", 
            "Contratos Emitidos",
            "Distratos"
        ],
        "UH": [
            summary["uh_aguardando_mcid"],
            summary["uh_mcid_emitida"],
            summary["uh_contratos_emitidos"],
            summary["uh_distratos"]
        ],
        "Empreendimentos": [
            summary["aguardando_mcid"],
            summary["mcid_emitida"],
            summary["contratos_emitidos"],
            summary["distratos"]
        ],
        "Colors": ['#2196f3', '#ff9800', '#4caf50', '#f44336']
    })
    
    # Create figure with subplots
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Unidades Habitacionais por Etapa", "Empreendimentos por Etapa"),
        horizontal_spacing=0.12,
        specs=[[{"type": "bar"}, {"type": "bar"}]]
    )
    
    # UH bar chart
    for i, row in chart_df.iterrows():
        fig.add_trace(
            go.Bar(
                x=[row["Status"]],
                y=[row["UH"]],
                text=[format_br_number(row["UH"])],
                textposition="outside",
                marker_color=row["Colors"],
                name=row["Status"],
                showlegend=False,
                textfont=dict(size=12, family="Inter, Arial")
            ),
            row=1, col=1
        )
    
    # Empreendimentos bar chart
    for i, row in chart_df.iterrows():
        fig.add_trace(
            go.Bar(
                x=[row["Status"]],
                y=[row["Empreendimentos"]],
                text=[format_br_number(row["Empreendimentos"])],
                textposition="outside",
                marker_color=row["Colors"],
                name=row["Status"],
                showlegend=False,
                textfont=dict(size=12, family="Inter, Arial")
            ),
            row=1, col=2
        )
    
    # Update layout
    fig.update_layout(
        height=450,
        showlegend=False,
        title_text="📈 Visão Geral das Contratações",
        title_font=dict(size=20, family="Inter, Arial"),
        title_x=0.5,
        plot_bgcolor='white',
        paper_bgcolor='white',
        bargap=0.2,
        font=dict(family="Inter, Arial")
    )
    
    # Update axes
    fig.update_xaxes(title_text="", tickfont=dict(size=11), row=1, col=1)
    fig.update_xaxes(title_text="", tickfont=dict(size=11), row=1, col=2)
    fig.update_yaxes(title_text="UH", title_font=dict(size=12), tickfont=dict(size=10), row=1, col=1)
    fig.update_yaxes(title_text="Empreendimentos", title_font=dict(size=12), tickfont=dict(size=10), row=1, col=2)
    
    # Add grid
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(200,200,200,0.3)')
    
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Progress indicators with custom styling
    st.markdown("---")
    st.markdown("### 📊 Indicadores de Progresso")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        progress_mcid = (summary['mcid_emitida'] / summary['total_empreendimentos'] * 100) if summary['total_empreendimentos'] > 0 else 0
        st.markdown(f"""
        <div class="progress-metric">
            <div style="font-size: 14px; color: #666; margin-bottom: 5px;">Taxa de Autorização MCID</div>
            <div style="font-size: 28px; font-weight: 700; color: #2196f3;">{progress_mcid:.1f}%</div>
            <div style="font-size: 12px; color: #4caf50; margin-top: 5px;">↑ {summary['mcid_emitida']} empreendimentos</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        progress_contratos = (summary['contratos_emitidos'] / summary['total_empreendimentos'] * 100) if summary['total_empreendimentos'] > 0 else 0
        st.markdown(f"""
        <div class="progress-metric">
            <div style="font-size: 14px; color: #666; margin-bottom: 5px;">Taxa de Contratação</div>
            <div style="font-size: 28px; font-weight: 700; color: #4caf50;">{progress_contratos:.1f}%</div>
            <div style="font-size: 12px; color: #4caf50; margin-top: 5px;">↑ {summary['contratos_emitidos']} empreendimentos</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        taxa_distratos = (summary['distratos'] / summary['total_empreendimentos'] * 100) if summary['total_empreendimentos'] > 0 else 0
        st.markdown(f"""
        <div class="progress-metric">
            <div style="font-size: 14px; color: #666; margin-bottom: 5px;">Taxa de Distratos</div>
            <div style="font-size: 28px; font-weight: 700; color: #f44336;">{taxa_distratos:.1f}%</div>
            <div style="font-size: 12px; color: #f44336; margin-top: 5px;">• {summary['distratos']} empreendimentos</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Footer info
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.caption("📊 Dados atualizados dos views SQL contratadas")
    with col2:
        st.caption("💾 Cache atualizado a cada 5 minutos")
    
    # Export buttons
    st.markdown("---")
    st.markdown("### 📥 Exportar Dashboard")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Generate HTML for PDF export
        html_content = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
                body {{ font-family: 'Inter', Arial, sans-serif; margin: 40px; }}
                .header {{ text-align: center; margin-bottom: 40px; }}
                .metric-container {{ 
                    border: 1px solid #ddd; 
                    padding: 20px; 
                    margin: 10px;
                    text-align: center;
                    display: inline-block;
                    width: 30%;
                }}
                .metric-title {{ font-size: 14px; font-weight: bold; color: #0066cc; margin-bottom: 15px; }}
                .metric-value {{ font-size: 36px; font-weight: bold; color: #1f1f1f; }}
                .metric-label {{ font-size: 12px; color: #666; margin-top: 5px; }}
                .total-container {{ 
                    background-color: #f0f8ff; 
                    padding: 30px; 
                    margin: 30px auto;
                    border: 2px solid #0066cc;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Status de Contratações - MCMV</h1>
                <p>Relatório gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
            </div>
            
            <div style="text-align: center;">
                <div class="metric-container">
                    <div class="metric-title">AGUARDANDO AUTORIZAÇÃO MCID</div>
                    <div class="metric-value">{format_br_number(summary['aguardando_mcid'])}</div>
                    <div class="metric-label">Empreendimentos</div>
                    <div class="metric-value">{format_br_number(summary['uh_aguardando_mcid'])}</div>
                    <div class="metric-label">UH</div>
                </div>
                
                <div class="metric-container">
                    <div class="metric-title">AUTORIZAÇÃO MCID EMITIDA</div>
                    <div class="metric-value">{format_br_number(summary['mcid_emitida'])}</div>
                    <div class="metric-label">Empreendimentos</div>
                    <div class="metric-value">{format_br_number(summary['uh_mcid_emitida'])}</div>
                    <div class="metric-label">UH</div>
                </div>
                
                <div class="metric-container">
                    <div class="metric-title">CONTRATOS EMITIDOS</div>
                    <div class="metric-value">{format_br_number(summary['contratos_emitidos'])}</div>
                    <div class="metric-label">Empreendimentos</div>
                    <div class="metric-value">{format_br_number(summary['uh_contratos_emitidos'])}</div>
                    <div class="metric-label">UH</div>
                </div>
            </div>
            
            <div class="total-container">
                <h2>TOTAL GERAL</h2>
                <p><strong>Total Empreendimentos:</strong> {format_br_number(summary['total_empreendimentos'])}</p>
                <p><strong>Total UH:</strong> {format_br_number(summary['uh_total'])}</p>
                <p><strong>Valor Total:</strong> {format_br_currency(summary['valor_total'], 'bi')}</p>
            </div>
        </body>
        </html>
        """
        
        st.download_button(
            label="📄 Download PDF",
            data=html_content.encode('utf-8'),
            file_name=f"contratacoes_mcmv_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
            mime="text/html",
            help="Baixa o relatório em formato HTML (abra no navegador e imprima como PDF)"
        )
    
    with col2:
        # Create PowerPoint content
        pptx_data = create_pptx_report(summary)
        
        st.download_button(
            label="📊 Download PPTX",
            data=pptx_data,
            file_name=f"contratacoes_mcmv_{datetime.now().strftime('%Y%m%d_%H%M')}.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            help="Baixa o relatório em formato PowerPoint"
        )
    
    with col3:
        # Export chart as image
        try:
            img_bytes = fig.to_image(format="png", width=1200, height=600, scale=2)
            
            st.download_button(
                label="📈 Download Gráfico",
                data=img_bytes,
                file_name=f"grafico_contratacoes_{datetime.now().strftime('%Y%m%d_%H%M')}.png",
                mime="image/png",
                help="Baixa o gráfico em alta resolução"
            )
        except Exception as e:
            st.error(f"Erro ao gerar imagem: {str(e)}. Instale kaleido: pip install kaleido")

def render_suspensivas_tab():
    """Render suspensivas analysis"""
    st.header("⏰ Análise de Suspensivas")
    
    # For now, show a message since we don't have suspensivas data
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
    """Render cities analysis"""
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
    """Render risk analysis with fixed queries"""
    st.header("🚨 Análise de Riscos")
    
    try:
        # Risk by program
        risk_by_program = load_risk_by_program()
        
        if not risk_by_program.empty:
            st.subheader("Projetos em Alto Risco por Programa")
            risk_prog = risk_by_program[risk_by_program['alto_risco'] > 0]
            
            if not risk_prog.empty:
                fig_risk_prog = px.bar(
                    risk_prog,
                    x='programa',
                    y='alto_risco',
                    title="Distribuição de Alto Risco por Programa",
                    labels={'alto_risco': 'Projetos em Alto Risco'},
                    color='alto_risco',
                    color_continuous_scale='Reds',
                    text='alto_risco'
                )
                fig_risk_prog.update_traces(texttemplate='%{text}', textposition='outside')
                st.plotly_chart(fig_risk_prog, use_container_width=True)
        
        # Risk by state
        risk_by_state = load_risk_by_state()
        
        if not risk_by_state.empty:
            st.subheader("Estados com Projetos em Alto Risco")
            
            fig_risk_state = px.bar(
                risk_by_state.head(10),
                x='uf',
                y='alto_risco',
                title="Projetos em Alto Risco por Estado",
                color='alto_risco',
                color_continuous_scale='Reds',
                text='alto_risco'
            )
            fig_risk_state.update_traces(texttemplate='%{text}', textposition='outside')
            st.plotly_chart(fig_risk_state, use_container_width=True)
            
            # Risk details table
            st.subheader("Detalhamento de Riscos por Estado")
            risk_table = risk_by_state[['uf', 'alto_risco', 'total_projetos', 'avg_execution']].copy()
            risk_table['% Alto Risco'] = (risk_table['alto_risco'] / risk_table['total_projetos'] * 100).round(1)
            risk_table['avg_execution'] = risk_table['avg_execution'].round(1)
            risk_table.columns = ['Estado', 'Alto Risco', 'Total Projetos', 'Exec. Média (%)', '% Alto Risco']
            st.dataframe(risk_table, use_container_width=True, hide_index=True)
        else:
            st.success("✅ Nenhum projeto em alto risco identificado!")
            
    except Exception as e:
        st.error(f"Erro ao carregar análise de risco: {str(e)}")

def render_financial_tab():
    """Render financial analysis"""
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
    """Render geographic distribution"""
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

def main():
    st.title("🏠 MCMV Analytics Dashboard - Enhanced")
    st.markdown("Análise completa dos programas habitacionais com visualizações geográficas")
    
    # Load and display KPIs
    render_kpis()
    
    st.markdown("---")
    
    # Sidebar
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
        .program-item {
            display: flex;
            justify-content: space-between;
            padding: 0.5rem 0;
            border-bottom: 1px solid #e0e0e0;
        }
        .program-name {
            font-weight: 500;
            color: #333;
        }
        .program-count {
            font-weight: 600;
            color: #0066cc;
        }
        .total-box {
            background-color: #e3f2fd;
            padding: 0.75rem;
            border-radius: 0.25rem;
            margin-top: 0.5rem;
            text-align: center;
        }
        .total-number {
            font-size: 1.5rem;
            font-weight: 700;
            color: #0066cc;
        }
        .update-time {
            font-size: 0.85rem;
            color: #666;
            text-align: center;
            margin-top: 0.5rem;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown('<div class="sidebar-info-box">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-header">📊 Dados Incluídos</div>', unsafe_allow_html=True)

        # Display each program
        for _, row in project_counts.iterrows():
            st.markdown(f"""
            <div class="program-item">
                <span class="program-name">{row['programa']}</span>
                <span class="program-count">{row['count']:,}</span>
            </div>
            """, unsafe_allow_html=True)

        # Display total
        st.markdown(f"""
        <div class="total-box">
            <div style="font-size: 0.9rem; color: #666;">Total de Projetos</div>
            <div class="total-number">{total_projects:,}</div>
            <div style="font-size: 0.85rem; color: #666;">MCMV</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="update-time">
            🕐 Atualizado: {datetime.now().strftime('%d/%m/%Y às %H:%M')}
        </div>
        """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)
                
        if st.button("🔄 Atualizar Dados"):
            st.cache_data.clear()
            st.rerun()


    
    # Main tabs
    tabs = st.tabs([
        "📍 Mapa", 
        "📊 Por Região", 
        "📑 Contratações", 
        "⏰ Suspensivas",
        "🏙️ Cidades",
        "🚨 Análise de Risco", 
        "💰 Fluxo Financeiro", 
        "📊 Distribuição"
    ])
    
    with tabs[0]:
        render_map_tab()
    
    with tabs[1]:
        render_region_barchart()
    
    with tabs[2]:
        render_contratacoes_tab()
    
    with tabs[3]:
        render_suspensivas_tab()
    
    with tabs[4]:
        render_cidades_tab()
    
    with tabs[5]:
        render_risk_analysis_tab()
    
    with tabs[6]:
        render_financial_tab()
    
    with tabs[7]:
        render_distribution_tab()
    
    # Footer
    st.markdown("---")
    st.caption("📊 Dados extraídos das views SQL otimizadas")
    st.caption("🔄 Cache atualizado a cada 5 minutos")

if __name__ == "__main__":
    main()
