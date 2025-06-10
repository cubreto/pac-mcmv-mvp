#!/usr/bin/env python3
"""
Enhanced PAC ETL Script with Real-Time Capabilities - COMPLETE FIX
Load 78-column OGU data into PAC database with change tracking
FIXED: Foreign key constraint violation and proper execution sequence
"""

import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text
import os
import sys
from datetime import datetime, timezone
import logging
import hashlib
import json
import time
from typing import Dict, List, Tuple, Optional

# Setup enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedPACETL:
    def __init__(self):
        self.batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.start_time = datetime.now(timezone.utc)
        self.engine = None
        self.data_quality_checks = []
        self.changes_detected = {
            'new_operations': [],
            'updated_operations': [],
            'status_changes': [],
            'significant_delays': []
        }
        
    def get_database_connection(self):
        """Get database connection using environment variables"""
        try:
            # Try environment variables first (Docker setup)
            db_host = os.getenv('DB_HOST', 'localhost')
            db_port = os.getenv('DB_PORT', '5434')
            db_name = os.getenv('DB_NAME', 'pac_database')
            db_user = os.getenv('DB_USER', 'postgres')
            db_password = os.getenv('DB_PASSWORD', 'postgres123')
            
            connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
            self.engine = create_engine(connection_string)
            
            logger.info(f"Connected to database: {db_host}:{db_port}/{db_name}")
            return self.engine
            
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def find_pac_data_file(self) -> Optional[str]:
        """Find the PAC OGU data file"""
        possible_paths = [
            '/app/data/pac/REUNI_Operações_Novo_PAC_OGU_Interno_CAIXA_21-05-2025.xlsx',  # Docker path
            './data/pac/REUNI_Operações_Novo_PAC_OGU_Interno_CAIXA_21-05-2025.xlsx',    # Local development
            'data/pac/REUNI_Operações_Novo_PAC_OGU_Interno_CAIXA_21-05-2025.xlsx',      # Alternative local
            os.path.expanduser('~/Downloads/REUNI GOV 2/REUNI_Operações_Novo_PAC_OGU_Interno_CAIXA_21-05-2025.xlsx'),  # Original location
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"Found PAC data file: {path}")
                return path
        
        logger.error("PAC data file not found in any expected location")
        logger.info(f"Searched paths: {possible_paths}")
        return None

    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of the source file"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.warning(f"Could not calculate file hash: {e}")
            return "unknown"

    def load_and_validate_data(self, file_path: str) -> pd.DataFrame:
        """Load Excel file and validate structure"""
        try:
            logger.info(f"Loading data from: {file_path}")
            
            # Load Excel file
            if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                df = pd.read_excel(file_path)
            else:
                df = pd.read_csv(file_path)
            
            logger.info(f"Data loaded: {len(df)} rows, {len(df.columns)} columns")
            logger.info(f"First 5 column names: {list(df.columns)[:5]}")
            
            # Enhanced data quality checks
            self.perform_data_quality_checks(df)
            
            if df.empty:
                raise ValueError("Data file is empty")
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            raise

    def perform_data_quality_checks(self, df: pd.DataFrame) -> None:
        """Perform comprehensive data quality checks"""
        
        # Check 1: Row count validation
        if len(df) == 0:
            self.data_quality_checks.append({
                'check': 'row_count',
                'status': 'FAIL',
                'details': 'No data rows found',
                'value_found': str(len(df)),
                'expected_value': '>0'
            })
        elif len(df) < 100:
            self.data_quality_checks.append({
                'check': 'row_count',
                'status': 'WARNING',
                'details': 'Low row count detected',
                'value_found': str(len(df)),
                'expected_value': '>=100'
            })
        else:
            self.data_quality_checks.append({
                'check': 'row_count',
                'status': 'PASS',
                'details': 'Row count within expected range',
                'value_found': str(len(df)),
                'expected_value': '>=100'
            })
        
        # Check 2: Required columns presence
        required_columns = ['Operação', 'UF', 'Município Beneficiado', 'Repassador']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            self.data_quality_checks.append({
                'check': 'required_columns',
                'status': 'FAIL',
                'details': f'Missing required columns: {missing_columns}',
                'value_found': str(len(df.columns) - len(missing_columns)),
                'expected_value': str(len(required_columns))
            })
        else:
            self.data_quality_checks.append({
                'check': 'required_columns',
                'status': 'PASS',
                'details': 'All required columns present',
                'value_found': str(len(required_columns)),
                'expected_value': str(len(required_columns))
            })
        
        # Check 3: Data completeness for key fields
        if 'Operação' in df.columns:
            null_operations = df['Operação'].isnull().sum()
            if null_operations > 0:
                self.data_quality_checks.append({
                    'check': 'operation_completeness',
                    'status': 'FAIL',
                    'details': f'{null_operations} null operation IDs found',
                    'value_found': str(null_operations),
                    'expected_value': '0'
                })
            else:
                self.data_quality_checks.append({
                    'check': 'operation_completeness',
                    'status': 'PASS',
                    'details': 'No null operation IDs',
                    'value_found': '0',
                    'expected_value': '0'
                })
        
        # Check 4: Duplicate operations
        if 'Operação' in df.columns:
            duplicates = df['Operação'].duplicated().sum()
            if duplicates > 0:
                self.data_quality_checks.append({
                    'check': 'duplicate_operations',
                    'status': 'WARNING',
                    'details': f'{duplicates} duplicate operation IDs found',
                    'value_found': str(duplicates),
                    'expected_value': '0'
                })
            else:
                self.data_quality_checks.append({
                    'check': 'duplicate_operations',
                    'status': 'PASS',
                    'details': 'No duplicate operation IDs',
                    'value_found': '0',
                    'expected_value': '0'
                })

    def calculate_data_quality_score(self) -> float:
        """Calculate overall data quality score"""
        if not self.data_quality_checks:
            return 1.0
        
        total_checks = len(self.data_quality_checks)
        passed_checks = sum(1 for check in self.data_quality_checks if check['status'] == 'PASS')
        warning_checks = sum(1 for check in self.data_quality_checks if check['status'] == 'WARNING')
        
        # Pass = 1.0, Warning = 0.5, Fail = 0.0
        score = (passed_checks + warning_checks * 0.5) / total_checks
        return round(score, 2)

    def map_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Map CSV columns to database schema - ENHANCED with all 78 columns"""
        
        # Complete column mapping based on your ACTUAL 78-column structure
        column_mapping = {
            # Basic info (columns 1-15)
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
            
            # Project Classification (columns 16-20)
            'Tipo': 'tipo',
            'Tipologia': 'tipologia',
            'Situação do Termo de Compromisso': 'situacao_termo_compromisso',
            'Situação da Proposta': 'situacao_proposta',
            'Regime Simplificado': 'regime_simplificado',
            
            # Financial Data (columns 21-26)
            'Valor Repasse': 'valor_repasse',
            'Valor Investimento': 'valor_investimento',
            'Valor Empenhado': 'valor_empenhado',
            'Valor Pago C.Convênio': 'valor_pago',
            'Valor Desbloqueado': 'valor_desbloqueado',
            'Ação Orçamentária': 'acao_orcamentaria',
            
            # Process Timeline (columns 27-32)
            'Envio para CAIXA': 'envio_caixa',
            'PT em Complementação': 'pt_complementacao',
            'PT em Análise': 'pt_analise',
            'PT Aprovado': 'pt_aprovado',
            'Emissão Empenho': 'emissao_empenho',
            'TC Assinado': 'tc_assinado',
            
            # Suspensiva Data (columns 33-47)
            'Vencimento da Suspensiva': 'vencimento_da_suspensiva',
            'Classificação Suspensiva': 'classificacao_suspensiva',
            'Suspensiva': 'suspensiva',
            'Data Cumprimento Suspensiva': 'data_cumprimento_suspensiva',
            'Último Envio Suspensiva (dentro do prazo contratual)': 'ultimo_envio_suspensiva_prazo',
            'Último Envio Suspensiva': 'ultimo_envio_suspensiva',
            'Última Evolução Suspensiva': 'ultima_evolucao_suspensiva',
            'Dias sem movimentação': 'dias_sem_movimentacao',
            'Prazo Suspensiva Contratual': 'prazo_suspensiva_contratual',
            'Limite para retirada da suspensiva (90 dias)': 'limite_retirada_90dias',
            'Limite para retirada da suspensiva (prorrogação 30 dias)': 'limite_retirada_prorrogacao',
            'Prazo para retirada da suspensiva (dias)': 'prazo_retirada_dias',
            'Data Retirada Suspensiva': 'data_retirada_suspensiva',
            'Qd.Complementações de Suspensiva': 'qtd_complementacoes_suspensiva',
            'Situação da Análise Suspensiva': 'situacao_da_analise_suspensiva',
            
            # AIL Process (columns 48-52)
            'Situação da AIL': 'situacao_ail',
            'Data solicitação AIL ao Repassador': 'data_solicitacao_ail',
            'Data recebimento retorno AIL pelo Repassador': 'data_recebimento_retorno_ail',
            'Data envio da AIL ao Recebedor': 'data_envio_ail_recebedor',
            'Data Previsão Publicação Edital Licitação': 'data_previsao_publicacao_edital',
            
            # Licitação Process (columns 53-61)
            'Data Publicação Edital Licitação': 'data_publicacao_edital',
            'Primeiro Envio da Licitação': 'primeiro_envio_licitacao',
            'Último Envio da Licitação': 'ultimo_envio_licitacao',
            'Situação da Análise VRPL': 'situacao_da_analise_vrpl',
            'Dias sem movimentação VRPL': 'dias_sem_movimentacao_vrpl',
            'Data Conclusão Análise VRPL': 'data_conclusao_analise_vrpl',
            'Data Aceite VRPL': 'data_aceite_vrpl',
            'Data Última Movimentação VRPL': 'data_ultima_movimentacao_vrpl',
            'Data Homologação Licitação': 'data_homologacao_licitacao',
            
            # Obras Process (columns 62-74)
            'Data Previsão Ordem Serviço': 'data_previsao_ordem_servico',
            'Data Emissão Ordem Serviço': 'data_emissao_ordem_servico',
            'Data Previsão Início de Obra': 'data_previsao_inicio_obra',
            'Data Início de Obra (TGov)': 'data_inicio_de_obra',
            'Data Último BM (TGOV)': 'data_ultimo_bm_tgov',
            'Data Último BM (REUNI)': 'data_ultimo_bm_reuni',
            'Percentual informado (REUNI)': 'percentual_informado_reuni',
            'Percentual informado (TGov)': 'percentual_informado_tgov',
            'Percentual realizado (REUNI)': 'percentual_realizado',
            'Percentual realizado (TGov)': 'percentual_realizado_tgov',
            'Valor Informado no último BM (TGov)': 'valor_ultimo_bm_tgov',
            'Valor Informado no último BM (REUNI)': 'valor_ultimo_bm_reuni',
            'Execução por Etapas': 'execucao_por_etapas',
            
            # Metadata and Status (columns 75-78)
            'Etiquetas': 'etiquetas',
            'Situação Atual': 'situacao_atual',
            'Data atualização da Situação Atual': 'data_atualizacao_situacao',
            'Data Atualização': 'data_atualizacao'
        }
        
        # Check which columns exist in the data
        available_columns = {}
        missing_columns = []
        
        for csv_col, db_col in column_mapping.items():
            if csv_col in df.columns:
                available_columns[csv_col] = db_col
            else:
                missing_columns.append(csv_col)
        
        logger.info(f"Available columns for mapping: {len(available_columns)}")
        if missing_columns:
            logger.warning(f"Missing expected columns: {missing_columns}")
        
        # Rename columns
        mapped_df = df.rename(columns=available_columns)
        
        # Select only the columns we can map
        db_columns = list(available_columns.values())
        final_df = mapped_df[db_columns].copy()
        
        logger.info(f"Mapped columns: {db_columns}")
        return final_df

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and prepare data for database insertion"""
        
        # Convert date columns - comprehensive list
        date_columns = [
            'envio_caixa', 'pt_complementacao', 'pt_analise', 'pt_aprovado', 'emissao_empenho', 'tc_assinado',
            'vencimento_da_suspensiva', 'data_cumprimento_suspensiva', 'data_retirada_suspensiva',
            'ultimo_envio_suspensiva_prazo', 'ultimo_envio_suspensiva', 'ultima_evolucao_suspensiva',
            'prazo_suspensiva_contratual', 'limite_retirada_90dias', 'limite_retirada_prorrogacao',
            'data_solicitacao_ail', 'data_recebimento_retorno_ail', 'data_envio_ail_recebedor',
            'data_previsao_publicacao_edital', 'data_publicacao_edital', 'primeiro_envio_licitacao',
            'ultimo_envio_licitacao', 'data_conclusao_analise_vrpl', 'data_aceite_vrpl',
            'data_ultima_movimentacao_vrpl', 'data_homologacao_licitacao', 'data_previsao_ordem_servico',
            'data_emissao_ordem_servico', 'data_previsao_inicio_obra', 'data_inicio_de_obra',
            'data_ultimo_bm_tgov', 'data_ultimo_bm_reuni', 'data_atualizacao_situacao', 'data_atualizacao'
        ]
        
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Convert numeric columns - comprehensive list
        numeric_columns = [
            'latitude', 'longitude', 'dias_sem_movimentacao', 'prazo_retirada_dias',
            'qtd_complementacoes_suspensiva', 'dias_sem_movimentacao_vrpl',
            'valor_repasse', 'valor_investimento', 'valor_empenhado', 'valor_pago', 'valor_desbloqueado',
            'percentual_informado_reuni', 'percentual_informado_tgov', 'percentual_realizado',
            'percentual_realizado_tgov', 'valor_ultimo_bm_tgov', 'valor_ultimo_bm_reuni'
        ]
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Clean text columns - comprehensive list
        text_columns = [
            'proposta', 'operacao', 'dv', 'instrumento', 'recebedor', 'ente_vinculacao',
            'uf', 'municipio_beneficiado', 'gigov_regov', 'gigov_vinculacao', 'repassador',
            'programa', 'objetivo', 'tipo', 'tipologia', 'situacao_termo_compromisso',
            'situacao_proposta', 'regime_simplificado', 'acao_orcamentaria',
            'classificacao_suspensiva', 'suspensiva', 'situacao_da_analise_suspensiva',
            'situacao_ail', 'situacao_da_analise_vrpl', 'execucao_por_etapas',
            'etiquetas', 'situacao_atual'
        ]
        
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                df[col] = df[col].replace('nan', None)
        
        # Add tracking metadata
        df['data_load_timestamp'] = self.start_time
        df['data_batch_id'] = self.batch_id
        df['record_version'] = 1
        df['is_active'] = True
        df['first_seen_batch'] = self.batch_id
        df['last_updated_batch'] = self.batch_id
        
        # Calculate record hash for change detection
        if 'operacao' in df.columns:
            df['record_hash'] = df.apply(self.calculate_record_hash, axis=1)
        
        logger.info(f"Data cleaned: {len(df)} rows ready for insertion")
        return df

    def calculate_record_hash(self, row: pd.Series) -> str:
        """Calculate hash of key fields for change detection"""
        key_fields = ['operacao', 'situacao_atual', 'dias_sem_movimentacao', 'valor_empenhado']
        hash_data = ""
        
        for field in key_fields:
            if field in row.index and pd.notna(row[field]):
                hash_data += str(row[field])
        
        if hash_data:
            return hashlib.md5(hash_data.encode()).hexdigest()
        else:
            return hashlib.md5(str(row.get('operacao', '')).encode()).hexdigest()

    def load_existing_data(self) -> Optional[pd.DataFrame]:
        """Load existing data for change detection"""
        try:
            query = """
            SELECT operacao, situacao_atual, dias_sem_movimentacao, valor_empenhado, 
                   record_hash, record_version
            FROM pac_ogu_data 
            WHERE is_active = TRUE
            """
            existing_df = pd.read_sql(query, self.engine)
            logger.info(f"Loaded {len(existing_df)} existing records for comparison")
            return existing_df
        except Exception as e:
            logger.warning(f"Could not load existing data: {e}")
            return None

    def detect_changes(self, new_df: pd.DataFrame, existing_df: Optional[pd.DataFrame]) -> None:
        """Enhanced change detection with detailed tracking"""
        
        if existing_df is None or existing_df.empty:
            # All records are new
            self.changes_detected['new_operations'] = [str(op) for op in new_df['operacao'].dropna().tolist()]
            logger.info(f"All {len(new_df)} operations are new (first load)")
            return
        
        # Clean operation IDs and create sets
        new_ops_clean = set(str(op) for op in new_df['operacao'].dropna() if str(op) != 'nan')
        existing_ops_clean = set(str(op) for op in existing_df['operacao'].dropna() if str(op) != 'nan')
        
        # Detect new operations
        new_operations = new_ops_clean - existing_ops_clean
        self.changes_detected['new_operations'] = list(new_operations)
        
        # Detect updates in existing operations
        common_ops = new_ops_clean.intersection(existing_ops_clean)
        
        for op in common_ops:
            try:
                # Find records safely
                new_matches = new_df[new_df['operacao'].astype(str) == str(op)]
                existing_matches = existing_df[existing_df['operacao'].astype(str) == str(op)]
                
                if new_matches.empty or existing_matches.empty:
                    continue
                
                new_record = new_matches.iloc[0]
                existing_record = existing_matches.iloc[0]
                
                # Compare hashes safely
                new_hash = new_record.get('record_hash', '')
                existing_hash = existing_record.get('record_hash', '')
                
                if new_hash != existing_hash and new_hash != '' and existing_hash != '':
                    self.changes_detected['updated_operations'].append(str(op))
                    
                    # Detect specific changes
                    if ('situacao_atual' in new_record.index and 
                        'situacao_atual' in existing_record.index):
                        
                        old_status = existing_record['situacao_atual']
                        new_status = new_record['situacao_atual']
                        
                        if pd.notna(old_status) and pd.notna(new_status) and old_status != new_status:
                            self.changes_detected['status_changes'].append({
                                'operacao': str(op),
                                'old_status': str(old_status),
                                'new_status': str(new_status)
                            })
                    
                    # Detect significant delays
                    if ('dias_sem_movimentacao' in new_record.index and 
                        'dias_sem_movimentacao' in existing_record.index):
                        
                        old_days = existing_record['dias_sem_movimentacao']
                        new_days = new_record['dias_sem_movimentacao']
                        
                        if (pd.notna(old_days) and pd.notna(new_days) and 
                            float(new_days) > float(old_days) + 5):
                            
                            self.changes_detected['significant_delays'].append({
                                'operacao': str(op),
                                'days_increase': float(new_days) - float(old_days),
                                'old_days': float(old_days),
                                'new_days': float(new_days)
                            })
                            
            except Exception as e:
                logger.warning(f"Error processing operation {op}: {e}")
                continue
        
        # Log change summary
        logger.info(f"Change detection completed:")
        logger.info(f"  New operations: {len(self.changes_detected['new_operations'])}")
        logger.info(f"  Updated operations: {len(self.changes_detected['updated_operations'])}")
        logger.info(f"  Status changes: {len(self.changes_detected['status_changes'])}")
        logger.info(f"  Significant delays: {len(self.changes_detected['significant_delays'])}")

    def save_metadata(self, total_records: int, source_file: str, file_hash: str) -> None:
        """Save batch metadata - MUST BE CALLED BEFORE INSERTING DATA"""
        try:
            processing_duration = (datetime.now(timezone.utc) - self.start_time).total_seconds()
            quality_score = self.calculate_data_quality_score()
            
            metadata = {
                'batch_id': self.batch_id,
                'load_timestamp': self.start_time,
                'total_records': total_records,
                'source_file_name': os.path.basename(source_file),
                'source_file_hash': file_hash,
                'data_quality_score': quality_score,
                'processing_duration_seconds': int(processing_duration),
                'status': 'SUCCESS',
                'new_operations_count': len(self.changes_detected['new_operations']),
                'updated_operations_count': len(self.changes_detected['updated_operations']),
                'errors_detected': sum(1 for check in self.data_quality_checks if check['status'] == 'FAIL')
            }
            
            # Insert metadata - this creates the foreign key that data records will reference
            with self.engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO pac_data_metadata 
                    (batch_id, load_timestamp, total_records, source_file_name, source_file_hash,
                     data_quality_score, processing_duration_seconds, status, new_operations_count,
                     updated_operations_count, errors_detected)
                    VALUES (:batch_id, :load_timestamp, :total_records, :source_file_name, 
                            :source_file_hash, :data_quality_score, :processing_duration_seconds,
                            :status, :new_operations_count, :updated_operations_count, :errors_detected)
                """), metadata)
                conn.commit()
            
            logger.info(f"Metadata saved for batch {self.batch_id}")
            
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
            raise

    def save_quality_checks(self) -> None:
        """Save data quality check results"""
        try:
            if not self.data_quality_checks:
                logger.info("No quality checks to save")
                return
                
            quality_records = []
            for check in self.data_quality_checks:
                quality_records.append({
                    'batch_id': self.batch_id,
                    'quality_check': check['check'],
                    'status': check['status'],
                    'details': check['details'],
                    'value_found': check['value_found'],
                    'expected_value': check['expected_value']
                })
            
            if quality_records:
                quality_df = pd.DataFrame(quality_records)
                quality_df.to_sql('pac_data_quality_log', self.engine, 
                                if_exists='append', index=False)
                
                logger.info(f"Saved {len(quality_records)} quality check results")
        
        except Exception as e:
            logger.error(f"Failed to save quality checks: {e}")
            # Don't fail the entire ETL for quality tracking issues

    def save_changes(self) -> None:
        """Save detected changes"""
        try:
            change_records = []
            
            # Save new operations
            for op in self.changes_detected['new_operations']:
                if op and str(op) != 'nan':
                    change_records.append({
                        'batch_id': self.batch_id,
                        'operacao': str(op)[:100],  # Limit length
                        'change_type': 'NEW',
                        'field_name': None,
                        'old_value': None,
                        'new_value': None,
                        'significance_score': 5
                    })
            
            # Save status changes
            for change in self.changes_detected['status_changes']:
                if change.get('operacao') and str(change['operacao']) != 'nan':
                    change_records.append({
                        'batch_id': self.batch_id,
                        'operacao': str(change['operacao'])[:100],
                        'change_type': 'STATUS_CHANGE',
                        'field_name': 'situacao_atual',
                        'old_value': str(change.get('old_status', ''))[:500],
                        'new_value': str(change.get('new_status', ''))[:500],
                        'significance_score': 7
                    })
            
            # Save significant delays
            for change in self.changes_detected['significant_delays']:
                if change.get('operacao') and str(change['operacao']) != 'nan':
                    change_records.append({
                        'batch_id': self.batch_id,
                        'operacao': str(change['operacao'])[:100],
                        'change_type': 'DELAY_INCREASE',
                        'field_name': 'dias_sem_movimentacao',
                        'old_value': str(change.get('old_days', ''))[:500],
                        'new_value': str(change.get('new_days', ''))[:500],
                        'significance_score': 8
                    })
            
            if change_records:
                changes_df = pd.DataFrame(change_records)
                changes_df.to_sql('pac_data_changes', self.engine, 
                                if_exists='append', index=False)
                
                logger.info(f"Saved {len(change_records)} change records")
            else:
                logger.info("No changes to save")
        
        except Exception as e:
            logger.error(f"Failed to save changes: {e}")
            # Don't fail the entire ETL for change tracking issues

    def load_to_database(self, df: pd.DataFrame) -> int:
        """Load data into database with version management"""
        try:
            # Mark existing records as inactive (soft delete approach)
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM pac_ogu_data WHERE is_active = TRUE"))
                existing_count = result.fetchone()[0]
                
                if existing_count > 0:
                    logger.info(f"Marking {existing_count} existing records as inactive...")
                    conn.execute(text("UPDATE pac_ogu_data SET is_active = FALSE WHERE is_active = TRUE"))
                    conn.commit()
            
            # Insert new data
            logger.info(f"Inserting {len(df)} new records...")
            df.to_sql(
                'pac_ogu_data',
                self.engine,
                if_exists='append',
                index=False,
                method='multi',
                chunksize=1000
            )
            
            # Verify insertion
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM pac_ogu_data WHERE is_active = TRUE"))
                final_count = result.fetchone()[0]
            
            logger.info(f"Data insertion completed: {final_count} active records")
            return final_count
            
        except Exception as e:
            logger.error(f"Database insertion failed: {e}")
            raise

    def run(self) -> Dict:
        """Main ETL process with CORRECTED execution sequence"""
        try:
            logger.info(f"Starting enhanced PAC ETL process - Batch {self.batch_id}")
            
            # 1. Find data file
            file_path = self.find_pac_data_file()
            if not file_path:
                raise FileNotFoundError("PAC data file not found")
            
            # 2. Calculate file hash
            file_hash = self.calculate_file_hash(file_path)
            
            # 3. Connect to database
            self.get_database_connection()
            
            # 4. Load existing data for comparison
            existing_df = self.load_existing_data()
            
            # 5. Load and validate new data
            df = self.load_and_validate_data(file_path)
            
            # 6. Map columns
            mapped_df = self.map_columns(df)
            
            # 7. Clean data
            clean_df = self.clean_data(mapped_df)
            
            # 8. Detect changes
            self.detect_changes(clean_df, existing_df)
            
            # 9. CRITICAL: Save metadata FIRST (creates foreign key)
            self.save_metadata(len(clean_df), file_path, file_hash)
            
            # 10. Load to database (now foreign key exists)
            record_count = self.load_to_database(clean_df)
            
            # 11. Save quality checks and changes
            self.save_quality_checks()
            self.save_changes()
            
            # 12. Generate summary
            summary = {
                'status': 'SUCCESS',
                'batch_id': self.batch_id,
                'records_processed': record_count,
                'processing_time_seconds': (datetime.now(timezone.utc) - self.start_time).total_seconds(),
                'data_quality_score': self.calculate_data_quality_score(),
                'changes_detected': self.changes_detected,
                'quality_checks': len(self.data_quality_checks)
            }
            
            logger.info(f"Enhanced PAC ETL completed successfully: {record_count} records processed")
            logger.info(f"Quality score: {summary['data_quality_score']*100:.1f}%")
            
            return summary
            
        except Exception as e:
            # Save error metadata if possible
            try:
                if self.engine:
                    with self.engine.connect() as conn:
                        conn.execute(text("""
                            INSERT INTO pac_data_metadata 
                            (batch_id, load_timestamp, total_records, status, errors_detected)
                            VALUES (:batch_id, :load_timestamp, 0, 'ERROR', 1)
                        """), {
                            'batch_id': self.batch_id,
                            'load_timestamp': self.start_time
                        })
                        conn.commit()
            except:
                pass
            
            logger.error(f"Enhanced PAC ETL failed: {e}")
            return {
                'status': 'ERROR',
                'batch_id': self.batch_id,
                'error_message': str(e)
            }

def main():
    """Main entry point"""
    etl = EnhancedPACETL()
    result = etl.run()
    
    if result['status'] == 'SUCCESS':
        print(f"\n✅ ETL completed successfully - Batch: {result['batch_id']}")
        print(f"📊 Records processed: {result['records_processed']:,}")
        print(f"⏱️ Processing time: {result['processing_time_seconds']:.1f}s")
        print(f"🎯 Quality score: {result['data_quality_score']*100:.1f}%")
        
        if result['changes_detected']['new_operations']:
            print(f"✨ New operations: {len(result['changes_detected']['new_operations'])}")
        if result['changes_detected']['status_changes']:
            print(f"🔄 Status changes: {len(result['changes_detected']['status_changes'])}")
        if result['changes_detected']['significant_delays']:
            print(f"⚠️ Significant delays: {len(result['changes_detected']['significant_delays'])}")
        
        sys.exit(0)
    else:
        print(f"\n❌ ETL failed: {result.get('error_message', 'Unknown error')}")
        sys.exit(1)

if __name__ == "__main__":
    main()
