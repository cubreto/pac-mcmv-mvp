#!/usr/bin/env python3
"""Analyze loaded Rural MCMV data"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from etl.mcmv.rural_loader import load_rural_data
import pandas as pd

def analyze_rural_data():
    print("📊 Analyzing MCMV Rural Data...\n")
    
    data = load_rural_data("data/mcmv/DADOS_RURAL.xlsx")
    
    if not data or data['cadastro'] is None:
        print("❌ Failed to load data")
        return
        
    df = data['cadastro']
    
    print(f"📈 OVERALL STATISTICS")
    print(f"{'='*50}")
    print(f"Total Projects: {len(df):,}")
    print(f"Total UH (Housing Units): {df['qt_uh_construcao'].sum():,.0f}")
    print(f"Total Investment: R$ {df['valor_total_investimento'].sum():,.2f}")
    
    print(f"\n📍 BY STATE")
    print(f"{'='*50}")
    state_summary = df.groupby('uf').agg({
        'nu_apf': 'count',
        'qt_uh_construcao': 'sum',
        'valor_total_investimento': 'sum'
    }).rename(columns={
        'nu_apf': 'projects',
        'qt_uh_construcao': 'total_uh',
        'valor_total_investimento': 'total_investment'
    }).sort_values('total_uh', ascending=False)
    
    print(f"{'State':<6} {'Projects':>10} {'UH':>12} {'Investment (R$)':>20}")
    print("-" * 50)
    for state, row in state_summary.head(10).iterrows():
        print(f"{state:<6} {row['projects']:>10,} {row['total_uh']:>12,.0f} {row['total_investment']:>20,.2f}")
    
    print(f"\n🏗️ BY STATUS")
    print(f"{'='*50}")
    status_summary = df.groupby('situacao_obra').agg({
        'nu_apf': 'count',
        'qt_uh_construcao': 'sum'
    }).rename(columns={
        'nu_apf': 'projects',
        'qt_uh_construcao': 'total_uh'
    })
    
    print(f"{'Status':<20} {'Projects':>10} {'UH':>12}")
    print("-" * 45)
    for status, row in status_summary.iterrows():
        print(f"{status:<20} {row['projects']:>10,} {row['total_uh']:>12,.0f}")
    
    # Check if we have beneficiary data
    if data['beneficiarios'] is not None:
        print(f"\n👥 BENEFICIARIES")
        print(f"{'='*50}")
        print(f"Total Projects with Beneficiaries: {len(data['beneficiarios']):,}")
        
        # The beneficiaries data is already aggregated
        avg_beneficiaries = data['beneficiarios']['num_beneficiarios'].mean()
        max_beneficiaries = data['beneficiarios']['num_beneficiarios'].max()
        print(f"Average Beneficiaries per Project: {avg_beneficiaries:.1f}")
        print(f"Max Beneficiaries per Project: {max_beneficiaries}")
    
    # Top 10 projects by UH
    print(f"\n🏆 TOP 10 PROJECTS BY HOUSING UNITS")
    print(f"{'='*50}")
    top_projects = df.nlargest(10, 'qt_uh_construcao')[['nome_empreendimento', 'uf', 'municipio', 'qt_uh_construcao']]
    for idx, row in top_projects.iterrows():
        name = row['nome_empreendimento'][:40] + '...' if len(row['nome_empreendimento']) > 40 else row['nome_empreendimento']
        print(f"{name:<45} {row['uf']:<3} {row['qt_uh_construcao']:>5,.0f} UH")

if __name__ == "__main__":
    analyze_rural_data()
