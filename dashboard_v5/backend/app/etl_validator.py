"""
ETL Validation Module
Prevents data quality issues during ETL process
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ETLValidator:
    """Validates data during ETL to prevent quality issues"""
    
    def __init__(self):
        self.validation_errors = []
        self.validation_warnings = []
        
    def validate_dados_prioritarios(self, df: pd.DataFrame) -> bool:
        """Validate dados_prioritarios data before loading"""
        self.validation_errors = []
        self.validation_warnings = []
        
        # Required columns
        required_columns = [
            'apf', 'nome_empreendimento', 'modalidade', 'sg_uf', 
            'municipio', 'data_movimento'
        ]
        
        # Check required columns
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            self.validation_errors.append(f"Missing required columns: {missing_cols}")
            return False
        
        # Validate modalidade values
        valid_modalidades = {'FAR', 'FDS', 'RURAL'}
        invalid_modalidades = df[~df['modalidade'].isin(valid_modalidades)]['modalidade'].unique()
        if len(invalid_modalidades) > 0:
            # Auto-fix Entidades -> FDS
            if 'Entidades' in invalid_modalidades:
                df.loc[df['modalidade'] == 'Entidades', 'modalidade'] = 'FDS'
                self.validation_warnings.append("Auto-fixed: 'Entidades' -> 'FDS'")
                invalid_modalidades = [m for m in invalid_modalidades if m != 'Entidades']
            
            if len(invalid_modalidades) > 0:
                self.validation_errors.append(f"Invalid modalidade values: {invalid_modalidades}")
        
        # Validate UH fields
        if 'uh_original_contratadas' in df.columns and 'uh_contratadas' in df.columns:
            # Auto-fix zero uh_contratadas
            zero_uh_mask = (df['uh_contratadas'] == 0) & (df['uh_original_contratadas'] > 0)
            if zero_uh_mask.any():
                df.loc[zero_uh_mask, 'uh_contratadas'] = df.loc[zero_uh_mask, 'uh_original_contratadas']
                self.validation_warnings.append(
                    f"Auto-fixed: {zero_uh_mask.sum()} records with zero uh_contratadas"
                )
        
        # Check for encoding issues
        encoding_issues = df['municipio'].str.contains('Ã|Â', na=False).sum()
        if encoding_issues > 0:
            # Auto-fix common encoding issues
            df['municipio'] = self.fix_encoding(df['municipio'])
            df['nome_empreendimento'] = self.fix_encoding(df['nome_empreendimento'])
            self.validation_warnings.append(
                f"Auto-fixed: {encoding_issues} records with encoding issues"
            )
        
        # Trim whitespace
        text_columns = ['municipio', 'nome_empreendimento', 'sg_uf']
        for col in text_columns:
            if col in df.columns:
                # Remove extra spaces and trim
                df[col] = df[col].str.replace(r'\s+', ' ', regex=True).str.strip()
        
        # Validate dates
        if 'data_movimento' in df.columns:
            df['data_movimento'] = pd.to_datetime(df['data_movimento'], errors='coerce')
            invalid_dates = df['data_movimento'].isna().sum()
            if invalid_dates > 0:
                self.validation_errors.append(f"Invalid data_movimento: {invalid_dates} records")
        
        # Validate coordinates if present
        if 'latitude' in df.columns and 'longitude' in df.columns:
            # Check valid ranges
            invalid_lat = ((df['latitude'] < -90) | (df['latitude'] > 90)).sum()
            invalid_lon = ((df['longitude'] < -180) | (df['longitude'] > 180)).sum()
            
            if invalid_lat > 0:
                self.validation_warnings.append(f"Invalid latitude values: {invalid_lat} records")
            if invalid_lon > 0:
                self.validation_warnings.append(f"Invalid longitude values: {invalid_lon} records")
        
        # Check for logical inconsistencies
        if 'uh_entregues' in df.columns and 'uh_contratadas' in df.columns:
            delivery_exceeds = (df['uh_entregues'] > df['uh_contratadas']).sum()
            if delivery_exceeds > 0:
                self.validation_warnings.append(
                    f"Delivery exceeds contracted: {delivery_exceeds} records"
                )
        
        # Log results
        if self.validation_errors:
            logger.error(f"Validation errors: {self.validation_errors}")
        if self.validation_warnings:
            logger.warning(f"Validation warnings: {self.validation_warnings}")
        
        return len(self.validation_errors) == 0
    
    def fix_encoding(self, series: pd.Series) -> pd.Series:
        """Fix common encoding issues in text"""
        if series is None or series.empty:
            return series
        
        encoding_map = {
            'Ã§': 'ç', 'Ã£': 'ã', 'Ã¡': 'á', 'Ã¢': 'â', 'Ã©': 'é',
            'Ãª': 'ê', 'Ã­': 'í', 'Ã³': 'ó', 'Ã´': 'ô', 'Ãµ': 'õ',
            'Ãº': 'ú', 'Ã‡': 'Ç', 'Ãƒ': 'Ã', 'Ã': 'Á', 'Ã‚': 'Â',
            'Ã‰': 'É', 'ÃŠ': 'Ê', 'Ã"': 'Ó', 'Ã"': 'Ô', 'Ã•': 'Õ',
            'Â ': ' ', 'Â': ''
        }
        
        result = series.copy()
        for wrong, correct in encoding_map.items():
            result = result.str.replace(wrong, correct, regex=False)
        
        return result
    
    def validate_projetos(self, df: pd.DataFrame) -> bool:
        """Validate projetos data before loading"""
        self.validation_errors = []
        self.validation_warnings = []
        
        # Required columns
        required_columns = [
            'nu_apf', 'no_empreendimento', 'programa', 'sg_uf', 
            'no_municipio', 'dt_contratacao'
        ]
        
        # Check required columns
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            self.validation_errors.append(f"Missing required columns: {missing_cols}")
            return False
        
        # Validate program values
        valid_programs = {'FAR', 'FDS', 'RURAL'}
        invalid_programs = df[~df['programa'].isin(valid_programs)]['programa'].unique()
        if len(invalid_programs) > 0:
            self.validation_errors.append(f"Invalid program values: {invalid_programs}")
        
        # Validate dates
        date_columns = ['dt_contratacao', 'dt_inicio_obra', 'dt_previsao_conclusao_obra']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
                invalid_dates = df[col].isna().sum()
                if invalid_dates > 0 and col == 'dt_contratacao':
                    self.validation_errors.append(f"Invalid {col}: {invalid_dates} records")
                elif invalid_dates > 0:
                    self.validation_warnings.append(f"Invalid {col}: {invalid_dates} records")
        
        # Check date logic
        if all(col in df.columns for col in ['dt_contratacao', 'dt_inicio_obra']):
            start_before_contract = (
                df['dt_inicio_obra'].notna() & 
                df['dt_contratacao'].notna() &
                (df['dt_inicio_obra'] < df['dt_contratacao'])
            ).sum()
            if start_before_contract > 0:
                self.validation_warnings.append(
                    f"Start date before contract: {start_before_contract} records"
                )
        
        # Validate financial values
        financial_columns = ['vr_total_operacao', 'vr_total_investimento']
        for col in financial_columns:
            if col in df.columns:
                negative_values = (df[col] < 0).sum()
                if negative_values > 0:
                    self.validation_errors.append(f"Negative {col}: {negative_values} records")
        
        # Check financial logic
        if 'vr_total_investimento' in df.columns and 'vr_total_operacao' in df.columns:
            investment_exceeds = (
                df['vr_total_investimento'] > df['vr_total_operacao']
            ).sum()
            if investment_exceeds > 0:
                self.validation_warnings.append(
                    f"Investment exceeds operation: {investment_exceeds} records"
                )
        
        # Validate progress percentage
        if 'pc_obra_realizada' in df.columns:
            invalid_progress = (
                (df['pc_obra_realizada'] < 0) | (df['pc_obra_realizada'] > 100)
            ).sum()
            if invalid_progress > 0:
                self.validation_errors.append(
                    f"Invalid progress percentage: {invalid_progress} records"
                )
        
        return len(self.validation_errors) == 0
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get validation summary"""
        return {
            'errors': self.validation_errors,
            'warnings': self.validation_warnings,
            'has_errors': len(self.validation_errors) > 0,
            'timestamp': datetime.now().isoformat()
        }