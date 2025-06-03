"""
FAR (Fundo de Arrendamento Residencial) loader
"""
from .base_loader import MCMVBaseLoader
import logging

logger = logging.getLogger(__name__)

class FARLoader(MCMVBaseLoader):
    """Loader for FAR program data"""
    
    def __init__(self, file_path):
        super().__init__(file_path, 'FAR')
        
    def load_and_validate(self):
        """Load and validate FAR data"""
        if not self.load_all_sheets():
            return None
            
        # Get principal sheet - FAR uses HISTB010_MONITORAMENTO_CADASTRO
        self.principal_df = self.sheets.get('HISTB010_MONITORAMENTO_CADASTRO')
        
        if self.principal_df is None:
            logger.error("HISTB010_MONITORAMENTO_CADASTRO sheet not found")
            return None
            
        # Validate NU_APF
        if not self.validate_nu_apf(self.principal_df):
            logger.warning("NU_APF validation failed, continuing anyway")
            
        # Validate dates
        date_columns = ['DT_MOVIMENTO', 'DT_APRESENTACAO_ORCAMENTO']
        self.principal_df = self.validate_dates(self.principal_df, date_columns)
        
        # Apply lookups
        self.principal_df = self.apply_lookups(self.principal_df)
        
        # Add program identifier
        self.principal_df['program_code'] = self.program_code
        self.principal_df['program_name'] = self.program_name
        
        # Log summary
        logger.info(f"FAR Summary:")
        logger.info(f"  Total projects: {len(self.principal_df)}")
        logger.info(f"  Expected units: 133,440")
        
        if 'CO_TIPO_EDIFICACAO' in self.principal_df.columns:
            building_dist = self.principal_df['building_type_name'].value_counts()
            logger.info(f"  Building types: {building_dist.to_dict()}")
            
        return {
            'principal': self.principal_df,
            'obra': self.sheets.get('HISTB012_MOVIMENTO_OBRA'),
            'pts': self.sheets.get('HISTB013_EXEC_TS'),  # FAR doesn't have this
            'pf': self.sheets.get('HISTB009_MONITORAMENTO_PF')  # FAR doesn't have this
        }
