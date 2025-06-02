#!/usr/bin/env python3
"""Check EXEC_TS sheet columns"""

import pandas as pd

# Check the EXEC_TS sheet
df = pd.read_excel("data/mcmv/DADOS_RURAL.xlsx", sheet_name="EXEC_TS")
print("=== EXEC_TS columns ===")
for i, col in enumerate(df.columns):
    print(f"{i}: {col}")

print(f"\nTotal rows: {len(df)}")

# Check if PC_OBRA_EXECUTADA exists
if 'PC_OBRA_EXECUTADA' in df.columns:
    print("\n✓ PC_OBRA_EXECUTADA found!")
    print(f"Sample values: {df['PC_OBRA_EXECUTADA'].head()}")
else:
    print("\n✗ PC_OBRA_EXECUTADA not found")
    # Look for similar columns
    exec_cols = [col for col in df.columns if 'EXEC' in col or 'PC_' in col or 'PERCENT' in col]
    print(f"Possible execution columns: {exec_cols}")

# Check for NU_APF
if 'NU_APF' in df.columns:
    print(f"\n✓ NU_APF found - can merge with cadastro")
else:
    print("\n✗ NU_APF not found - cannot merge")
