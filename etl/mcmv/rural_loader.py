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
            self.prioritarios_df = sheets.get('DADOS_PRIORITÁRIOS_RURAL')
            
            logger.info(f"Loaded Rural data:")
            logger.info(f"  - Cadastro: {len(self.cadastro_df)} records")
            logger.info(f"  - PF: {len(self.pf_df)} records")
            logger.info(f"  - TS: {len(self.ts_df)} records")
            logger.info(f"  - Prioritários: {len(self.prioritarios_df)} records")
            
            return True
        except Exception as e:
            logger.error(f"Error loading Rural data: {e}")
            return False
            
    def transform_cadastro(self):
        """Transform cadastro data to database schema"""
        if self.cadastro_df is None:
            return None
            
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
            'IC_SITUACAO_OBRA': 'situacao_obra',
            'PC_OBRA_EXECUTADA': 'percentual_obra_executada'
        }
        
        # Select available columns
        available_cols = [col for col in column_mapping.keys() if col in self.cadastro_df.columns]
        df = self.cadastro_df[available_cols].copy()
        df = df.rename(columns={k: column_mapping[k] for k in available_cols})
        
        # Add program type
        df['tipo_programa'] = 'RURAL'
        df['fonte'] = 'MCMV_RURAL'
        
        # Clean data
        numeric_fields = ['qt_uh_construcao', 'qt_uh_projeto', 'valor_obra', 
                         'valor_projeto', 'valor_total_investimento', 'percentual_obra_executada']
        df = self.clean_numeric_fields(df, numeric_fields)
        
        date_fields = ['data_inicio_obra']
        df = self.clean_date_fields(df, date_fields)
        
        text_fields = ['nome_empreendimento', 'municipio', 'situacao_obra']
        df = self.clean_text_fields(df, text_fields)
        
        df = self.validate_uf(df)
        
        logger.info(f"Transformed {len(df)} cadastro records")
        return df
        
    def transform_beneficiarios(self):
        """Transform beneficiarios (PF) data"""
        if self.pf_df is None:
            return None
            
        # Column mapping for PF
        column_mapping = {
            'NU_APF': 'nu_apf',
            'NU_CPF_CNPJ_MUTUARIO': 'cpf_beneficiario',
            'NO_MUTUARIO': 'nome_beneficiario',
            'VR_EVENTO': 'valor_financiamento',
            'VR_TAXA_ABERTURA_CREDITO': 'taxa_abertura_credito',
            'DT_NASCIMENTO': 'data_nascimento',
            'SG_SEXO': 'sexo'
        }
        
        # Select available columns
        available_cols = [col for col in column_mapping.keys() if col in self.pf_df.columns]
        df = self.pf_df[available_cols].copy()
        df = df.rename(columns={k: column_mapping[k] for k in available_cols})
        
        # Clean data
        numeric_fields = ['valor_financiamento', 'taxa_abertura_credito']
        df = self.clean_numeric_fields(df, numeric_fields)
        
        date_fields = ['data_nascimento']
        df = self.clean_date_fields(df, date_fields)
        
        text_fields = ['nome_beneficiario', 'sexo']
        df = self.clean_text_fields(df, text_fields)
        
        logger.info(f"Transformed {len(df)} beneficiario records")
        return df
        
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
            logger.info(f"Rural totals: {total_uh} UH, R$ {total_investment:,.2f}")
            
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
        print(f"   - Cadastro: {len(data['cadastro'])} projects")
        print(f"   - Beneficiários: {len(data['beneficiarios'])} beneficiaries")
