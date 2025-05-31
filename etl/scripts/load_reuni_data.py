"""
ETL script to load REUNI Excel data into PostgreSQL
"""
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import logging
from datetime import datetime
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ReuniETL:
    def __init__(self, excel_path, db_url):
        self.excel_path = excel_path
        self.db_url = db_url
        self.engine = None
        
    def connect_db(self):
        """Connect to PostgreSQL database"""
        try:
            self.engine = create_engine(self.db_url)
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("✅ Connected to database")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            return False
    
    def load_excel(self):
        """Load Excel file into pandas DataFrame"""
        try:
            logger.info(f"📂 Loading Excel file: {self.excel_path}")
            df = pd.read_excel(self.excel_path, engine='openpyxl')
            logger.info(f"✅ Loaded {len(df)} records with {len(df.columns)} columns")
            return df
        except Exception as e:
            logger.error(f"❌ Failed to load Excel: {e}")
            return None
    
    def standardize_column_names(self, df):
        """Standardize column names for PostgreSQL"""
        column_mapping = {
            'ID_OPERAÇÃO': 'id_operacao',
            'UF': 'uf',
            'SIGLA_UF': 'sigla_uf',
            'MUNICÍPIO_BENEFICIADO': 'municipio_beneficiado',
            'COD_IBGE': 'cod_ibge',
            'TIPO_DE_OBRA': 'tipo_de_obra',
            'EMPREENDIMENTO': 'empreendimento',
            'ÁREA/SETOR': 'area_setor',
            'OBSERVAÇÕES': 'observacoes',
            'ORIGEM_DO_RECURSO': 'origem_do_recurso',
            'NÚMERO_DO_CONTRATO': 'numero_do_contrato',
            'PROPONENTE': 'proponente',
            'MODALIDADE': 'modalidade',
            'SELEÇÃO': 'selecao',
            'EXECUTOR': 'executor',
            'CNPJ_PROPONENTE': 'cnpj_proponente',
            'DATA_DE_SELEÇÃO': 'data_de_selecao',
            'VALOR_DE_REPASSE': 'valor_repasse',
            'VALOR_DE_CONTRAPARTIDA': 'valor_contrapartida',
            'VALOR_DE_INVESTIMENTO': 'valor_investimento',
            'DATA_BASE': 'data_base',
            'CATEGORIA': 'categoria',
            'EXECUÇÃO_POR_ETAPAS': 'execucao_por_etapas',
            'ETAPA': 'etapa',
            'PROGRAMA': 'programa',
            'AÇÃO': 'acao',
            'MINISTÉRIO': 'ministerio',
            'VALOR_CONTRATADO': 'valor_contratado',
            'DATA_ASSINATURA': 'data_assinatura',
            'DATA_INÍCIO_VIGÊNCIA': 'data_inicio_vigencia',
            'DATA_FIM_VIGÊNCIA': 'data_fim_vigencia',
            'SITUAÇÃO_DA_OPERAÇÃO': 'situacao_da_operacao',
            'ESTÁGIO': 'estagio',
            '%_DE_EXECUÇÃO': 'percentual_execucao',
            'VALOR_DESBLOQUEADO': 'valor_desbloqueado',
            'VALOR_DESEMBOLSADO': 'valor_desembolsado',
            'DATA_DO_ÚLTIMO_DESBLOQUEIO': 'data_ultimo_desbloqueio',
            'DATA_DO_ÚLTIMO_DESEMBOLSO': 'data_ultimo_desembolso',
            'PROVIDÊNCIA_TÉCNICA': 'providencia_tecnica',
            'DESCRIÇÃO_PROVIDÊNCIA_TÉCNICA': 'descricao_providencia_tecnica',
            'DATA_PROVIDÊNCIA_TÉCNICA': 'data_providencia_tecnica',
            'PRAZO_PROVIDÊNCIA_TÉCNICA': 'prazo_providencia_tecnica',
            'RESTRIÇÃO': 'restricao',
            'CATEGORIA_RESTRIÇÃO': 'categoria_restricao',
            'RESPONSÁVEL_PELA_RESTRIÇÃO': 'responsavel_pela_restricao',
            'DESCRIÇÃO_RESTRIÇÃO': 'descricao_restricao',
            'DATA_INCLUSÃO_RESTRIÇÃO': 'data_inclusao_restricao',
            'PRAZO_RESTRIÇÃO': 'prazo_restricao'
        }
        
        # Rename columns
        df = df.rename(columns=column_mapping)
        
        # Handle any remaining columns not in mapping
        df.columns = [col.lower().replace(' ', '_').replace('/', '_').replace('ç', 'c').replace('ã', 'a').replace('õ', 'o').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u').replace('â', 'a').replace('ê', 'e').replace('ô', 'o').replace('à', 'a').replace('ü', 'u') for col in df.columns]
        
        logger.info("✅ Column names standardized")
        return df
    
    def transform_data(self, df):
        """Transform data types and clean data"""
        try:
            # Convert money columns to centavos (integer)
            money_columns = [
                'valor_repasse', 'valor_contrapartida', 'valor_investimento',
                'valor_contratado', 'valor_desbloqueado', 'valor_desembolsado'
            ]
            
            for col in money_columns:
                if col in df.columns:
                    # Convert to float, multiply by 100, then to integer
                    df[col + '_centavos'] = pd.to_numeric(df[col], errors='coerce').fillna(0) * 100
                    df[col + '_centavos'] = df[col + '_centavos'].astype('int64')
                    df.drop(columns=[col], inplace=True)
            
            # Convert date columns
            date_columns = [
                'data_de_selecao', 'data_base', 'data_assinatura',
                'data_inicio_vigencia', 'data_fim_vigencia',
                'data_ultimo_desbloqueio', 'data_ultimo_desembolso',
                'data_providencia_tecnica', 'data_inclusao_restricao'
            ]
            
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            
            # Convert percentage column
            if 'percentual_execucao' in df.columns:
                df['percentual_execucao'] = pd.to_numeric(df['percentual_execucao'], errors='coerce')
            
            # Convert boolean
            if 'execucao_por_etapas' in df.columns:
                df['execucao_por_etapas'] = df['execucao_por_etapas'].map({'Sim': True, 'Não': False}).fillna(False)
            
            # Add ETL metadata
            df['etl_loaded_at'] = datetime.now()
            df['etl_source_file'] = os.path.basename(self.excel_path)
            
            logger.info("✅ Data transformed")
            return df
            
        except Exception as e:
            logger.error(f"❌ Failed to transform data: {e}")
            return None
    
    def load_to_db(self, df):
        """Load DataFrame to PostgreSQL"""
        try:
            # Use TRUNCATE CASCADE to handle foreign keys
            with self.engine.connect() as conn:
                conn.execute(text("TRUNCATE TABLE pac_operations CASCADE"))
                conn.commit()
            
            # Load data
            df.to_sql(
                'pac_operations',
                self.engine,
                if_exists='append',  # Use append since we truncated
                index=False,
                chunksize=1000
            )
            
            logger.info(f"✅ Loaded {len(df)} records to database")
            
            # Record load history if table exists
            try:
                with self.engine.connect() as conn:
                    conn.execute(
                        text("""
                        INSERT INTO etl_load_history (
                            source_file, records_loaded, load_status, load_timestamp
                        ) VALUES (
                            :source_file, :records_loaded, 'success', :timestamp
                        )
                        """),
                        {
                            'source_file': os.path.basename(self.excel_path),
                            'records_loaded': len(df),
                            'timestamp': datetime.now()
                        }
                    )
                    conn.commit()
            except:
                # If etl_load_history doesn't exist, skip it
                pass
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load to database: {e}")
            return False
    
    def run(self):
        """Run the complete ETL pipeline"""
        logger.info("🚀 Starting REUNI ETL Pipeline")
        
        # Connect to database
        if not self.connect_db():
            logger.error("💥 ETL Pipeline failed!")
            return False
        
        # Load Excel
        df = self.load_excel()
        if df is None:
            logger.error("💥 ETL Pipeline failed!")
            return False
        
        # Standardize column names
        df = self.standardize_column_names(df)
        
        # Transform data
        df = self.transform_data(df)
        if df is None:
            logger.error("💥 ETL Pipeline failed!")
            return False
        
        # Load to database
        if not self.load_to_db(df):
            logger.error("💥 ETL Pipeline failed!")
            return False
        
        logger.info("🎉 ETL Pipeline completed successfully!")
        return True
