#!/usr/bin/env python3
"""
Main ETL script for PAC-MCMV MVP
Loads Excel data + generates fake Habitação data, saves to database
"""

import sys
import os
from pathlib import Path
import pandas as pd
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from database import DatabaseManager
from excel_loader import process_excel_files
from fake_data_generator import generate_habitacao_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_etl():
    """Main ETL process"""
    
    logger.info("🚀 Starting PAC-MCMV ETL process...")
    
    # Initialize database
    db = DatabaseManager()
    
    if not db.test_connection():
        logger.error("❌ Database connection failed")
        return False
    
    all_data = []
    
    # Try to load real PAC data from Excel
    try:
        logger.info("📊 Loading PAC data from Excel files...")
        pac_df = process_excel_files("../data")  # Look in data folder
        logger.info(f"✅ Loaded {len(pac_df)} PAC records from Excel")
        all_data.append(pac_df)
    except Exception as e:
        logger.warning(f"⚠️ Could not load Excel data: {e}")
        logger.info("📊 Generating fake PAC data instead...")
        from fake_data_generator import generate_pac_data
        pac_df = generate_pac_data(400)
        logger.info(f"✅ Generated {len(pac_df)} fake PAC records")
        all_data.append(pac_df)
    
    # Generate fake Habitação data (placeholder until real data arrives)
    logger.info("🏠 Generating fake Habitação data...")
    habitacao_df = generate_habitacao_data(250) 
    logger.info(f"✅ Generated {len(habitacao_df)} fake Habitação records")
    all_data.append(habitacao_df)
    
    # Combine all data
    combined_df = pd.concat(all_data, ignore_index=True)
    logger.info(f"📋 Combined dataset: {len(combined_df)} total records")
    
    # Save to database
    logger.info("💾 Saving to database...")
    try:
        db.save_dataframe(combined_df, 'projeto_status', if_exists='replace')
        logger.info("✅ Data saved successfully")
        
        # Verify data
        count = db.get_projeto_count()
        logger.info(f"📊 Database now contains {count} projects")
        
        # Show summary by program type
        summary = db.load_dataframe("""
            SELECT tipo_programa, COUNT(*) as count 
            FROM projeto_status 
            GROUP BY tipo_programa
        """)
        
        logger.info("📈 Data summary:")
        for _, row in summary.iterrows():
            logger.info(f"   {row['tipo_programa']}: {row['count']} projects")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database save failed: {e}")
        return False

if __name__ == "__main__":
    success = run_etl()
    if success:
        print("\n🎉 ETL completed successfully!")
        print("You can now run the Streamlit dashboard:")
        print("   streamlit run streamlit_app/dashboard.py")
    else:
        print("\n💥 ETL failed - check the logs above")
        sys.exit(1)
