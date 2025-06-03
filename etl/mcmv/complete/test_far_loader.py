#!/usr/bin/env python3
"""
Test FAR loader
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from etl.mcmv.complete.far_loader import FARLoader

def test_far_loader():
    # Path to FAR data - adjust if needed
    far_path = "data/mcmv/HIS/FAR.xlsx"
    
    print("🚀 Testing FAR loader...")
    print(f"Looking for file at: {far_path}")
    
    if not Path(far_path).exists():
        print(f"❌ File not found at {far_path}")
        print("Please check the path to FAR.xlsx")
        return
        
    loader = FARLoader(far_path)
    data = loader.load_and_validate()
    
    if data and data['principal'] is not None:
        df = data['principal']
        print(f"\n✅ Successfully loaded FAR data")
        print(f"Total projects: {len(df)}")
        
        # Show sample data
        print("\nSample projects:")
        print(df[['NU_APF', 'NO_EMPREENDIMENTO', 'SG_UF', 'building_type_name']].head())
        
        # Show state distribution
        print("\nProjects by state:")
        print(df['SG_UF'].value_counts().head(10))
        
        # Show other loaded sheets
        print("\nOther sheets loaded:")
        for key, sheet_df in data.items():
            if key != 'principal' and sheet_df is not None:
                print(f"  {key}: {len(sheet_df)} rows")
    else:
        print("❌ Failed to load FAR data")

if __name__ == "__main__":
    test_far_loader()
