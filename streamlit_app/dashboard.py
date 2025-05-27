#!/usr/bin/env python3
"""
Simple PAC-MCMV Dashboard - Works with actual data structure
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import database and text analyzer
from etl.database import DatabaseManager
from streamlit_app.text_analyzer import analyze_situacao_texts, detect_delays, categorize_problems

# Page config
st.set_page_config(
    page_title="PAC-MCMV Dashboard",
    page_icon="🏗️",
    layout="wide"
)

# Database connection
@st.cache_resource
def get_db():
    return DatabaseManager()

# Load data
@st.cache_data(ttl=300)
def load_data():
    """Load data from database with actual column names"""
    db = get_db()
    
    # Use actual column names from your data
    query = """
    SELECT 
        programa,
        proposta,
        uf,
        municipio_beneficiado,
        tipo_programa,
        valor_repasse,
        valor_investimento,
        percentual_obra_realizado,
        data_inicio_obra,
        situacao_atual,
        data_atualizacao_situacao
    FROM projeto_status
    """
    
    df = db.load_dataframe(query)
    
    # Add analysis columns
    df['has_delay'] = df['situacao_atual'].apply(detect_delays)
    df['problem_categories'] = df['situacao_atual'].apply(categorize_problems)
    
    return df

def main():
    st.title("🏗️ PAC-MCMV Dashboard")
    st.markdown("Análise da 'Situação Atual' - Dados Reais PAC")
    
    # Load data
    try:
        df = load_data()
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        st.info("Execute primeiro: `python etl/run_etl.py`")
        return
    
    # Sidebar filters
    st.sidebar.header("Filtros")
    
    # State filter
    states = st.sidebar.multiselect(
        "Estado (UF)",
        options=sorted(df['uf'].unique()),
        default=sorted(df['uf'].unique())
    )
    
    # Program type filter  
    if 'tipo_programa' in df.columns and df['tipo_programa'].notna().any():
        program_types = st.sidebar.multiselect(
            "Tipo de Programa",
            options=sorted(df['tipo_programa'].dropna().unique()),
            default=sorted(df['tipo_programa'].dropna().unique())
        )
        filtered_df = df[df['uf'].isin(states) & df['tipo_programa'].isin(program_types)]
    else:
        filtered_df = df[df['uf'].isin(states)]
    
    # Delay filter
    show_delays_only = st.sidebar.checkbox("Mostrar apenas projetos com atrasos", False)
    
    if show_delays_only:
        filtered_df = filtered_df[filtered_df['has_delay']]
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Visão Geral", "📝 Análise de Texto", "⚠️ Problemas", "🗺️ Por Estado"])
    
    with tab1:
        # KPIs
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Projetos", f"{len(filtered_df):,}")
        
        with col2:
            total_value = filtered_df['valor_repasse'].sum()
            st.metric("Valor Total Repasse", f"R$ {total_value/1e9:.2f}B")
        
        with col3:
            delay_pct = (filtered_df['has_delay'].sum() / len(filtered_df) * 100) if len(filtered_df) > 0 else 0
            st.metric("Projetos com Atrasos", f"{delay_pct:.1f}%")
        
        with col4:
            avg_progress = filtered_df['percentual_obra_realizado'].mean()
            st.metric("Progresso Médio", f"{avg_progress:.1f}%")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Projects by state
            state_counts = filtered_df['uf'].value_counts().head(10)
            fig = px.bar(
                x=state_counts.values,
                y=state_counts.index,
                orientation='h',
                title="Top 10 Estados por Número de Projetos",
                labels={'x': 'Número de Projetos', 'y': 'Estado'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Progress distribution
            fig = px.histogram(
                filtered_df,
                x='percentual_obra_realizado',
                nbins=20,
                title="Distribuição de Progresso das Obras (%)",
                labels={'percentual_obra_realizado': 'Progresso (%)'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Investment vs Repasse comparison
        st.subheader("💰 Comparação: Valor Investimento vs Repasse")
        
        inv_rep_df = filtered_df.groupby('uf').agg({
            'valor_investimento': 'sum',
            'valor_repasse': 'sum'
        }).reset_index()
        inv_rep_df = inv_rep_df.sort_values('valor_repasse', ascending=False).head(15)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(name='Investimento', x=inv_rep_df['uf'], y=inv_rep_df['valor_investimento']))
        fig.add_trace(go.Bar(name='Repasse', x=inv_rep_df['uf'], y=inv_rep_df['valor_repasse']))
        fig.update_layout(title='Top 15 Estados: Investimento vs Repasse', barmode='group')
        st.plotly_chart(fig, use_container_width=True)
        
        # Sample texts
        st.subheader("📋 Exemplos de Situação Atual")
        sample_texts = filtered_df[filtered_df['situacao_atual'].notna()].sample(min(5, len(filtered_df)))
        for _, row in sample_texts.iterrows():
            with st.expander(f"{row['uf']} - {row['municipio_beneficiado']} - {row['proposta']}"):
                st.write(f"**Situação:** {row['situacao_atual']}")
                st.write(f"**Progresso:** {row['percentual_obra_realizado']:.1f}%")
                st.write(f"**Valor Repasse:** R$ {row['valor_repasse']:,.2f}")
                if row['has_delay']:
                    st.warning("⚠️ Possível atraso detectado")
    
    with tab2:
        st.header("📝 Análise de Texto - Situação Atual")
        
        # Get all situacao texts
        texts = filtered_df['situacao_atual'].dropna().tolist()
        
        if texts:
            # Analyze texts
            analysis = analyze_situacao_texts(texts)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🔤 Palavras Mais Frequentes")
                st.info(f"Analisando {len(texts)} textos de situação")
                
                words_df = pd.DataFrame(analysis['common_words'], columns=['Palavra', 'Frequência'])
                fig = px.bar(
                    words_df.head(15),
                    x='Frequência',
                    y='Palavra',
                    orientation='h',
                    title="Top 15 Palavras (excluindo stopwords)"
                )
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("📊 Categorias de Problemas Identificados")
                
                # Count problem categories
                all_categories = []
                for cats in filtered_df['problem_categories']:
                    all_categories.extend(cats)
                
                if all_categories:
                    cat_counts = pd.Series(all_categories).value_counts()
                    fig = px.pie(
                        values=cat_counts.values,
                        names=cat_counts.index,
                        title="Distribuição de Tipos de Problemas",
                        hole=0.4
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Nenhuma categoria específica de problema identificada nos textos")
            
            # Key insights
            st.subheader("🔍 Insights Principais")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Textos Analisados", len(texts))
            with col2:
                st.metric("Textos com Indicação de Atraso", analysis['delay_count'])
            with col3:
                delay_rate = (analysis['delay_count'] / len(texts) * 100) if len(texts) > 0 else 0
                st.metric("Taxa de Atraso Detectada", f"{delay_rate:.1f}%")
        else:
            st.warning("Nenhum texto de situação disponível para análise")
    
    with tab3:
        st.header("⚠️ Projetos com Problemas")
        
        # Projects with delays
        delayed_df = filtered_df[filtered_df['has_delay']]
        
        if not delayed_df.empty:
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total com Atrasos", f"{len(delayed_df):,}")
            
            with col2:
                delay_value = delayed_df['valor_repasse'].sum()
                st.metric("Valor em Risco", f"R$ {delay_value/1e6:.1f}M")
            
            with col3:
                avg_progress_delayed = delayed_df['percentual_obra_realizado'].mean()
                st.metric("Progresso Médio (Atrasados)", f"{avg_progress_delayed:.1f}%")
            
            # Problem categories breakdown
            st.subheader("🏷️ Tipos de Problemas por Estado")
            
            problem_data = []
            for idx, row in delayed_df.iterrows():
                for category in row['problem_categories']:
                    problem_data.append({
                        'Categoria': category,
                        'UF': row['uf'],
                        'Valor': row['valor_repasse']
                    })
            
            if problem_data:
                problem_df = pd.DataFrame(problem_data)
                problem_summary = problem_df.groupby(['Categoria', 'UF']).agg({
                    'Valor': ['sum', 'count']
                }).reset_index()
                problem_summary.columns = ['Categoria', 'UF', 'Valor_Total', 'Quantidade']
                
                # Top states with problems
                top_problem_states = problem_summary.groupby('UF')['Quantidade'].sum().sort_values(ascending=False).head(10)
                
                fig = px.bar(
                    x=top_problem_states.values,
                    y=top_problem_states.index,
                    orientation='h',
                    title="Top 10 Estados com Mais Problemas Identificados",
                    labels={'x': 'Número de Problemas', 'y': 'Estado'}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Detailed table
            st.subheader("📋 Detalhes dos Projetos com Atrasos")
            
            # Select columns to display
            display_cols = ['proposta', 'uf', 'municipio_beneficiado', 
                          'valor_repasse', 'percentual_obra_realizado', 'situacao_atual']
            
            # Format the dataframe for display
            display_df = delayed_df[display_cols].copy()
            display_df.columns = ['Proposta', 'UF', 'Município', 'Valor Repasse', 'Progresso %', 'Situação']
            
            # Format currency
            display_df['Valor Repasse'] = display_df['Valor Repasse'].apply(lambda x: f'R$ {x:,.2f}')
            display_df['Progresso %'] = display_df['Progresso %'].apply(lambda x: f'{x:.1f}%')
            
            st.dataframe(
                display_df.head(20),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.success("✅ Nenhum projeto com atraso identificado!")
    
    with tab4:
        st.header("🗺️ Análise por Estado")
        
        # State summary
        state_summary = filtered_df.groupby('uf').agg({
            'proposta': 'count',
            'valor_repasse': 'sum',
            'valor_investimento': 'sum',
            'percentual_obra_realizado': 'mean',
            'has_delay': 'sum'
        }).reset_index()
        
        state_summary.columns = ['UF', 'Total_Projetos', 'Valor_Repasse', 'Valor_Investimento', 'Progresso_Medio', 'Projetos_Atrasados']
        state_summary['Pct_Atrasados'] = (state_summary['Projetos_Atrasados'] / state_summary['Total_Projetos'] * 100).round(1)
        
        # Top states by value
        fig = px.treemap(
            state_summary,
            path=['UF'],
            values='Valor_Repasse',
            color='Pct_Atrasados',
            hover_data=['Total_Projetos', 'Progresso_Medio'],
            color_continuous_scale='RdYlGn_r',
            title='Estados por Valor de Repasse (cor indica % de atrasos)'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # State ranking table
        st.subheader("🏆 Ranking de Estados")
        
        state_summary['Valor_Repasse_M'] = (state_summary['Valor_Repasse'] / 1e6).round(2)
        state_summary['Valor_Investimento_M'] = (state_summary['Valor_Investimento'] / 1e6).round(2)
        
        display_summary = state_summary[['UF', 'Total_Projetos', 'Valor_Repasse_M', 
                                       'Valor_Investimento_M', 'Progresso_Medio', 'Pct_Atrasados']].sort_values(
            'Total_Projetos', ascending=False
        )
        
        display_summary.columns = ['Estado', 'Total Projetos', 'Repasse (R$ M)', 
                                 'Investimento (R$ M)', 'Progresso Médio (%)', '% Atrasados']
        
        st.dataframe(
            display_summary.style.format({
                'Repasse (R$ M)': '{:,.2f}',
                'Investimento (R$ M)': '{:,.2f}',
                'Progresso Médio (%)': '{:.1f}',
                '% Atrasados': '{:.1f}'
            }),
            use_container_width=True,
            hide_index=True
        )
        
        # Additional insights
        st.subheader("💡 Insights por Estado")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # States with highest delay rate
            worst_states = state_summary.nlargest(5, 'Pct_Atrasados')[['UF', 'Pct_Atrasados']]
            st.write("**Estados com Maior % de Atrasos:**")
            for _, row in worst_states.iterrows():
                st.write(f"- {row['UF']}: {row['Pct_Atrasados']:.1f}%")
        
        with col2:
            # States with best progress
            best_states = state_summary.nlargest(5, 'Progresso_Medio')[['UF', 'Progresso_Medio']]
            st.write("**Estados com Melhor Progresso Médio:**")
            for _, row in best_states.iterrows():
                st.write(f"- {row['UF']}: {row['Progresso_Medio']:.1f}%")

if __name__ == "__main__":
    main()
