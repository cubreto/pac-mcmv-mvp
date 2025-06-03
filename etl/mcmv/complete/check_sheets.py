#!/usr/bin/env python3
"""Check sheet names in all HIS files"""
import pandas as pd

files = {
    'FAR': 'data/mcmv/HIS/FAR.xlsx',
    'FDS': 'data/mcmv/HIS/FDS.xlsx', 
    'RURAL': 'data/mcmv/HIS/RURAL.xlsx'
}

for program, path in files.items():
    print(f"\n📋 {program} sheets:")
    try:
        excel = pd.ExcelFile(path)
        for sheet in excel.sheet_names:
            df = pd.read_excel(excel, sheet_name=sheet)
            print(f"  - {sheet}: {len(df)} rows, {len(df.columns)} columns")
    except Exception as e:
        print(f"  Error: {e}")
