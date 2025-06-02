"""MCMV Rural Dashboard Component"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from etl.mcmv.rural_loader import load_rural_data

def render_rural_dashboard():
    """Render MCMV Rural dashboard"""
    
    st.header("🏘️ MCMV Rural - Minha Casa Minha Vida Rural")
    
    # Load data
    with st.spinner("Carregando dados MCMV Rural..."):
        data = load_rural_data("data/mcmv/DADOS_RURAL.xlsx")
        
    if not data or data['cadastro'] is None:
        st.error("Erro ao carregar dados MCMV Rural")
        return
        
    df = data['cadastro']
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de Projetos", f"{len(df):,}")
        
    with col2:
        total_uh = df['qt_uh_construcao'].sum()
        st.metric("Total de UH", f"{total_uh:,.0f}")
        
    with col3:
        total_invest = df['valor_total_investimento'].sum()
        st.metric("Investimento Total", f"R$ {total_invest/1e9:.2f}B")
        
    with col4:
        if 'uh_entregues' in df.columns:
            uh_entregues = df['uh_entregues'].sum()
            st.metric("UH Entregues", f"{uh_entregues:,.0f}")
        else:
            em_exec = df[df['situacao_obra'].str.contains('execução|ANDAMENTO', case=False, na=False)]['qt_uh_construcao'].sum()
            st.metric("UH em Execução", f"{em_exec:,.0f}")
    
    # Add execution percentage if available
    if 'percentual_execucao' in df.columns:
        st.info(f"📊 Execução média dos projetos: {df['percentual_execucao'].mean():.1f}%")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Top states by UH
        state_summary = df.groupby('uf').agg({
            'qt_uh_construcao': 'sum'
        }).sort_values('qt_uh_construcao', ascending=True).tail(15)
        
        fig_states = px.bar(
            state_summary,
            x='qt_uh_construcao',
            y=state_summary.index,
            orientation='h',
            title='Top 15 Estados por Unidades Habitacionais',
            labels={'qt_uh_construcao': 'Unidades Habitacionais', 'index': 'Estado'}
        )
        st.plotly_chart(fig_states, use_container_width=True)
    
    with col2:
        # Status distribution
        status_dist = df.groupby('situacao_obra').agg({
            'qt_uh_construcao': 'sum'
        })
        
        fig_status = px.pie(
            values=status_dist['qt_uh_construcao'],
            names=status_dist.index,
            title='Distribuição por Situação'
        )
        st.plotly_chart(fig_status, use_container_width=True)
    
    # Progress chart if we have execution data
    if 'percentual_execucao' in df.columns:
        st.subheader("📈 Distribuição de Progresso de Execução")
        
        # Create execution bins
        bins = [0, 25, 50, 75, 90, 99, 100]
        labels = ['0-25%', '26-50%', '51-75%', '76-90%', '91-99%', '100%']
        df['exec_range'] = pd.cut(df['percentual_execucao'], bins=bins, labels=labels, include_lowest=True)
        
        exec_dist = df.groupby('exec_range').agg({
            'nu_apf': 'count',
            'qt_uh_construcao': 'sum'
        }).reset_index()
        
        fig_exec = px.bar(
            exec_dist,
            x='exec_range',
            y='qt_uh_construcao',
            title='Unidades Habitacionais por Faixa de Execução',
            labels={'exec_range': 'Faixa de Execução', 'qt_uh_construcao': 'Unidades Habitacionais'}
        )
        st.plotly_chart(fig_exec, use_container_width=True)
    
    # Detailed table
    if st.checkbox("Mostrar tabela detalhada"):
        st.subheader("Projetos MCMV Rural")
        
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            selected_states = st.multiselect(
                "Filtrar por Estado",
                options=sorted(df['uf'].unique()),
                default=[]
            )
        
        with col2:
            selected_status = st.multiselect(
                "Filtrar por Situação",
                options=df['situacao_obra'].unique(),
                default=[]
            )
        
        # Apply filters
        filtered_df = df.copy()
        if selected_states:
            filtered_df = filtered_df[filtered_df['uf'].isin(selected_states)]
        if selected_status:
            filtered_df = filtered_df[filtered_df['situacao_obra'].isin(selected_status)]
        
        # Select columns to display
        display_cols = ['nome_empreendimento', 'uf', 'municipio', 'qt_uh_construcao', 
                       'valor_total_investimento', 'situacao_obra']
        
        if 'percentual_execucao' in df.columns:
            display_cols.append('percentual_execucao')
        if 'uh_entregues' in df.columns:
            display_cols.append('uh_entregues')
            
        display_df = filtered_df[display_cols].copy()
        
        # Rename columns for display
        rename_dict = {
            'nome_empreendimento': 'Empreendimento',
            'uf': 'UF',
            'municipio': 'Município',
            'qt_uh_construcao': 'UH Planejadas',
            'valor_total_investimento': 'Investimento (R$)',
            'situacao_obra': 'Situação',
            'percentual_execucao': 'Execução %',
            'uh_entregues': 'UH Entregues'
        }
        
        display_df = display_df.rename(columns=rename_dict)
        
        # Format numeric columns
        if 'Investimento (R$)' in display_df.columns:
            display_df['Investimento (R$)'] = display_df['Investimento (R$)'].apply(lambda x: f'R$ {x:,.2f}' if pd.notna(x) else '')
        if 'Execução %' in display_df.columns:
            display_df['Execução %'] = display_df['Execução %'].apply(lambda x: f'{x:.1f}%' if pd.notna(x) else '')
        
        st.dataframe(display_df, use_container_width=True)
        
        st.caption(f"Mostrando {len(filtered_df)} de {len(df)} projetos")

if __name__ == "__main__":
    # Test function
    print("MCMV Rural Dashboard component is ready to use")
