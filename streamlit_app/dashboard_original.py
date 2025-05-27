import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
from pathlib import Path
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from etl.database import DatabaseManager

# Simple text analysis functions
from text_analyzer import analyze_situacao_texts, categorize_problems, detect_delays

st.set_page_config(
    page_title="PAC-MCMV MVP Dashboard",
    page_icon="🏗️",
    layout="wide"
)

@st.cache_data
def load_data_from_database():
    """Load data from PostgreSQL database"""
    try:
        db = DatabaseManager()
        df = db.get_all_projects()
        return df
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None

def main():
    st.title("🏗️ PAC-MCMV MVP Dashboard")
    st.markdown("**Análise unificada PAC + Habitação - Foco na 'Situação Atual'**")
    
    # Load data from database
    with st.spinner("Carregando dados do banco..."):
        df = load_data_from_database()
    
    if df is None or df.empty:
        st.error("Não foi possível carregar dados do banco de dados")
        st.info("Execute primeiro: `python etl/run_etl.py`")
        return
    
    # Sidebar filters
    st.sidebar.header("🎛️ Filtros")
    
    # Program type filter
    program_types = ['Todos'] + sorted(df['tipo_programa'].unique().tolist())
    selected_program = st.sidebar.selectbox("Tipo de Programa", program_types)
    
    if selected_program != 'Todos':
        df = df[df['tipo_programa'] == selected_program]
    
    # State filter
    estados = ['Todos'] + sorted(df['uf'].dropna().unique().tolist())
    selected_estado = st.sidebar.selectbox("Estado", estados)
    
    if selected_estado != 'Todos':
        df = df[df['uf'] == selected_estado]
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Visão Geral", 
        "📝 Análise de Texto",
        "🚨 Problemas por Programa", 
        "🗺️ Análise Geográfica"
    ])
    
    with tab1:
        render_overview(df)
    
    with tab2:
        render_text_analysis(df)
    
    with tab3:
        render_program_problems(df)
    
    with tab4:
        render_geographic_analysis(df)

