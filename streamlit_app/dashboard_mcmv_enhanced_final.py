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

def render_contratacoes_tab():
    """Render enhanced contracting status with KPIs and visualization"""
    st.header("📑 Status de Contratações")

    summary = load_contratacoes_summary()

    st.subheader("📊 Resumo de Contratações")

    # Top 3 buckets (same layout)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.info("**AGUARDANDO AUTORIZAÇÃO MCID**")
        st.metric("Empreendimentos", f"{int(summary['aguardando_mcid']):,}".replace(",", "."))
        st.metric("UH", f"{int(summary['uh_aguardando_mcid']):,}".replace(",", "."))
        if summary['aguardando_mcid'] > 0:
            valor_est = (summary['uh_aguardando_mcid'] * 75000) / 1e6
            st.metric("Valor Estimado", f"R$ {valor_est:.2f} mi")

    with col2:
        st.warning("**AUTORIZAÇÃO MCID EMITIDA**")
        st.metric("Empreendimentos", f"{int(summary['mcid_emitida']):,}".replace(",", "."))
        st.metric("UH", f"{int(summary['uh_mcid_emitida']):,}".replace(",", "."))
        if summary['mcid_emitida'] > 0:
            valor_est = (summary['uh_mcid_emitida'] * 75000) / 1e6
            st.metric("Valor Estimado", f"R$ {valor_est:.2f} mi")

    with col3:
        st.success("**CONTRATOS EMITIDOS**")
        st.metric("Empreendimentos", f"{int(summary['contratos_emitidos']):,}".replace(",", "."))
        st.metric("UH", f"{int(summary['uh_contratos_emitidos']):,}".replace(",", "."))
        if summary['contratos_emitidos'] > 0:
            valor_est = (summary['uh_contratos_emitidos'] * 75000) / 1e6
            st.metric("Valor Estimado", f"R$ {valor_est:.2f} mi")

    st.markdown("---")

    # Distratos and Total
    col1, col2 = st.columns(2)
    with col1:
        st.error("**DISTRATOS**")
        st.metric("Empreendimentos", f"{int(summary['distratos']):,}".replace(",", "."))
        st.metric("UH", f"{int(summary['uh_distratos']):,}".replace(",", "."))

    with col2:
        st.markdown("**📊 TOTAL GERAL**")
        st.metric("Total Empreendimentos", f"{int(summary['total_empreendimentos']):,}".replace(",", "."))
        st.metric("Total UH", f"{int(summary['uh_total']):,}".replace(",", "."))
        st.metric("Valor Total", f"R$ {summary['valor_total']/1e9:.2f} bi")

    st.markdown("---")

    # Add bar chart for visual summary
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
        ]
    })

    fig = px.bar(chart_df,
                 x="Status",
                 y="UH",
                 text="UH",
                 color="Status",
                 title="📈 Unidades Habitacionais por Etapa",
                 color_discrete_sequence=px.colors.qualitative.Pastel)

    fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    fig.update_layout(height=450, xaxis_title="", yaxis_title="UH")

    st.plotly_chart(fig, use_container_width=True)

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
        st.header("ℹ️ Informações")
        st.info(f"""
        **Dados incluídos:**
        - FAR: 791 projetos
        - FDS: 109 projetos  
        - RURAL: 438 projetos
        - Faixas 1-3 e outros
        
        **Total:** 1,498 projetos MCMV
        
        **Última atualização:**
        {datetime.now().strftime('%d/%m/%Y %H:%M')}
        """)
        
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
