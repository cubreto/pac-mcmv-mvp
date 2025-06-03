#!/usr/bin/env python3
"""Test RURAL loader"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from etl.mcmv.complete.rural_loader import RURALLoader

def test_rural_loader():
    rural_path = "data/mcmv/HIS/RURAL.xlsx"
    
    print("🚀 Testing RURAL loader...")
    loader = RURALLoader(rural_path)
    data = loader.load_and_validate()
    
    if data and data['principal'] is not None:
        df = data['principal']
        print(f"\n✅ Successfully loaded RURAL data")
        print(f"Total projects: {len(df)}")
        print(f"\nProjects by state:")
        print(df['SG_UF'].value_counts().head(10))
        
        # Check if RURAL has PF data
        if data['pf'] is not None:
            print(f"\nRURAL also has PF data: {len(data['pf'])} beneficiaries")
    else:
        print("❌ Failed to load RURAL data")

if __name__ == "__main__":
    test_rural_loader()
