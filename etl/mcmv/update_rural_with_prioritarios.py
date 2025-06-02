#!/usr/bin/env python3
"""Check if we should merge with prioritários data"""

import pandas as pd

# Load prioritários
prio_df = pd.read_excel("data/mcmv/DADOS_RURAL.xlsx", sheet_name="DADOS_PRORITÁRIOS_RURAL")

# Check if APF matches
print(f"Prioritários has {len(prio_df)} records")
print(f"APF column type: {prio_df['APF'].dtype}")
print(f"Sample APFs: {prio_df['APF'].head()}")
print(f"\nExecution % stats:")
print(f"  - Non-null: {prio_df['% Exec'].notna().sum()}")
print(f"  - Min: {prio_df['% Exec'].min()}")
print(f"  - Max: {prio_df['% Exec'].max()}")
print(f"  - Mean: {prio_df['% Exec'].mean():.2f}")

# Check situação
print(f"\nSituação values:")
print(prio_df['Situação do Empreendimento'].value_counts())

# Check if we can match with cadastro
cadastro_df = pd.read_excel("data/mcmv/DADOS_RURAL.xlsx", sheet_name="MONITORAMENTO_CADASTRO")
print(f"\nCadastro APFs: {cadastro_df['NU_APF'].dtype}")
print(f"Sample: {cadastro_df['NU_APF'].head()}")

# Try to match
common_apfs = set(prio_df['APF']).intersection(set(cadastro_df['NU_APF']))
print(f"\nCommon APFs between sheets: {len(common_apfs)}")
print(f"Coverage: {len(common_apfs) / len(cadastro_df) * 100:.1f}% of cadastro projects have prioritários data")
