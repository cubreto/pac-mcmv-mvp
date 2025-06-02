#!/usr/bin/env python3
"""Test enhanced Rural MCMV data loader"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from etl.mcmv.rural_loader import load_rural_data

if __name__ == "__main__":
    print("🚀 Testing enhanced Rural MCMV data loader...")
    
    data = load_rural_data("data/mcmv/DADOS_RURAL.xlsx")
    
    if data and data['cadastro'] is not None:
        df = data['cadastro']
        print(f"\n✅ Successfully loaded {len(df)} rural projects")
        
        # Check if we have enhanced data
        if 'percentual_execucao' in df.columns:
            print(f"✨ Enhanced data available:")
            print(f"   - Projects with execution %: {df['percentual_execucao'].notna().sum()}")
            print(f"   - Average execution: {df['percentual_execucao'].mean():.1f}%")
            
        if 'uh_entregues' in df.columns:
            total_delivered = df['uh_entregues'].sum()
            total_planned = df['qt_uh_construcao'].sum()
            print(f"   - UH delivered: {total_delivered:,.0f} of {total_planned:,.0f} ({total_delivered/total_planned*100:.1f}%)")
            
        print(f"\n📊 Status distribution:")
        print(df['situacao_obra'].value_counts())
        
        print(f"\n🏆 Top 5 completed projects:")
        completed = df[df['situacao_obra'] == 'CONCLUÍDO E ENTREGUE'].nlargest(5, 'qt_uh_construcao')
        for _, row in completed.iterrows():
            print(f"   - {row['nome_empreendimento'][:50]}... ({row['qt_uh_construcao']} UH)")
    else:
        print("❌ Failed to load Rural data")
