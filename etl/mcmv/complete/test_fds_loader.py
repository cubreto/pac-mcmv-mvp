#!/usr/bin/env python3
"""Test FDS loader"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from etl.mcmv.complete.fds_loader import FDSLoader

def test_fds_loader():
    fds_path = "data/mcmv/HIS/FDS.xlsx"
    
    print("🚀 Testing FDS loader...")
    loader = FDSLoader(fds_path)
    data = loader.load_and_validate()
    
    if data and data['principal'] is not None:
        df = data['principal']
        print(f"\n✅ Successfully loaded FDS data")
        print(f"Total projects: {len(df)}")
        print(f"\nProjects by state:")
        print(df['SG_UF'].value_counts().head(10))
    else:
        print("❌ Failed to load FDS data")

if __name__ == "__main__":
    test_fds_loader()
