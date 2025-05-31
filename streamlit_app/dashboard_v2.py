#!/usr/bin/env python3
"""
PAC-MCMV Dashboard V2 - Real CAIXA Data Integration
Implements requirements from CAIXA meeting for analyzing suspensivas and delays
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from sqlalchemy import create_engine, text
import os

# Import existing text analyzer
from text_analyzer import analyze_situacao_texts, detect_delays, categorize_problems

# Page config
st.set_page_config(
    page_title="PAC-MCMV Dashboard V2 - CAIXA",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .alert-box {
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .critical { background-color: #ffebee; border-left: 5px solid #f44336; }
    .warning { background-color: #fff3e0; border-left: 5px solid #ff9800; }
    .info { background-color: #e3f2fd; border-left: 5px solid #2196f3; }
</style>
""", unsafe_allow_html=True)

# Database connection
@st.cache_resource
def get_connection():
    """Create database connection"""
    # Use environment variable or default
    db_url = os.getenv('DATABASE_URL', 'postgresql://pac_user:pac_password@localhost:5432/pac_mcmv')
    return create_engine(db_url)

# Load data with caching
@st.cache_data(ttl=300)
def load_pac_operations():
    """Load data from pac_operations table with all CAIXA fields"""
    engine = get_connection()
    
    query = """
    SELECT 
        proposta,
        operacao,
        uf,
        municipio_beneficiado,
        programa,
        objetivo,
        tipo,
        tipologia,
        situacao_do_termo_de_compromisso,
        situacao_da_proposta,
        CAST(valor_repasse AS NUMERIC) as valor_repasse,
        CAST(valor_investimento AS NUMERIC) as valor_investimento,
        CAST(valor_empenhado AS NUMERIC) as valor_empenhado,
        CAST(valor_desbloqueado AS NUMERIC) as valor_desbloqueado,
        CAST(percentual_realizado_reuni AS NUMERIC) as percentual_realizado,
        vencimento_da_suspensiva,
        suspensiva,
        situacao_da_analise_suspensiva,
        dias_sem_movimentacao,
        prazo_para_retirada_da_suspensiva_dias,
        situacao_atual,
        data_atualizacao_da_situacao_atual,
        data_atualizacao,
        etiquetas,
        regime_simplificado,
        tc_assinado,
        data_inicio_de_obra_tgov,
        data_ultimo_bm_reuni,
        classificacao_suspensiva
    FROM pac_operations
    """
    
    df = pd.read_sql(query, engine)
    
    # Convert date columns
    date_cols = ['vencimento_da_suspensiva', 'data_atualizacao_da_situacao_atual', 
                 'data_atualizacao', 'tc_assinado', 'data_inicio_de_obra_tgov', 
                 'data_ultimo_bm_reuni']
    
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Add analysis columns
    df['has_delay'] = df['situacao_atual'].fillna('').apply(detect_delays)
    df['problem_categories'] = df['situacao_atual'].fillna('').apply(categorize_problems)
    
    # Add suspensiva analysis
    df['suspensiva_vencida'] = df['vencimento_da_suspensiva'].apply(
        lambda x: x < datetime.now() if pd.notna(x) else False
    )
    
    df['dias_ate_vencimento'] = df['vencimento_da_suspensiva'].apply(
        lambda x: (x - datetime.now()).days if pd.notna(x) else None
    )
    
    # Categorize urgency
    df['urgencia'] = df['dias_ate_vencimento'].apply(
        lambda x: 'Crítico' if x is not None and x < 0 else
                  'Urgente' if x is not None and 0 <= x <= 30 else
                  'Atenção' if x is not None and 30 < x <= 60 else
                  'Normal' if x is not None else 'Sem prazo'
    )
    
    return df

