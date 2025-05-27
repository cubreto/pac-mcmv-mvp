#!/usr/bin/env python3
"""
Excel data loader for real PAC data
Transforms Excel format to database schema
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_pac_excel(file_path):
    """Load PAC data from Excel file"""
    
    # Try different sheet names
    sheet_names = ["Analítico Proposta", "Sheet1", "Dados", "PAC"]
    
    df = None
    for sheet in sheet_names:
        try:
            df = pd.read_excel(file_path, sheet_name=sheet)
            logger.info(f"Successfully loaded sheet: {sheet}")
            break
        except:
            continue
    
    if df is None:
        df = pd.read_excel(file_path)  # Load first sheet
        logger.info("Loaded first sheet by default")
    
    return df

def transform_pac_data(df):
    """Transform Excel PAC data to database schema"""
    
    # Column mapping from Excel to database schema
    column_mapping = {
        'Proposta': 'proposta',
        'UF': 'uf', 
        'Município Beneficiado': 'municipio_beneficiado',
        'Programa': 'programa',
        'Valor Repasse': 'valor_repasse',
        'Valor Investimento': 'valor_investimento', 
        'Valor Empenhado': 'valor_empenhado',
        'Valor Pago C.Convênio': 'valor_pago',
        'Percentual de obra realizado': 'percentual_obra_realizado',
        'Data início de Obra': 'data_inicio_obra',
        'Situação Atual': 'situacao_atual',
        'Data atualização da Situação Atual': 'data_atualizacao_situacao'
    }
    
    # Find available columns (case-insensitive)
    available_mapping = {}
    df_columns_lower = {col.lower(): col for col in df.columns}
    
    for excel_col, db_col in column_mapping.items():
        excel_col_lower = excel_col.lower()
        if excel_col_lower in df_columns_lower:
            available_mapping[df_columns_lower[excel_col_lower]] = db_col
        elif excel_col in df.columns:
            available_mapping[excel_col] = db_col
    
    logger.info(f"Found {len(available_mapping)} matching columns")
    
    # Select and rename columns
    df_transformed = df[list(available_mapping.keys())].copy()
    df_transformed = df_transformed.rename(columns=available_mapping)
    
    # Add required fields
    df_transformed['tipo_programa'] = 'PAC'
    
    # Clean data
    df_transformed = clean_transformed_data(df_transformed)
    
    logger.info(f"Transformed {len(df_transformed)} PAC records")
    return df_transformed

def clean_transformed_data(df):
    """Clean and validate transformed data"""
    
    # Remove rows without situacao_atual
    df = df.dropna(subset=['situacao_atual'])
    df = df[df['situacao_atual'].astype(str).str.strip() != '']
    
    # Clean numeric fields
    numeric_fields = ['valor_repasse', 'valor_investimento', 'valor_empenhado', 
                     'valor_pago', 'percentual_obra_realizado']
    
    for field in numeric_fields:
        if field in df.columns:
            df[field] = pd.to_numeric(df[field], errors='coerce')
    
    # Clean date fields
    date_fields = ['data_inicio_obra', 'data_atualizacao_situacao']
    
    for field in date_fields:
        if field in df.columns:
            df[field] = pd.to_datetime(df[field], errors='coerce')
    
    # Clean text fields
    text_fields = ['proposta', 'uf', 'municipio_beneficiado', 'programa', 'situacao_atual']
    
    for field in text_fields:
        if field in df.columns:
            df[field] = df[field].astype(str).str.strip()
    
    # Validate UF format
    if 'uf' in df.columns:
        df['uf'] = df['uf'].str.upper()
        valid_ufs = {
            'AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 
            'MA', 'MG', 'MS', 'MT', 'PA', 'PB', 'PE', 'PI', 'PR', 
            'RJ', 'RN', 'RO', 'RR', 'RS', 'SC', 'SE', 'SP', 'TO'
        }
        df = df[df['uf'].isin(valid_ufs)]
    
    # Ensure required fields are present
    required_fields = ['uf', 'situacao_atual', 'tipo_programa']
    missing_fields = [field for field in required_fields if field not in df.columns]
    
    if missing_fields:
        raise ValueError(f"Missing required fields: {missing_fields}")
    
    logger.info(f"Cleaned data: {len(df)} valid records")
    return df

def process_excel_files(data_dir="data"):
    """Process all Excel files in data directory"""
    
    data_path = Path(data_dir)
    excel_files = list(data_path.glob("*.xlsx")) + list(data_path.glob("*.xls"))
    
    if not excel_files:
        raise FileNotFoundError(f"No Excel files found in {data_dir}")
    
    all_dataframes = []
    
    for file_path in excel_files:
        logger.info(f"Processing {file_path}")
        try:
            df = load_pac_excel(file_path)
            df_transformed = transform_pac_data(df)
            all_dataframes.append(df_transformed)
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            continue
    
    if not all_dataframes:
        raise ValueError("No valid data could be loaded from Excel files")
    
    # Combine all dataframes
    combined_df = pd.concat(all_dataframes, ignore_index=True)
    logger.info(f"Combined {len(combined_df)} total records from {len(all_dataframes)} files")
    
    return combined_df

if __name__ == "__main__":
    try:
        df = process_excel_files()
        print(f"✅ Loaded {len(df)} records")
        print("Sample data:")
        print(df[['proposta', 'uf', 'programa', 'situacao_atual']].head())
    except Exception as e:
        print(f"❌ Error: {e}")
