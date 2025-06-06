#!/usr/bin/env python3
"""
Load MCMV Beneficiary and Social Work data
Loads HISTB009_MONITORAMENTO_PF and HISTB013_EXEC_TS sheets
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
from etl.database import DatabaseManager
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_beneficiary_data():
    """Load beneficiary data from RURAL.xlsx"""
    db = DatabaseManager()
    
    try:
        # Load RURAL beneficiaries
        logger.info("Loading RURAL beneficiary data...")
        df_beneficiarios = pd.read_excel(
            'data/mcmv/HIS/RURAL.xlsx',
            sheet_name='HISTB009_MONITORAMENTO_PF'
        )
        
        # Create schema if not exists
        with db.engine.connect() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS mcmv_pf"))
            conn.commit()
        
        # Load to database
        df_beneficiarios.to_sql(
            'beneficiarios_rural',
            db.engine,
            schema='mcmv_pf',
            if_exists='replace',
            index=False
        )
        logger.info(f"Loaded {len(df_beneficiarios)} beneficiary records")
        
    except Exception as e:
        logger.error(f"Error loading beneficiaries: {e}")
        raise

def load_social_work_data():
    """Load social work data from FDS and RURAL"""
    db = DatabaseManager()
    
    try:
        dfs = []
        
        # Load FDS social work
        logger.info("Loading FDS social work data...")
        try:
            df_fds = pd.read_excel(
                'data/mcmv/HIS/FDS.xlsx',
                sheet_name='HISTB013_EXEC_TS'
            )
            df_fds['programa'] = 'FDS'
            dfs.append(df_fds)
            logger.info(f"Loaded {len(df_fds)} FDS social work records")
        except Exception as e:
            logger.warning(f"Could not load FDS social work: {e}")
        
        # Load RURAL social work
        logger.info("Loading RURAL social work data...")
        try:
            df_rural = pd.read_excel(
                'data/mcmv/HIS/RURAL.xlsx',
                sheet_name='HISTB013_EXEC_TS'
            )
            df_rural['programa'] = 'RURAL'
            dfs.append(df_rural)
            logger.info(f"Loaded {len(df_rural)} RURAL social work records")
        except Exception as e:
            logger.warning(f"Could not load RURAL social work: {e}")
        
        if dfs:
            # Combine all social work data
            df_combined = pd.concat(dfs, ignore_index=True)
            
            # Load to database
            df_combined.to_sql(
                'trabalho_social',
                db.engine,
                schema='mcmv_pf',
                if_exists='replace',
                index=False
            )
            logger.info(f"Loaded {len(df_combined)} total social work records")
        else:
            logger.warning("No social work data loaded")
            
    except Exception as e:
        logger.error(f"Error loading social work: {e}")
        raise

def main():
    """Main function"""
    logger.info("Starting beneficiary and social work data load...")
    
    # Load beneficiary data
    load_beneficiary_data()
    
    # Load social work data
    load_social_work_data()
    
    logger.info("✅ Beneficiary and social work data load complete!")

if __name__ == "__main__":
    main()
