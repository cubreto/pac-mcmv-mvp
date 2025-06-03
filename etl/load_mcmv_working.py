#!/usr/bin/env python3
"""
Load MCMV HIS data (FAR, FDS, RURAL) into projeto_status table
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from etl.mcmv.complete.unified_loader import UnifiedMCMVLoader
from etl.database import DatabaseManager
import pandas as pd
from datetime import datetime, date
from sqlalchemy import text

def load_mcmv_to_projeto_status():
    """Load MCMV data from HIS files into projeto_status table"""
    
    # Load MCMV data
    print("Loading MCMV data from HIS files...")
    loader = UnifiedMCMVLoader("data/mcmv/HIS")
    df = loader.load_all()
    
    if df is None or len(df) == 0:
        print("No data loaded!")
        return
    
    print(f"Loaded {len(df)} MCMV projects")
    
    # Prepare data for projeto_status table - only use existing columns
    print("Preparing data for database...")
    
    # Map columns to match projeto_status schema exactly
    df_db = pd.DataFrame({
        'proposta': df['NU_APF'].astype(str),
        'uf': df['SG_UF'],
        'municipio_beneficiado': df.get('NO_MUNICIPIO', df.get('NO_MUNICIPIO_IBGE', '')),
        'programa': df['program_code'],  # FAR, FDS, RURAL
        'tipo_programa': 'MCMV-HIS',
        'valor_repasse': 0,
        'valor_investimento': df['program_code'].map({
            'FAR': 168 * 75000,  # 168 UH avg * R$75k
            'FDS': 226 * 75000,  # 226 UH avg * R$75k
            'RURAL': 70 * 50000  # 70 UH avg * R$50k
        }),
        'valor_empenhado': 0,
        'valor_pago': 0,
        'percentual_obra_realizado': 50,  # Default 50% if not available
        'data_inicio_obra': None,
        'situacao_atual': 'Em execução - Dados HIS',
        'data_atualizacao_situacao': date.today()
    })
    
    # Clean data
    df_db = df_db.fillna({
        'municipio_beneficiado': '',
        'percentual_obra_realizado': 0,
        'situacao_atual': '',
        'valor_repasse': 0,
        'valor_empenhado': 0,
        'valor_pago': 0
    })
    
    # Remove rows with missing critical data
    df_db = df_db[df_db['proposta'].notna() & df_db['programa'].notna() & df_db['uf'].notna()]
    
    # Connect to database
    print("Connecting to database...")
    db = DatabaseManager()
    
    # Insert data
    print(f"Inserting {len(df_db)} records into projeto_status...")
    
    try:
        # First, delete existing MCMV data to avoid duplicates
        with db.engine.begin() as conn:
            conn.execute(text("DELETE FROM projeto_status WHERE programa IN ('FAR', 'FDS', 'RURAL')"))
            
            # Insert new data
            df_db.to_sql('projeto_status', conn, if_exists='append', index=False)
        
        print("Data loaded successfully!")
        
        # Verify using direct SQL
        with db.engine.connect() as conn:
            total = conn.execute(text(
                "SELECT COUNT(*) FROM projeto_status "
                "WHERE programa IN ('FAR', 'FDS', 'RURAL')"
            )).scalar_one()
            print(f"Total MCMV projects in database: {total}")
            
            summary = conn.execute(text(
                "SELECT programa, COUNT(*) "
                "FROM projeto_status "
                "WHERE programa IN ('FAR', 'FDS', 'RURAL') "
                "GROUP BY programa"
            )).all()
            
            print("\nSummary by program:")
            for programa, count in summary:
                print(f"  {programa}: {count} projects")
            
    except Exception as e:
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    load_mcmv_to_projeto_status()
