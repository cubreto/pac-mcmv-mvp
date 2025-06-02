#!/usr/bin/env python3
"""
Base loader for MCMV data - common functionality
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from abc import ABC, abstractmethod

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCMVBaseLoader(ABC):
    """Base class for MCMV data loaders"""
    
    def __init__(self, file_path):
        self.file_path = Path(file_path)
        self.df = None
        
    @abstractmethod
    def load_data(self):
        """Load data from Excel file"""
        pass
        
    @abstractmethod
    def transform_data(self):
        """Transform data to database schema"""
        pass
        
    def clean_numeric_fields(self, df, fields):
        """Clean numeric fields"""
        for field in fields:
            if field in df.columns:
                df[field] = pd.to_numeric(df[field], errors='coerce')
        return df
        
    def clean_date_fields(self, df, fields):
        """Clean date fields"""
        for field in fields:
            if field in df.columns:
                df[field] = pd.to_datetime(df[field], errors='coerce')
        return df
        
    def clean_text_fields(self, df, fields):
        """Clean text fields"""
        for field in fields:
            if field in df.columns:
                df[field] = df[field].astype(str).str.strip()
                df[field] = df[field].replace('nan', '')
        return df
        
    def validate_uf(self, df):
        """Validate UF codes"""
        valid_ufs = {
            'AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 
            'MA', 'MG', 'MS', 'MT', 'PA', 'PB', 'PE', 'PI', 'PR', 
            'RJ', 'RN', 'RO', 'RR', 'RS', 'SC', 'SE', 'SP', 'TO'
        }
        if 'uf' in df.columns:
            df['uf'] = df['uf'].str.upper()
            df = df[df['uf'].isin(valid_ufs)]
        return df