def render_overview(df):
    """Render overview tab"""
    st.header("📊 Visão Geral dos Projetos")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de Projetos", len(df))
    
    with col2:
        pac_count = len(df[df['tipo_programa'] == 'PAC'])
        st.metric("Projetos PAC", pac_count)
    
    with col3:
        hab_count = len(df[df['tipo_programa'] == 'HABITACAO'])
        st.metric("Projetos Habitação", hab_count)
    
    with col4:
        # Count projects with delay indicators
        delay_count = sum(detect_delays(text) for text in df['situacao_atual'].fillna(''))
        delay_pct = (delay_count / len(df)) * 100 if len(df) > 0 else 0
        st.metric("Com Atrasos", f"{delay_count} ({delay_pct:.1f}%)")
    
    # Program distribution
    col1, col2 = st.columns(2)
    
    with col1:
        program_counts = df['tipo_programa'].value_counts()
        fig = px.pie(
            values=program_counts.values,
            names=program_counts.index,
            title="Distribuição PAC vs Habitação"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Financial summary
        financial_summary = df.groupby('tipo_programa').agg({
            'valor_repasse': 'sum',
            'valor_investimento': 'sum'
        }).reset_index()
        
        fig = px.bar(
            financial_summary,
            x='tipo_programa',
            y=['valor_repasse', 'valor_investimento'],
            title="Valores Financeiros por Programa",
            labels={'value': 'Valor (R$)', 'tipo_programa': 'Tipo de Programa'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent projects table
    st.subheader("Projetos Recentes")
    recent_df = df.nlargest(10, 'data_atualizacao_situacao')[
        ['proposta', 'uf', 'programa', 'tipo_programa', 'situacao_atual']
    ]
    st.dataframe(recent_df, use_container_width=True)

def render_text_analysis(df):
    """Render text analysis tab"""
    st.header("📝 Análise de Texto - Situação Atual")
    
    # Analyze all situacao_atual texts
    texts = df['situacao_atual'].fillna('').tolist()
    
    with st.spinner("Analisando textos..."):
        analysis_results = analyze_situacao_texts(texts)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Most common words
        st.subheader("Palavras Mais Frequentes")
        words_data = pd.DataFrame(analysis_results['common_words'], columns=['Palavra', 'Frequência'])
        
        fig = px.bar(
            words_data.head(10),
            x='Frequência',
            y='Palavra',
            orientation='h',
            title="Top 10 Palavras"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Problem categories
        st.subheader("Categorias de Problemas")
        
        problem_counts = {}
        for text in texts:
            problems = categorize_problems(text)
            for problem in problems:
                problem_counts[problem] = problem_counts.get(problem, 0) + 1
        
        if problem_counts:
            problems_df = pd.DataFrame(list(problem_counts.items()), columns=['Categoria', 'Frequência'])
            problems_df = problems_df.sort_values('Frequência', ascending=False)
            
            fig = px.bar(
                problems_df,
                x='Frequência',
                y='Categoria',
                orientation='h',
                title="Tipos de Problemas Identificados"
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhuma categoria específica identificada")
    
    # Status classification
    st.subheader("Classificação de Status")
    
    status_counts = {'Com Problemas': 0, 'Normal': 0, 'Neutro': 0}
    
    for text in texts:
        if detect_delays(text):
            status_counts['Com Problemas'] += 1
        elif any(word in text.lower() for word in ['concluído', 'finalizada', 'executada', 'aprovada']):
            status_counts['Normal'] += 1
        else:
            status_counts['Neutro'] += 1
    
    status_df = pd.DataFrame(list(status_counts.items()), columns=['Status', 'Quantidade'])
    
    fig = px.pie(
        status_df,
        values='Quantidade',
        names='Status',
        title="Distribuição de Status dos Projetos",
        color_discrete_map={
            'Com Problemas': '#ff4444',
            'Normal': '#44ff44', 
            'Neutro': '#ffaa44'
        }
    )
    st.plotly_chart(fig, use_container_width=True)

def render_program_problems(df):
    """Render program-specific problems analysis"""
    st.header("🚨 Problemas por Tipo de Programa")
    
    # Analyze problems by program type
    program_analysis = {}
    
    for program_type in df['tipo_programa'].unique():
        program_df = df[df['tipo_programa'] == program_type]
        texts = program_df['situacao_atual'].fillna('').tolist()
        
        # Count delays and problems
        delay_count = sum(detect_delays(text) for text in texts)
        delay_rate = (delay_count / len(texts)) * 100 if texts else 0
        
        # Categorize problems
        all_problems = []
        for text in texts:
            if detect_delays(text):
                all_problems.extend(categorize_problems(text))
        
        problem_counts = pd.Series(all_problems).value_counts().to_dict()
        
        program_analysis[program_type] = {
            'total_projects': len(program_df),
            'delay_count': delay_count,
            'delay_rate': delay_rate,
            'top_problems': problem_counts
        }
    
    # Display comparison
    col1, col2 = st.columns(2)
    
    with col1:
        # Delay rates by program
        delay_data = []
        for program, stats in program_analysis.items():
            delay_data.append({
                'Programa': program,
                'Taxa_Atraso': stats['delay_rate'],
                'Total_Projetos': stats['total_projects']
            })
        
        delay_df = pd.DataFrame(delay_data)
        
        fig = px.bar(
            delay_df,
            x='Programa',
            y='Taxa_Atraso',
            title="Taxa de Atrasos por Tipo de Programa",
            labels={'Taxa_Atraso': 'Taxa de Atrasos (%)'},
            color='Taxa_Atraso',
            color_continuous_scale='Reds'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Problem breakdown
        st.subheader("Principais Problemas por Programa")
        
        for program_type, stats in program_analysis.items():
            st.write(f"**{program_type}**")
            st.write(f"- {stats['delay_count']} projetos com atrasos de {stats['total_projects']} ({stats['delay_rate']:.1f}%)")
            
            if stats['top_problems']:
                top_3_problems = dict(list(stats['top_problems'].items())[:3])
                for problem, count in top_3_problems.items():
                    st.write(f"  • {problem}: {count}")
            else:
                st.write("  • Nenhum problema específico identificado")
            st.write("")

def render_geographic_analysis(df):
    """Render geographic analysis"""
    st.header("🗺️ Análise Geográfica")
    
    # State-level analysis
    state_summary = []
    
    for uf in df['uf'].dropna().unique():
        state_df = df[df['uf'] == uf]
        texts = state_df['situacao_atual'].fillna('').tolist()
        
        total_projects = len(state_df)
        delay_projects = sum(detect_delays(text) for text in texts)
        delay_rate = (delay_projects / total_projects) * 100 if total_projects > 0 else 0
        
        pac_count = len(state_df[state_df['tipo_programa'] == 'PAC'])
        hab_count = len(state_df[state_df['tipo_programa'] == 'HABITACAO'])
        
        total_investment = state_df['valor_investimento'].fillna(0).sum()
        
        state_summary.append({
            'UF': uf,
            'Total_Projetos': total_projects,
            'Projetos_PAC': pac_count,
            'Projetos_Habitacao': hab_count,
            'Projetos_Atraso': delay_projects,
            'Taxa_Atraso': delay_rate,
            'Investimento_Total': total_investment
        })
    
    state_df = pd.DataFrame(state_summary)
    state_df = state_df.sort_values('Total_Projetos', ascending=False)
    
    # Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        # Projects by state
        fig = px.bar(
            state_df.head(15),  # Top 15 states
            x='UF',
            y='Total_Projetos',
            title="Projetos por Estado (Top 15)",
            labels={'Total_Projetos': 'Total de Projetos'},
            color='Total_Projetos',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Delay rate by state
        fig = px.bar(
            state_df.sort_values('Taxa_Atraso', ascending=False).head(15),
            x='UF', 
            y='Taxa_Atraso',
            title="Taxa de Atrasos por Estado (Top 15)",
            labels={'Taxa_Atraso': 'Taxa de Atrasos (%)'},
            color='Taxa_Atraso',
            color_continuous_scale='Reds'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed table
    st.subheader("Resumo Detalhado por Estado")
    
    display_df = state_df.copy()
    display_df['Taxa_Atraso'] = display_df['Taxa_Atraso'].round(1)
    display_df['Investimento_Total'] = display_df['Investimento_Total'].apply(
        lambda x: f"R$ {x/1000000:.1f}M" if x >= 1000000 else f"R$ {x/1000:.0f}K"
    )
    
    display_df = display_df.rename(columns={
        'UF': 'Estado',
        'Total_Projetos': 'Total',
        'Projetos_PAC': 'PAC',
        'Projetos_Habitacao': 'Habitação',
        'Projetos_Atraso': 'Atrasos',
        'Taxa_Atraso': 'Taxa (%)',
        'Investimento_Total': 'Investimento'
    })
    
    st.dataframe(display_df, use_container_width=True)

if __name__ == "__main__":
    main()
