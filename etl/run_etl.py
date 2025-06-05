#!/usr/bin/env python3
"""
PAC-MCMV ETL Process - PRODUCTION VERSION (NO FAKE DATA)
Fixed to remove fake data generation for client presentation
"""

import pandas as pd
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from database import DatabaseManager
from excel_loader import process_excel_files
# REMOVED: from fake_data_generator import generate_habitacao_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_etl():
    """Main ETL process - PRODUCTION VERSION (Real MCMV data only)"""
    
    logger.info("🚀 Starting PAC-MCMV ETL process (PRODUCTION - No fake data)...")
    
    # Initialize database
    db = DatabaseManager()
    
    all_data = []
    
    # Try to load real PAC data from Excel
    try:
        logger.info("📊 Loading PAC data from Excel files...")
        pac_df = process_excel_files("../data")  # Look in data folder
        logger.info(f"✅ Loaded {len(pac_df)} PAC records from Excel")
        all_data.append(pac_df)
    except Exception as e:
        logger.warning(f"⚠️ Could not load Excel data: {e}")
        logger.info("⚠️ PRODUCTION MODE: No fake PAC data will be generated")
        # REMOVED: Fake PAC data generation
    
    # REMOVED: Fake Habitação data generation
    logger.info("🏠 PRODUCTION MODE: Using only real MCMV data from HIS files")
    logger.info("📋 Fake Habitação data generation DISABLED for client presentation")
    
    # Load real MCMV data using the proper loader
    try:
        logger.info("📊 Loading real MCMV data from HIS files...")
        # Use the MCMV loader that processes FAR, FDS, RURAL
        from load_mcmv_final import load_mcmv_to_projeto_status
        load_mcmv_to_projeto_status()
        logger.info("✅ Real MCMV data loaded successfully")
    except Exception as e:
        logger.error(f"❌ Failed to load real MCMV data: {e}")
        raise
    
    # Combine and save only real data
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        logger.info(f"💾 Saving {len(combined_df)} total records (REAL DATA ONLY)")
        
        try:
            db.save_dataframe(combined_df, 'projeto_status', if_exists='append')
            logger.info("✅ Real data saved successfully")
        except Exception as e:
            logger.error(f"❌ Error saving data: {e}")
            raise
    else:
        logger.info("📊 Only MCMV data loaded (no PAC Excel data found)")
    
    logger.info("🎯 ETL Complete - PRODUCTION READY (Real data only)")

if __name__ == "__main__":
    run_etl()
