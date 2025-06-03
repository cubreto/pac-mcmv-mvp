"""
Base loader class for MCMV programs
"""
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from .domain_lookups import BUILDING_TYPES, STATE_CODES, RECORD_TYPES, PROGRAMS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCMVBaseLoader:
    """Base class for all MCMV program loaders"""
    
    def __init__(self, file_path, program_code):
        self.file_path = Path(file_path)
        self.program_code = program_code
        self.program_name = PROGRAMS.get(program_code, program_code)
        self.principal_df = None
        self.sheets = {}
        
    def validate_nu_apf(self, df):
        """Validate NU_APF is 8 digits"""
        invalid = ~df['NU_APF'].astype(str).str.match(r'^\d{8}$')
        if invalid.any():
            logger.warning(f"Found {invalid.sum()} invalid NU_APF values")
            return False
        return True
    
    def validate_dates(self, df, date_columns):
        """Validate date formats"""
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], format='%d/%m/%Y', errors='coerce')
        return df
    
    def apply_lookups(self, df):
        """Apply domain lookups to coded fields"""
        if 'CO_TIPO_EDIFICACAO' in df.columns:
            df['building_type_name'] = df['CO_TIPO_EDIFICACAO'].map(BUILDING_TYPES)
        
        if 'SG_UF' in df.columns:
            df['state_name'] = df['SG_UF'].map(STATE_CODES)
            
        if 'CO_TIPO_REGISTRO' in df.columns:
            df['record_type_name'] = df['CO_TIPO_REGISTRO'].map(RECORD_TYPES)
            
        return df
    
    def load_all_sheets(self):
        """Load all sheets from Excel file"""
        try:
            excel_file = pd.ExcelFile(self.file_path)
            logger.info(f"Loading {self.program_code} from {self.file_path.name}")
            logger.info(f"Found sheets: {excel_file.sheet_names}")
            
            for sheet_name in excel_file.sheet_names:
                self.sheets[sheet_name] = pd.read_excel(excel_file, sheet_name=sheet_name)
                logger.info(f"  {sheet_name}: {len(self.sheets[sheet_name])} rows")
                
            return True
        except Exception as e:
            logger.error(f"Error loading {self.program_code}: {e}")
            return False
