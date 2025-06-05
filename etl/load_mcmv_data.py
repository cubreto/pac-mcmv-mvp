#!/usr/bin/env python3
"""
Load MCMV HIS data using existing loaders but with REAL values
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from etl.mcmv.complete.unified_loader import UnifiedMCMVLoader
from etl.database import DatabaseManager
import pandas as pd
from datetime import date
from sqlalchemy import text

def load_mcmv_to_projeto_status():
    """Load MCMV data with real percentages and UH values"""
    
    print("Loading MCMV data from HIS files...")
    loader = UnifiedMCMVLoader("data/mcmv/HIS")
    df = loader.load_all()
    
    if df is None or len(df) == 0:
        print("No data loaded!")
        return
    
    print(f"Loaded {len(df)} MCMV projects")
    
    # Get the obra data for percentages
    all_obra_data = []
    for program, data in loader.all_data.items():
        if 'obra' in data and data['obra'] is not None:
            obra_df = data['obra'].copy()
            obra_df['program'] = program
            all_obra_data.append(obra_df)
    
    # Merge obra data to get PC_OBRA_REALIZADA
    if all_obra_data:
        obra_combined = pd.concat(all_obra_data, ignore_index=True)
        obra_latest = obra_combined.sort_values('DT_MOVIMENTO').groupby('NU_APF').last()
        df = df.merge(obra_latest[['PC_OBRA_REALIZADA']], left_on='NU_APF', right_index=True, how='left')
    
    # Extract real UH values based on program
    uh_mapping = {
        'FAR': 'NU_QT_UH',
        'FDS': 'NU_QT_UH_PROJETO',
        'RURAL': 'NU_QT_UH_CONSTRUCAO'
    }
    
    # Get UH values for each program
    df['uh_real'] = 0
    for program, uh_column in uh_mapping.items():
        mask = df['program_code'] == program
        if uh_column in df.columns:
            df.loc[mask, 'uh_real'] = df.loc[mask, uh_column]
        else:
            # Need to get from original cadastro sheet
            if program in loader.all_data:
                cadastro = loader.sheets.get('HISTB010_MONITORAMENTO_CADASTRO')
                if cadastro is not None and uh_column in cadastro.columns:
                    uh_lookup = cadastro.set_index('NU_APF')[uh_column].to_dict()
                    df.loc[mask, 'uh_real'] = df.loc[mask, 'NU_APF'].map(uh_lookup).fillna(0)
    
    # Calculate real investment based on actual UH
    uh_costs = {
        'FAR': 75000,
        'FDS': 75000,
        'RURAL': 50000
    }
    
    # Prepare data for database
    print("Preparing data for database...")
    df_db = pd.DataFrame({
        'proposta': df['NU_APF'].astype(str),
        'uf': df['SG_UF'],
        'municipio_beneficiado': df.get('NO_MUNICIPIO', df.get('NO_MUNICIPIO_IBGE', '')),
        'programa': df['program_code'],
        'tipo_programa': 'MCMV-HIS',
        'valor_repasse': 0,
        'valor_investimento': df.apply(lambda x: x['uh_real'] * uh_costs.get(x['program_code'], 50000), axis=1),
        'valor_empenhado': 0,
        'valor_pago': 0,
        'percentual_obra_realizado': df.get('PC_OBRA_REALIZADA', 0).fillna(0),
        'data_inicio_obra': None,
        'situacao_atual': 'Em execução - Dados HIS',
        'data_atualizacao_situacao': date.today(),
        'uh_estimadas': df['uh_real'].fillna(0).astype(int)
    })
    
    # Clean data
    df_db = df_db.dropna(subset=['proposta', 'programa', 'uf'])
    df_db = df_db[df_db['proposta'].notna() & df_db['programa'].notna() & df_db['uf'].notna()]
    
    # Connect to database
    print("Connecting to database...")
    db = DatabaseManager()
    
    # Insert data
    print(f"Inserting {len(df_db)} records into projeto_status...")
    
    try:
        with db.engine.begin() as conn:
            # Add uh_estimadas column if it doesn't exist
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'projeto_status' 
                AND column_name = 'uh_estimadas'
            """)).fetchone()
            
            if not result:
                print("Adding uh_estimadas column to projeto_status...")
                conn.execute(text("ALTER TABLE projeto_status ADD COLUMN uh_estimadas INTEGER DEFAULT 0"))
            
            # Delete existing MCMV data
            conn.execute(text("DELETE FROM projeto_status WHERE programa IN ('FAR', 'FDS', 'RURAL')"))
            
            # Insert new data
            df_db.to_sql('projeto_status', conn, if_exists='append', index=False)
        
        print("Data loaded successfully!")
        
        # Verify
        with db.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT programa, 
                       COUNT(*) as count,
                       SUM(uh_estimadas) as total_uh,
                       AVG(percentual_obra_realizado) as avg_pct
                FROM projeto_status 
                WHERE programa IN ('FAR', 'FDS', 'RURAL')
                GROUP BY programa
                ORDER BY programa
            """)).fetchall()
            
            print("\nSummary by program:")
            total_projects = 0
            total_uh = 0
            for programa, count, uh, avg_pct in result:
                print(f"  {programa}: {count} projects, {uh:,} UH, avg {avg_pct:.2f}% complete")
                total_projects += count
                total_uh += uh
            
            print(f"\nTotal: {total_projects} projects, {total_uh:,} UH")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    load_mcmv_to_projeto_status()
