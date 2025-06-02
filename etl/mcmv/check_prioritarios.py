#!/usr/bin/env python3
"""Check prioritários sheet structure"""

import pandas as pd

# Check the prioritários sheet
df = pd.read_excel("data/mcmv/DADOS_RURAL.xlsx", sheet_name="DADOS_PRORITÁRIOS_RURAL")
print("=== DADOS_PRORITÁRIOS_RURAL columns ===")
for i, col in enumerate(df.columns):
    if 'EXEC' in col or 'PC_' in col or 'PERCENT' in col or 'OBRA' in col:
        print(f"{i}: {col}")

print(f"\nTotal rows: {len(df)}")
print("\nAll columns:")
for i, col in enumerate(df.columns):
    print(f"{i}: {col}")
