#!/usr/bin/env python3
"""Test Rural MCMV data loader"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from etl.mcmv.rural_loader import load_rural_data

if __name__ == "__main__":
    print("🚀 Testing Rural MCMV data loader...")
    
    data = load_rural_data("data/mcmv/DADOS_RURAL.xlsx")
    
    if data and data['cadastro'] is not None:
        df = data['cadastro']
        print(f"\n✅ Successfully loaded {len(df)} rural projects")
        print(f"\nSample data:")
        print(df[['nome_empreendimento', 'uf', 'municipio', 'qt_uh_construcao']].head())
        
        print(f"\nSummary by state:")
        summary = df.groupby('uf').agg({
            'qt_uh_construcao': 'sum',
            'valor_total_investimento': 'sum'
        }).round(2)
        print(summary.head(10))
    else:
        print("❌ Failed to load Rural data")
