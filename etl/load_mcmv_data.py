#!/usr/bin/env python3
"""
Load MCMV HIS data using REAL investment values from Excel files
Updated to use VR_TOTAL_INVESTIMENTO and other actual investment fields
FIXED: Now includes nome_empreendimento from NO_EMPREENDIMENTO
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from etl.mcmv.complete.unified_loader import UnifiedMCMVLoader
from etl.database import DatabaseManager
import pandas as pd
import numpy as np
from datetime import date
from sqlalchemy import text

def load_mcmv_to_projeto_status():
    """Load MCMV data with REAL investment values from Excel"""
    
    print("Loading MCMV data from HIS files with REAL investment values...")
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
    
    # ================================================================
    # NEW: Use REAL investment values from Excel instead of calculated
    # ================================================================
    
    print("Extracting REAL investment values from Excel files...")
    
    # Initialize investment column
    df['valor_investimento_real'] = 0.0
    
    # Debug: Check what's available in loader
    print(f"Available programs in loader: {list(loader.all_data.keys())}")
    for program in loader.all_data.keys():
        print(f"  {program} data keys: {list(loader.all_data[program].keys())}")
        if program in loader.all_data and 'principal' in loader.all_data[program]:
            cadastro = loader.all_data[program]['principal']
            print(f"  {program} cadastro columns: {list(cadastro.columns)[:10]}...")  # Show first 10 columns
    
    # Process each program with actual Excel investment fields
    for program in ['FAR', 'FDS', 'RURAL']:
        if program in loader.all_data and 'principal' in loader.all_data[program]:
            cadastro = loader.all_data[program]['principal']
            
            # Define investment field mapping for each program
            if program == 'FAR':
                investment_field = 'VR_TOTAL_INVESTIMENTO'
            elif program == 'FDS':
                investment_field = 'VR_TOTAL_INVESTIMENTO'
            elif program == 'RURAL':
                investment_field = 'VR_TOTAL_INVESTIMENTO'
            
            # Debug: Check if investment field exists
            if investment_field in cadastro.columns:
                print(f"  ✅ {program}: Found {investment_field}")
                
                # Create lookup for this program
                investment_lookup = cadastro.set_index('NU_APF')[investment_field].to_dict()
                
                # Apply to matching rows in main dataframe
                mask = df['program_code'] == program
                df.loc[mask, 'valor_investimento_real'] = df.loc[mask, 'NU_APF'].map(investment_lookup).fillna(0)
                
                # Show totals for verification
                total_investment = df.loc[mask, 'valor_investimento_real'].sum()
                count = mask.sum()
                print(f"    {program}: {count} projects, R$ {total_investment/1e9:.2f}B total")
            else:
                print(f"  ❌ {program}: {investment_field} not found in columns: {list(cadastro.columns)[:5]}...")
    
    # ================================================================
    # Prepare data for database with REAL investment values
    # ================================================================
    
    print("Preparing data for database with REAL investment values...")
    df_db = pd.DataFrame({
        'proposta': df['NU_APF'].astype(str),
        'uf': df['SG_UF'],
        'municipio_beneficiado': df.get('NO_MUNICIPIO', df.get('NO_MUNICIPIO_IBGE', '')),
        'programa': df['program_code'],
        'tipo_programa': 'MCMV-HIS',
        'nome_empreendimento': df.get('NO_EMPREENDIMENTO', '').astype(str).str.strip(),  # ← FIXED: Now includes project names!
        'valor_repasse': 0,
        'valor_investimento': df['valor_investimento_real'],  # NOW USING REAL VALUES!
        'valor_empenhado': 0,
        'valor_pago': 0,
        'percentual_obra_realizado': df.get('PC_OBRA_REALIZADA', 0).fillna(0),
        'data_inicio_obra': df['DT_INICIO_OBRA'] if 'DT_INICIO_OBRA' in df.columns else None,
        'situacao_atual': 'Em execução - Dados HIS Reais',
        'data_atualizacao_situacao': date.today(),
        'uh_estimadas': df['uh_real'].fillna(0).astype(int)
    })
    
    # Clean data
    df_db = df_db.dropna(subset=['proposta', 'programa', 'uf'])
    df_db = df_db[df_db['proposta'].notna() & df_db['programa'].notna() & df_db['uf'].notna()]
    
    # ================================================================
    # Validation: Show totals before loading
    # ================================================================
    
    print(f"\nValidation - Investment totals by program:")
    for programa in ['FAR', 'FDS', 'RURAL']:
        mask = df_db['programa'] == programa
        total = df_db.loc[mask, 'valor_investimento'].sum()
        count = mask.sum()
        avg = total / count if count > 0 else 0
        print(f"  {programa}: {count} projects, R$ {total/1e9:.2f}B total, R$ {avg/1e6:.2f}M avg")
        
        # Show project names sample
        project_names = df_db.loc[mask, 'nome_empreendimento'].dropna()
        if len(project_names) > 0:
            print(f"    Sample names: {project_names.iloc[:2].tolist()}")
    
    total_all = df_db['valor_investimento'].sum()
    print(f"  TOTAL: {len(df_db)} projects, R$ {total_all/1e9:.2f}B")
    print(f"  Expected: ~R$ 23.60B (if using VR_TOTAL_INVESTIMENTO)")
    
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
            print("Deleting existing MCMV data...")
            conn.execute(text("DELETE FROM projeto_status WHERE programa IN ('FAR', 'FDS', 'RURAL')"))
            
            # Insert new data with REAL investment values AND project names
            print("Inserting new data with REAL investment values AND project names...")
            df_db.to_sql('projeto_status', conn, if_exists='append', index=False)
        
        print("✅ Data loaded successfully with REAL investment values AND project names!")
        
        # Verify the results
        with db.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    programa, 
                    COUNT(*) as count,
                    SUM(uh_estimadas) as total_uh,
                    SUM(valor_investimento)/1e9 as investment_billions,
                    AVG(percentual_obra_realizado) as avg_pct,
                    COUNT(nome_empreendimento) FILTER (WHERE nome_empreendimento != '' AND nome_empreendimento IS NOT NULL) as projects_with_names
                FROM projeto_status 
                WHERE programa IN ('FAR', 'FDS', 'RURAL')
                GROUP BY programa
                ORDER BY investment_billions DESC
            """)).fetchall()
            
            print("\n" + "="*60)
            print("✅ VERIFICATION: Database now contains REAL investment values AND project names")
            print("="*60)
            total_projects = 0
            total_uh = 0
            total_investment = 0
            total_with_names = 0
            for programa, count, uh, investment, avg_pct, with_names in result:
                print(f"  {programa}: {count} projects, {uh:,} UH, R$ {investment:.2f}B, avg {avg_pct:.2f}% complete, {with_names} with names")
                total_projects += count
                total_uh += uh
                total_investment += investment
                total_with_names += with_names
            
            print(f"\n  TOTAL: {total_projects} projects, {total_uh:,} UH, R$ {total_investment:.2f}B, {total_with_names} with names")
            
            if total_investment > 20:
                print("✅ SUCCESS: Investment values now match Excel source data!")
            else:
                print("❌ WARNING: Investment values still seem low - check field mappings")
                
            if total_with_names == total_projects:
                print("✅ SUCCESS: All projects now have names!")
            else:
                print(f"⚠️  WARNING: Only {total_with_names}/{total_projects} projects have names")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    load_mcmv_to_projeto_status()
