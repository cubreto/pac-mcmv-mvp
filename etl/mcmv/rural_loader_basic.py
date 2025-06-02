#!/usr/bin/env python3
"""
Rural MCMV data loader
Processes DADOS_RURAL.xlsx with multiple sheets
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from .base_loader import MCMVBaseLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RuralLoader(MCMVBaseLoader):
    """Loader for Rural MCMV data"""
    
    def load_data(self):
        """Load Rural data from Excel file"""
        try:
            # Load all sheets
            sheets = pd.read_excel(self.file_path, sheet_name=None)
            logger.info(f"Found sheets: {list(sheets.keys())}")
            
            self.cadastro_df = sheets.get('MONITORAMENTO_CADASTRO')
            self.pf_df = sheets.get('MONITORAMENTO_PF')
            self.ts_df = sheets.get('EXEC_TS')
            self.prioritarios_df = sheets.get('DADOS_PRIORITÁRIOS_RURAL') or sheets.get('DADOS_PRORITÁRIOS_RURAL')
            
            logger.info(f"Loaded Rural data:")
            logger.info(f"  - Cadastro: {len(self.cadastro_df) if self.cadastro_df is not None else 0} records")
            logger.info(f"  - PF: {len(self.pf_df) if self.pf_df is not None else 0} records")
            logger.info(f"  - TS: {len(self.ts_df) if self.ts_df is not None else 0} records")
            logger.info(f"  - Prioritários: {len(self.prioritarios_df) if self.prioritarios_df is not None else 0} records")
            
            return True
        except Exception as e:
            logger.error(f"Error loading Rural data: {e}")
            return False
            
    def transform_cadastro(self):
        """Transform cadastro data to database schema"""
        if self.cadastro_df is None:
            return None
            
        df = self.cadastro_df.copy()
        
        # Column mapping for cadastro
        column_mapping = {
            'NU_APF': 'nu_apf',
            'NO_EMPREENDIMENTO': 'nome_empreendimento',
            'SG_UF': 'uf',
            'NO_MUNICIPIO': 'municipio',
            'CO_MUNICIPIO_IBGE': 'codigo_ibge',
            'NU_QT_UH_CONSTRUCAO': 'qt_uh_construcao',
            'NU_QT_UH_PROJETO': 'qt_uh_projeto',
            'VR_MODALIDADE_OBRA': 'valor_obra',
            'VR_MODALIDADE_PROJETO': 'valor_projeto',
            'VR_TOTAL_INVESTIMENTO': 'valor_total_investimento',
            'DT_INICIO_OBRA': 'data_inicio_obra',
            'DT_CONTRATACAO': 'data_contratacao',
            'NO_EO': 'entidade_organizadora',
            'NU_CNPJ_EO': 'cnpj_eo',
            'NO_CONSTRUTORA': 'construtora',
            'NU_CNPJ_CONSTRUTORA': 'cnpj_construtora'
        }
        
        # Select available columns
        available_cols = [col for col in column_mapping.keys() if col in df.columns]
        df_transformed = df[available_cols].copy()
        df_transformed = df_transformed.rename(columns={k: column_mapping[k] for k in available_cols})
        
        # Add program type
        df_transformed['tipo_programa'] = 'MCMV'
        df_transformed['modalidade'] = 'RURAL'
        df_transformed['fonte'] = 'MCMV_RURAL'
        
        # Clean data
        numeric_fields = ['qt_uh_construcao', 'qt_uh_projeto', 'valor_obra', 
                         'valor_projeto', 'valor_total_investimento']
        df_transformed = self.clean_numeric_fields(df_transformed, [f for f in numeric_fields if f in df_transformed.columns])
        
        date_fields = ['data_inicio_obra', 'data_contratacao']
        df_transformed = self.clean_date_fields(df_transformed, [f for f in date_fields if f in df_transformed.columns])
        
        text_fields = ['nome_empreendimento', 'municipio', 'entidade_organizadora', 'construtora']
        df_transformed = self.clean_text_fields(df_transformed, [f for f in text_fields if f in df_transformed.columns])
        
        df_transformed = self.validate_uf(df_transformed)
        
        # Add default status based on data_inicio_obra
        df_transformed['situacao_obra'] = df_transformed.apply(
            lambda row: 'Em execução' if pd.notna(row.get('data_inicio_obra')) else 'Não iniciada',
            axis=1
        )
        
        logger.info(f"Transformed {len(df_transformed)} cadastro records")
        return df_transformed
        
    def transform_beneficiarios(self):
        """Transform beneficiarios (PF) data"""
        if self.pf_df is None:
            return None
            
        # For now, just count beneficiaries per APF
        beneficiary_count = self.pf_df.groupby('NU_APF').size().reset_index(name='num_beneficiarios')
        logger.info(f"Counted beneficiaries for {len(beneficiary_count)} projects")
        return beneficiary_count
        
    def transform_data(self):
        """Transform all Rural data"""
        results = {
            'cadastro': self.transform_cadastro(),
            'beneficiarios': self.transform_beneficiarios()
        }
        
        # Add summary statistics
        if results['cadastro'] is not None:
            total_uh = results['cadastro']['qt_uh_construcao'].sum()
            total_investment = results['cadastro']['valor_total_investimento'].sum()
            logger.info(f"Rural totals: {total_uh:,.0f} UH, R$ {total_investment:,.2f}")
            
        return results

def load_rural_data(file_path="data/mcmv/DADOS_RURAL.xlsx"):
    """Main function to load Rural data"""
    loader = RuralLoader(file_path)
    
    if loader.load_data():
        return loader.transform_data()
    else:
        return None

if __name__ == "__main__":
    data = load_rural_data()
    if data:
        print(f"✅ Loaded Rural data successfully")
        if data['cadastro'] is not None:
            print(f"   - Cadastro: {len(data['cadastro'])} projects")
        if data['beneficiarios'] is not None:
            print(f"   - Beneficiários: {len(data['beneficiarios'])} beneficiary counts")