def format_currency(value):
    """Format currency in Brazilian format"""
    if pd.isna(value):
        return "R$ 0,00"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def main():
    st.title("🏗️ Dashboard PAC-MCMV V2")
    st.markdown("**Análise Integrada com Foco em Suspensivas e Atrasos - Dados CAIXA**")
    
    # Load data
    try:
        with st.spinner("Carregando dados do PAC..."):
            df = load_pac_operations()
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        st.info("Verifique a conexão com o banco de dados")
        return
    
    # Sidebar filters
    st.sidebar.header("🔍 Filtros")
    
    # State filter
    estados = st.sidebar.multiselect(
        "Estados (UF)",
        options=sorted(df['uf'].unique()),
        default=[]
    )
    
    # Program filter
    programas = st.sidebar.multiselect(
        "Programas",
        options=sorted([p for p in df['programa'].unique() if pd.notna(p)]),
        default=[]
    )
    
    # Urgency filter
    urgencias = st.sidebar.multiselect(
        "Nível de Urgência",
        options=['Crítico', 'Urgente', 'Atenção', 'Normal', 'Sem prazo'],
        default=[]
    )
    
    # Delay filter
    show_delays = st.sidebar.checkbox("Apenas operações com atraso (>90 dias)", False)
    show_suspensivas = st.sidebar.checkbox("Apenas operações com suspensivas vencidas", False)
    
    # Apply filters
    filtered_df = df.copy()
    
    if estados:
        filtered_df = filtered_df[filtered_df['uf'].isin(estados)]
    
    if programas:
        filtered_df = filtered_df[filtered_df['programa'].isin(programas)]
    
    if urgencias:
        filtered_df = filtered_df[filtered_df['urgencia'].isin(urgencias)]
    
    if show_delays:
        filtered_df = filtered_df[
            (filtered_df['dias_sem_movimentacao'] > 90) | 
            (filtered_df['has_delay'] == True)
        ]
    
    if show_suspensivas:
        filtered_df = filtered_df[filtered_df['suspensiva_vencida'] == True]
    
    # Main content
    # Alert section
    st.markdown("### 🚨 Alertas Críticos")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        critical_ops = len(filtered_df[filtered_df['urgencia'] == 'Crítico'])
        st.markdown(f"""
        <div class="alert-box critical">
            <h4>Operações Críticas</h4>
            <h2>{critical_ops}</h2>
            <p>Suspensivas já vencidas</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        urgent_ops = len(filtered_df[filtered_df['urgencia'] == 'Urgente'])
        st.markdown(f"""
        <div class="alert-box warning">
            <h4>Operações Urgentes</h4>
            <h2>{urgent_ops}</h2>
            <p>Vencem em até 30 dias</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        delayed_ops = len(filtered_df[
            (filtered_df['dias_sem_movimentacao'] > 90) | 
            (filtered_df['has_delay'] == True)
        ])
        st.markdown(f"""
        <div class="alert-box info">
            <h4>Operações Paradas</h4>
            <h2>{delayed_ops}</h2>
            <p>Mais de 90 dias sem movimento</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Visão Geral",
        "⏰ Análise de Suspensivas", 
        "🚦 Atrasos e Gargalos",
        "📝 Análise de Texto",
        "🗺️ Análise Geográfica"
    ])
    
    with tab1:
        render_overview(filtered_df)
    
    with tab2:
        render_suspensivas_analysis(filtered_df)
    
    with tab3:
        render_delays_analysis(filtered_df)
    
    with tab4:
        render_text_analysis(filtered_df)
    
    with tab5:
        render_geographic_analysis(filtered_df)
    
    # Footer
    st.markdown("---")
    st.markdown(
        f"**Última atualização dos dados:** {df['data_atualizacao'].max().strftime('%d/%m/%Y') if pd.notna(df['data_atualizacao'].max()) else 'N/A'} | "
        f"**Total de operações:** {len(df):,}".replace(",", ".")
    )

def render_overview(df):
    """Render overview metrics and charts"""
    st.header("📊 Visão Geral")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_ops = len(df)
        st.metric("Total de Operações", f"{total_ops:,}".replace(",", "."))
    
    with col2:
        valor_total = df['valor_repasse'].sum() / 1e9
        st.metric("Valor Total de Repasse", f"R$ {valor_total:.2f} bi")
    
    with col3:
        avg_progress = df['percentual_realizado'].mean()
        st.metric("Progresso Médio", f"{avg_progress:.1f}%")
    
    with col4:
        municipios = df['municipio_beneficiado'].nunique()
        st.metric("Municípios Atendidos", f"{municipios:,}".replace(",", "."))
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Top programs by value
        prog_value = df.groupby('programa')['valor_repasse'].sum().sort_values(ascending=False).head(10)
        fig = px.bar(
            x=prog_value.values / 1e9,
            y=prog_value.index,
            orientation='h',
            title="Top 10 Programas por Valor de Repasse",
            labels={'x': 'Valor (R$ bilhões)', 'y': 'Programa'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Operations by status
        status_counts = df['situacao_do_termo_de_compromisso'].value_counts().head(10)
        fig = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="Distribuição por Situação",
            hole=0.4
        )
        st.plotly_chart(fig, use_container_width=True)

def render_suspensivas_analysis(df):
    """Analyze suspensivas (blocking conditions)"""
    st.header("⏰ Análise de Suspensivas")
    
    # Suspensivas overview
    total_with_suspensiva = len(df[df['suspensiva'].notna()])
    vencidas = len(df[df['suspensiva_vencida'] == True])
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Com Suspensivas", f"{total_with_suspensiva:,}".replace(",", "."))
    
    with col2:
        st.metric("Suspensivas Vencidas", vencidas)
    
    with col3:
        pct_vencidas = (vencidas / total_with_suspensiva * 100) if total_with_suspensiva > 0 else 0
        st.metric("% Vencidas", f"{pct_vencidas:.1f}%")
    
    # Urgency distribution
    urgency_counts = df['urgencia'].value_counts()
    fig = px.bar(
        x=urgency_counts.index,
        y=urgency_counts.values,
        title="Distribuição por Nível de Urgência",
        labels={'x': 'Nível de Urgência', 'y': 'Quantidade'},
        color=urgency_counts.index,
        color_discrete_map={
            'Crítico': '#d32f2f',
            'Urgente': '#f57c00',
            'Atenção': '#fbc02d',
            'Normal': '#388e3c',
            'Sem prazo': '#757575'
        }
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Critical operations table
    st.subheader("🚨 Operações Críticas (Suspensivas Vencidas)")
    
    critical_df = df[df['urgencia'] == 'Crítico'].sort_values('dias_ate_vencimento')
    
    if not critical_df.empty:
        display_cols = ['proposta', 'uf', 'municipio_beneficiado', 'programa', 
                       'vencimento_da_suspensiva', 'dias_ate_vencimento', 'situacao_atual']
        
        display_df = critical_df[display_cols].head(20).copy()
        display_df['vencimento_da_suspensiva'] = display_df['vencimento_da_suspensiva'].dt.strftime('%d/%m/%Y')
        display_df['dias_ate_vencimento'] = display_df['dias_ate_vencimento'].apply(lambda x: f"{abs(x)} dias atrás")
        
        display_df.columns = ['Proposta', 'UF', 'Município', 'Programa', 
                             'Vencimento', 'Dias Vencido', 'Situação']
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("✅ Nenhuma operação crítica encontrada")

def render_delays_analysis(df):
    """Analyze delays and bottlenecks"""
    st.header("🚦 Análise de Atrasos e Gargalos")
    
    # Delays overview
    delayed_df = df[(df['dias_sem_movimentacao'] > 90) | (df['has_delay'] == True)]
    
    col1, col2 = st.columns(2)
    
    with col1:
        # States with most delays
        delays_by_state = delayed_df['uf'].value_counts().head(10)
        fig = px.bar(
            x=delays_by_state.values,
            y=delays_by_state.index,
            orientation='h',
            title="Estados com Mais Atrasos",
            labels={'x': 'Operações Atrasadas', 'y': 'Estado'},
            color=delays_by_state.values,
            color_continuous_scale='Reds'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Programs with most delays
        if 'programa' in delayed_df.columns:
            delays_by_program = delayed_df['programa'].value_counts().head(10)
            fig = px.bar(
                x=delays_by_program.values,
                y=delays_by_program.index,
                orientation='h',
                title="Programas com Mais Atrasos",
                labels={'x': 'Operações Atrasadas', 'y': 'Programa'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Bottleneck analysis
    st.subheader("🔍 Análise de Gargalos")
    
    # Group by state and calculate metrics
    state_metrics = df.groupby('uf').agg({
        'proposta': 'count',
        'dias_sem_movimentacao': lambda x: (x > 90).sum(),
        'suspensiva_vencida': 'sum',
        'valor_repasse': 'sum'
    }).reset_index()
    
    state_metrics.columns = ['UF', 'Total_Ops', 'Ops_Paradas', 'Suspensivas_Vencidas', 'Valor_Total']
    state_metrics['Bottleneck_Score'] = (
        (state_metrics['Ops_Paradas'] / state_metrics['Total_Ops']) * 0.5 +
        (state_metrics['Suspensivas_Vencidas'] / state_metrics['Total_Ops']) * 0.5
    ) * 100
    
    state_metrics = state_metrics.sort_values('Bottleneck_Score', ascending=False)
    
    # Show bottleneck table
    st.markdown("**Estados com Maiores Gargalos** (Score: % operações paradas + % suspensivas vencidas)")
    
    display_metrics = state_metrics.head(10).copy()
    display_metrics['Valor_Total'] = display_metrics['Valor_Total'].apply(lambda x: f"R$ {x/1e6:.1f}M")
    display_metrics['Bottleneck_Score'] = display_metrics['Bottleneck_Score'].apply(lambda x: f"{x:.1f}%")
    
    st.dataframe(
        display_metrics[['UF', 'Total_Ops', 'Ops_Paradas', 'Suspensivas_Vencidas', 
                        'Valor_Total', 'Bottleneck_Score']],
        use_container_width=True,
        hide_index=True
    )

def render_text_analysis(df):
    """Text analysis of situacao_atual field"""
    st.header("📝 Análise de Texto - Situação Atual")
    
    # Get all texts
    texts = df['situacao_atual'].fillna('').tolist()
    
    # Analyze texts
    with st.spinner("Analisando textos..."):
        analysis_results = analyze_situacao_texts(texts)
    
    # Word frequency
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Palavras Mais Frequentes")
        words_data = pd.DataFrame(analysis_results['common_words'][:15], 
                                 columns=['Palavra', 'Frequência'])
        
        fig = px.bar(
            words_data,
            x='Frequência',
            y='Palavra',
            orientation='h',
            title="Top 15 Palavras (excluindo stopwords)"
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Categorias de Problemas")
        
        # Count problem categories
        all_problems = []
        for problems in df['problem_categories']:
            all_problems.extend(problems)
        
        if all_problems:
            problem_counts = pd.Series(all_problems).value_counts()
            
            fig = px.pie(
                values=problem_counts.values,
                names=problem_counts.index,
                title="Distribuição de Problemas por Categoria",
                hole=0.4
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhuma categoria de problema identificada")
    
    # Sample texts with problems
    st.subheader("📋 Exemplos de Situações com Problemas")
    
    problem_texts = df[df['has_delay'] == True].sample(min(5, len(df[df['has_delay'] == True])))
    
    for _, row in problem_texts.iterrows():
        with st.expander(f"Proposta {row['proposta']} - {row['uf']}"):
            st.write(f"**Situação:** {row['situacao_atual']}")
            st.write(f"**Problemas identificados:** {', '.join(row['problem_categories'])}")
            if pd.notna(row['dias_sem_movimentacao']):
                st.write(f"**Dias sem movimentação:** {row['dias_sem_movimentacao']}")

def render_geographic_analysis(df):
    """Geographic analysis by state"""
    st.header("🗺️ Análise Geográfica")
    
    # State summary
    state_summary = df.groupby('uf').agg({
        'proposta': 'count',
        'valor_repasse': 'sum',
        'valor_investimento': 'sum',
        'percentual_realizado': 'mean',
        'has_delay': 'sum',
        'suspensiva_vencida': 'sum'
    }).reset_index()
    
    state_summary.columns = ['UF', 'Total_Ops', 'Valor_Repasse', 'Valor_Investimento',
                           'Progresso_Medio', 'Com_Atraso', 'Suspensivas_Vencidas']
    
    state_summary['Taxa_Atraso'] = (state_summary['Com_Atraso'] / state_summary['Total_Ops'] * 100).round(1)
    
    # Map visualization
    fig = px.scatter_geo(
        state_summary,
        locations='UF',
        locationmode='geojson-id',
        size='Total_Ops',
        color='Taxa_Atraso',
        hover_data=['Valor_Repasse', 'Progresso_Medio'],
        title='Operações PAC por Estado (tamanho = quantidade, cor = taxa de atraso)',
        color_continuous_scale='RdYlGn_r'
    )
    
    # Update layout for Brazil
    fig.update_geos(
        visible=False,
        resolution=50,
        showcountries=True,
        countrycolor="RebeccaPurple",
        showcoastlines=True,
        coastlinecolor="RebeccaPurple",
        showland=True,
        landcolor="LightGreen",
        fitbounds="locations"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Regional comparison
    col1, col2 = st.columns(2)
    
    with col1:
        # Top states by value
        top_states = state_summary.nlargest(10, 'Valor_Repasse')
        fig = px.bar(
            top_states,
            x='Valor_Repasse',
            y='UF',
            orientation='h',
            title='Top 10 Estados por Valor de Repasse',
            labels={'Valor_Repasse': 'Valor (R$)'},
            text=top_states['Total_Ops']
        )
        fig.update_traces(texttemplate='%{text} ops', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # States with highest delay rates
        worst_states = state_summary.nlargest(10, 'Taxa_Atraso')
        fig = px.bar(
            worst_states,
            x='Taxa_Atraso',
            y='UF',
            orientation='h',
            title='Estados com Maiores Taxas de Atraso',
            labels={'Taxa_Atraso': 'Taxa de Atraso (%)'},
            color='Taxa_Atraso',
            color_continuous_scale='Reds'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed state table
    st.subheader("📊 Resumo Detalhado por Estado")
    
    display_summary = state_summary.copy()
    display_summary['Valor_Repasse'] = display_summary['Valor_Repasse'].apply(
        lambda x: f"R$ {x/1e6:.1f}M"
    )
    display_summary['Progresso_Medio'] = display_summary['Progresso_Medio'].apply(
        lambda x: f"{x:.1f}%"
    )
    display_summary['Taxa_Atraso'] = display_summary['Taxa_Atraso'].apply(
        lambda x: f"{x:.1f}%"
    )
    
    st.dataframe(
        display_summary.sort_values('Total_Ops', ascending=False),
        use_container_width=True,
        hide_index=True
    )

if __name__ == "__main__":
    main()
