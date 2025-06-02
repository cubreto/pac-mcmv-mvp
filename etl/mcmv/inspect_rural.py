#!/usr/bin/env python3
"""Inspect Rural MCMV data structure"""

import pandas as pd
import sys
from pathlib import Path

# Check the MONITORAMENTO_CADASTRO sheet
df = pd.read_excel("data/mcmv/DADOS_RURAL.xlsx", sheet_name="MONITORAMENTO_CADASTRO")
print("=== MONITORAMENTO_CADASTRO columns ===")
for i, col in enumerate(df.columns):
    print(f"{i}: {col}")

print(f"\nTotal rows: {len(df)}")
print("\nFirst 5 rows sample:")
print(df.head())
