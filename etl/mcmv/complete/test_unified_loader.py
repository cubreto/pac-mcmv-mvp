#!/usr/bin/env python3
"""
Test Unified MCMV loader
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from etl.mcmv.complete.unified_loader import UnifiedMCMVLoader

def test_unified_loader():
    base_folder = "data/mcmv/HIS"
    
    print("🚀 Testing Unified MCMV loader...")
    loader = UnifiedMCMVLoader(base_folder)
    master_df = loader.load_all()
    
    if master_df is not None and len(master_df) > 0:
        print(f"\n✅ Master DataFrame loaded with {len(master_df)} total rows")
        
        print("\nPrograms breakdown:")
        print(master_df['program_code'].value_counts())
        
        print("\nTop 10 states:")
        print(master_df['SG_UF'].value_counts().head(10))
        
        print("\nSample rows:")
        print(master_df[['NU_APF', 'program_code', 'NO_EMPREENDIMENTO', 'SG_UF']].head())
        
        # Get summary
        summary = loader.get_summary()
        print(f"\nExpected vs Actual:")
        print(f"FAR: {summary['by_program'].get('FAR', 0)} actual / {summary['total_expected_units']['FAR']} expected")
        print(f"FDS: {summary['by_program'].get('FDS', 0)} actual / {summary['total_expected_units']['FDS']} expected")
        print(f"RURAL: {summary['by_program'].get('RURAL', 0)} actual / {summary['total_expected_units']['RURAL']} expected")
        
        print(f"\n⚠️  Note: These are SAMPLE files, not complete datasets!")
        print(f"Total in samples: {len(master_df)} projects")
        print(f"Total expected: 188,775 housing units")
        
    else:
        print("❌ Failed to load any principal tables")

if __name__ == "__main__":
    test_unified_loader()
