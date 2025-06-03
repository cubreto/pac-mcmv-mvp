#!/usr/bin/env python3
"""
MCMV Complete Dashboard - All three housing programs
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from etl.mcmv.complete.unified_loader import UnifiedMCMVLoader

# Page config
st.set_page_config(
    page_title="MCMV Dashboard - Complete",
    page_icon="🏠",
    layout="wide"
)

@st.cache_data(ttl=3600)
def load_mcmv_data():
    """Load all MCMV data"""
    loader = UnifiedMCMVLoader("data/mcmv/HIS")
    return loader.load_all(), loader.get_summary()

def main():
    st.title("🏠 MCMV Dashboard - Minha Casa Minha Vida")
    st.markdown("Dashboard unificado dos três programas habitacionais")
    
    # Load data
    with st.spinner("Carregando dados MCMV..."):
        df, summary = load_mcmv_data()
    
    if df is None:
        st.error("Erro ao carregar dados")
        return
    
    # Clean data - remove rows with missing state
    df = df.dropna(subset=['SG_UF'])
    
    # Sidebar filters
    st.sidebar.header("Filtros")
    
    selected_programs = st.sidebar.multiselect(
        "Programas",
        options=df['program_code'].unique(),
        default=df['program_code'].unique()
    )
    
    # Get unique states and remove any remaining NaN
    unique_states = df['SG_UF'].dropna().unique()
    selected_states = st.sidebar.multiselect(
        "Estados",
        options=sorted(unique_states),
        default=[]
    )
    
    # Apply filters
    filtered_df = df.copy()
    if selected_programs:
        filtered_df = filtered_df[filtered_df['program_code'].isin(selected_programs)]
    if selected_states:
        filtered_df = filtered_df[filtered_df['SG_UF'].isin(selected_states)]
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Projetos", f"{len(filtered_df):,}")
    
    with col2:
        st.metric("Estados", filtered_df['SG_UF'].nunique())
    
    with col3:
        expected_total = sum(summary['total_expected_units'].values()) - summary['total_expected_units']['TOTAL']
        st.metric("UH Esperadas", f"{expected_total:,}")
    
    with col4:
        if expected_total > 0:
            percentage = (len(df)/expected_total)*100
        else:
            percentage = 0
        st.metric("Dados Carregados", f"{percentage:.1f}%")
    
    # Program breakdown
    st.subheader("Distribuição por Programa")
    col1, col2 = st.columns(2)
    
    with col1:
        program_counts = filtered_df['program_code'].value_counts()
        
        fig_programs = px.pie(
            values=program_counts.values,
            names=program_counts.index,
            title="Projetos por Programa",
            hole=0.4
        )
        st.plotly_chart(fig_programs, use_container_width=True)
    
    with col2:
        # Program summary table
        program_summary = pd.DataFrame({
            'Programa': ['FAR', 'FDS', 'RURAL'],
            'Projetos (Amostra)': [
                program_counts.get('FAR', 0),
                program_counts.get('FDS', 0),
                program_counts.get('RURAL', 0)
            ],
            'UH Esperadas': [133440, 24606, 30729]
        })
        st.dataframe(program_summary, use_container_width=True, hide_index=True)
    
    # State distribution
    st.subheader("Distribuição Geográfica")
    state_counts = filtered_df['SG_UF'].value_counts().head(15)
    
    fig_states = px.bar(
        x=state_counts.values,
        y=state_counts.index,
        orientation='h',
        title="Top 15 Estados por Número de Projetos",
        labels={'x': 'Número de Projetos', 'y': 'Estado'},
        color=state_counts.values,
        color_continuous_scale='Blues'
    )
    st.plotly_chart(fig_states, use_container_width=True)
    
    # Data table
    if st.checkbox("Mostrar dados detalhados"):
        display_columns = ['NU_APF', 'program_name', 'NO_EMPREENDIMENTO', 'SG_UF']
        if 'state_name' in filtered_df.columns:
            display_columns.append('state_name')
        if 'building_type_name' in filtered_df.columns:
            display_columns.append('building_type_name')
            
        st.dataframe(
            filtered_df[display_columns],
            use_container_width=True
        )
    
    # Footer
    st.markdown("---")
    st.caption("⚠️ Nota: Estes são arquivos de AMOSTRA. Os dados completos contêm 188.775 unidades habitacionais.")

if __name__ == "__main__":
    main()
