"""
ETL Script to load REUNI Excel data into PostgreSQL
Based on analysis of 4,899 records with 78 columns
"""
import pandas as pd
import numpy as np
from datetime import datetime
import logging
from sqlalchemy import create_engine
import os
from decimal import Decimal

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ReuniETL:
    def __init__(self, excel_path, db_url=None):
        self.excel_path = excel_path
        self.db_url = db_url or os.getenv('DATABASE_URL')
        self.engine = None
        
    def connect_db(self):
        """Create database connection"""
        try:
            self.engine = create_engine(self.db_url)
            logger.info("✅ Connected to database")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    def load_excel(self):
        """Load and validate Excel file"""
        try:
            logger.info(f"📂 Loading Excel file: {self.excel_path}")
            df = pd.read_excel(self.excel_path)
            logger.info(f"✅ Loaded {len(df)} records with {len(df.columns)} columns")
            return df
        except Exception as e:
            logger.error(f"❌ Failed to load Excel: {e}")
            return None
    
    def clean_column_names(self, df):
        """Standardize column names for PostgreSQL"""
        column_mapping = {
            'Proposta': 'proposta',
            'Operação': 'operacao',
            'DV': 'dv',
            'Instrumento': 'instrumento',
            'Recebedor': 'recebedor',
            'Ente de vinculação': 'ente_vinculacao',
            'UF': 'uf',
            'Município Beneficiado': 'municipio_beneficiado',
            'GIGOV/REGOV': 'gigov_regov',
            'GIGOV de Vinculação': 'gigov_vinculacao',
            'Repassador': 'repassador',
            'Programa': 'programa',
            'Objetivo': 'objetivo',
            'Latitude': 'latitude',
            'Longitude': 'longitude',
            'Tipo': 'tipo',
            'Tipologia': 'tipologia',
            'Situação do Termo de Compromisso': 'situacao_termo_compromisso',
            'Situação da Proposta': 'situacao_proposta',
            'Regime Simplificado': 'regime_simplificado',
            'Valor Repasse': 'valor_repasse',
            'Valor Investimento': 'valor_investimento',
            'Valor Empenhado': 'valor_empenhado',
            'Valor Pago C.Convênio': 'valor_pago_convenio',
            'Valor Desbloqueado': 'valor_desbloqueado',
            'Ação Orçamentária': 'acao_orcamentaria',
            'Envio para CAIXA': 'envio_para_caixa',
            'PT em Complementação': 'pt_em_complementacao',
            'PT em Análise': 'pt_em_analise',
            'PT Aprovado': 'pt_aprovado',
            'Emissão Empenho': 'emissao_empenho',
            'TC Assinado': 'tc_assinado',
            'Vencimento da Suspensiva': 'vencimento_suspensiva',
            'Classificação Suspensiva': 'classificacao_suspensiva',
            'Suspensiva': 'suspensiva',
            'Data Cumprimento Suspensiva': 'data_cumprimento_suspensiva',
            'Último Envio Suspensiva (dentro do prazo contratual)': 'ultimo_envio_suspensiva_prazo',
            'Último Envio Suspensiva': 'ultimo_envio_suspensiva',
            'Última Evolução Suspensiva': 'ultima_evolucao_suspensiva',
            'Dias sem movimentação': 'dias_sem_movimentacao',
            'Prazo Suspensiva Contratual': 'prazo_suspensiva_contratual',
            'Limite para retirada da suspensiva (90 dias)': 'limite_retirada_suspensiva_90',
            'Limite para retirada da suspensiva (prorrogação 30 dias)': 'limite_retirada_suspensiva_prorrogacao',
            'Prazo para retirada da suspensiva (dias)': 'prazo_retirada_suspensiva_dias',
            'Data Retirada Suspensiva': 'data_retirada_suspensiva',
            'Qd.Complementações de Suspensiva': 'qd_complementacoes_suspensiva',
            'Situação da Análise Suspensiva': 'situacao_analise_suspensiva',
            'Situação da AIL': 'situacao_ail',
            'Data solicitação AIL ao Repassador': 'data_solicitacao_ail_repassador',
            'Data recebimento retorno AIL pelo Repassador': 'data_recebimento_retorno_ail',
            'Data envio da AIL ao Recebedor': 'data_envio_ail_recebedor',
            'Data Previsão Publicação Edital Licitação': 'data_previsao_publicacao_edital',
            'Data Publicação Edital Licitação': 'data_publicacao_edital',
            'Primeiro Envio da Licitação': 'primeiro_envio_licitacao',
            'Último Envio da Licitação': 'ultimo_envio_licitacao',
            'Situação da Análise VRPL': 'situacao_analise_vrpl',
            'Dias sem movimentação VRPL': 'dias_sem_movimentacao_vrpl',
            'Data Conclusão Análise VRPL': 'data_conclusao_analise_vrpl',
            'Data Aceite VRPL': 'data_aceite_vrpl',
            'Data Última Movimentação VRPL': 'data_ultima_movimentacao_vrpl',
            'Data Homologação Licitação': 'data_homologacao_licitacao',
            'Data Previsão Ordem Serviço': 'data_previsao_ordem_servico',
            'Data Emissão Ordem Serviço': 'data_emissao_ordem_servico',
            'Data Previsão Início de Obra': 'data_previsao_inicio_obra',
            'Data Início de Obra (TGov)': 'data_inicio_obra_tgov',
            'Data Último BM (TGOV)': 'data_ultimo_bm_tgov',
            'Data Último BM (REUNI)': 'data_ultimo_bm_reuni',
            'Percentual informado (REUNI)': 'percentual_informado_reuni',
            'Percentual informado (TGov)': 'percentual_informado_tgov',
            'Percentual realizado (REUNI)': 'percentual_realizado_reuni',
            'Percentual realizado (TGov)': 'percentual_realizado_tgov',
            'Valor Informado no último BM (TGov)': 'valor_informado_ultimo_bm_tgov',
            'Valor Informado no último BM (REUNI)': 'valor_informado_ultimo_bm_reuni',
            'Execução por Etapas': 'execucao_por_etapas',
            'Etiquetas': 'etiquetas',
            'Situação Atual': 'situacao_atual',
            'Data atualização da Situação Atual': 'data_atualizacao_situacao_atual',
            'Data Atualização': 'data_atualizacao'
        }
        
        df.rename(columns=column_mapping, inplace=True)
        logger.info("✅ Column names standardized")
        return df
    
    def transform_data(self, df):
        """Transform data types and clean values"""
        
        # Convert money values to centavos (integer)
        money_columns = [
            'valor_repasse', 'valor_investimento', 'valor_empenhado',
            'valor_pago_convenio', 'valor_desbloqueado',
            'valor_informado_ultimo_bm_tgov', 'valor_informado_ultimo_bm_reuni'
        ]
        
        for col in money_columns:
            if col in df.columns:
                # Convert to centavos to avoid floating point issues
                df[f'{col}_centavos'] = (df[col] * 100).fillna(0).astype('int64')
                df.drop(columns=[col], inplace=True)
        
        # Convert boolean fields
        if 'execucao_por_etapas' in df.columns:
            df['execucao_por_etapas'] = df['execucao_por_etapas'].map({'Sim': True, 'Não': False}).fillna(False)
        
        # Ensure proposta is string and not null
        df['proposta'] = df['proposta'].astype(str)
        
        # Handle numeric columns
        numeric_cols = ['operacao', 'dv', 'instrumento', 'dias_sem_movimentacao', 
                       'qd_complementacoes_suspensiva', 'dias_sem_movimentacao_vrpl',
                       'prazo_retirada_suspensiva_dias']
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Clean percentage fields
        pct_cols = ['percentual_informado_reuni', 'percentual_informado_tgov',
                   'percentual_realizado_reuni', 'percentual_realizado_tgov']
        
        for col in pct_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                df[col] = df[col].fillna(0.0)
        
        logger.info("✅ Data transformed")
        return df
    
    def load_to_database(self, df):
        """Load data to PostgreSQL"""
        try:
            # Select only columns that exist in our schema
            columns_to_load = [col for col in df.columns if col in [
                'proposta', 'operacao', 'dv', 'instrumento', 'recebedor',
                'ente_vinculacao', 'uf', 'municipio_beneficiado', 'gigov_regov',
                'gigov_vinculacao', 'repassador', 'programa', 'objetivo',
                'latitude', 'longitude', 'tipo', 'tipologia',
                'situacao_termo_compromisso', 'situacao_proposta', 'regime_simplificado',
                'valor_repasse_centavos', 'valor_investimento_centavos',
                'valor_empenhado_centavos', 'valor_pago_convenio_centavos',
                'valor_desbloqueado_centavos', 'envio_para_caixa',
                'pt_em_complementacao', 'pt_em_analise', 'pt_aprovado',
                'emissao_empenho', 'tc_assinado', 'vencimento_suspensiva',
                'classificacao_suspensiva', 'suspensiva', 'data_cumprimento_suspensiva',
                'ultimo_envio_suspensiva_prazo', 'ultimo_envio_suspensiva',
                'ultima_evolucao_suspensiva', 'dias_sem_movimentacao',
                'prazo_suspensiva_contratual', 'limite_retirada_suspensiva_90',
                'limite_retirada_suspensiva_prorrogacao', 'prazo_retirada_suspensiva_dias',
                'data_retirada_suspensiva', 'qd_complementacoes_suspensiva',
                'situacao_analise_suspensiva', 'situacao_ail',
                'data_solicitacao_ail_repassador', 'data_recebimento_retorno_ail',
                'data_envio_ail_recebedor', 'data_previsao_publicacao_edital',
                'data_publicacao_edital', 'primeiro_envio_licitacao',
                'ultimo_envio_licitacao', 'situacao_analise_vrpl',
                'dias_sem_movimentacao_vrpl', 'data_conclusao_analise_vrpl',
                'data_aceite_vrpl', 'data_ultima_movimentacao_vrpl',
                'data_homologacao_licitacao', 'data_previsao_ordem_servico',
                'data_emissao_ordem_servico', 'data_previsao_inicio_obra',
                'data_inicio_obra_tgov', 'data_ultimo_bm_tgov',
                'data_ultimo_bm_reuni', 'percentual_informado_reuni',
                'percentual_informado_tgov', 'percentual_realizado_reuni',
                'percentual_realizado_tgov', 'valor_informado_ultimo_bm_tgov_centavos',
                'valor_informado_ultimo_bm_reuni_centavos', 'execucao_por_etapas',
                'etiquetas', 'situacao_atual', 'data_atualizacao_situacao_atual',
                'data_atualizacao'
            ]]
            
            df_to_load = df[columns_to_load].copy()
            
            # Load to database
            df_to_load.to_sql(
                'pac_operations',
                self.engine,
                if_exists='replace',
                index=False,
                method='multi',
                chunksize=500
            )
            
            logger.info(f"✅ Loaded {len(df_to_load)} records to database")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load to database: {e}")
            return False
    
    def run(self):
        """Execute the complete ETL pipeline"""
        logger.info("🚀 Starting REUNI ETL Pipeline")
        
        # Connect to database
        if not self.connect_db():
            return False
        
        # Load Excel
        df = self.load_excel()
        if df is None:
            return False
        
        # Clean column names
        df = self.clean_column_names(df)
        
        # Transform data
        df = self.transform_data(df)
        
        # Load to database
        success = self.load_to_database(df)
        
        if success:
            logger.info("🎉 ETL Pipeline completed successfully!")
        else:
            logger.error("💥 ETL Pipeline failed!")
            
        return success


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Load REUNI Excel data to PostgreSQL')
    parser.add_argument('excel_path', help='Path to REUNI Excel file')
    parser.add_argument('--db-url', help='Database URL (or set DATABASE_URL env var)')
    
    args = parser.parse_args()
    
    etl = ReuniETL(args.excel_path, args.db_url)
    etl.run()
