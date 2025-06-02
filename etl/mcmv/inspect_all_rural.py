#!/usr/bin/env python3
"""Inspect all Rural MCMV sheets"""

import pandas as pd

# Load all sheets
excel_file = pd.ExcelFile("data/mcmv/DADOS_RURAL.xlsx")

for sheet_name in excel_file.sheet_names:
    print(f"\n{'='*60}")
    print(f"SHEET: {sheet_name}")
    print('='*60)
    
    df = pd.read_excel(excel_file, sheet_name=sheet_name)
    print(f"Rows: {len(df)}, Columns: {len(df.columns)}")
    
    if sheet_name == "EXEC_TS":
        print("\nColumns:")
        for i, col in enumerate(df.columns):
            print(f"{i}: {col}")
        print("\nSample data:")
        print(df[['NU_APF', 'PC_OBRA_EXECUTADA'] if 'PC_OBRA_EXECUTADA' in df.columns else df.columns[:5]].head())
    
    elif sheet_name == "MONITORAMENTO_PF":
        print("\nKey columns:")
        for col in df.columns:
            if any(keyword in col for keyword in ['CPF', 'MUTUARIO', 'VR_', 'DT_', 'SEXO']):
                print(f"  - {col}")
                
print("\n✅ Inspection complete!")
