"""
Unified loader for all three MCMV programs (FAR, FDS, RURAL).
Concatenates the 'principal' DataFrames into a Master Proposals table.
"""
import logging
import pandas as pd
from pathlib import Path

from .far_loader import FARLoader
from .fds_loader import FDSLoader
from .rural_loader import RURALLoader

logger = logging.getLogger(__name__)

class UnifiedMCMVLoader:
    """Loader that consolidates FAR, FDS and RURAL into a single 'master_df'"""
    
    def __init__(self, base_folder):
        """
        base_folder: path to 'data/mcmv/HIS'
        """
        self.base_folder = Path(base_folder)
        self.far_path = self.base_folder / 'FAR.xlsx'
        self.fds_path = self.base_folder / 'FDS.xlsx'
        self.rural_path = self.base_folder / 'RURAL.xlsx'
        
        self.master_df = None
        self.all_data = {}
        
    def load_all(self):
        """Load and concatenate all 'principal' from FAR, FDS and RURAL"""
        dfs = []
        
        # 1) Load FAR
        if self.far_path.exists():
            logger.info("Loading FAR...")
            far_loader = FARLoader(self.far_path)
            far_data = far_loader.load_and_validate()
            if far_data and far_data.get('principal') is not None:
                dfs.append(far_data['principal'])
                self.all_data['FAR'] = far_data
            else:
                logger.warning("Failed to load FAR principal")
        else:
            logger.warning(f"FAR.xlsx not found at {self.far_path}")
            
        # 2) Load FDS
        if self.fds_path.exists():
            logger.info("Loading FDS...")
            fds_loader = FDSLoader(self.fds_path)
            fds_data = fds_loader.load_and_validate()
            if fds_data and fds_data.get('principal') is not None:
                dfs.append(fds_data['principal'])
                self.all_data['FDS'] = fds_data
            else:
                logger.warning("Failed to load FDS principal")
        else:
            logger.warning(f"FDS.xlsx not found at {self.fds_path}")
            
        # 3) Load RURAL
        if self.rural_path.exists():
            logger.info("Loading RURAL...")
            rural_loader = RURALLoader(self.rural_path)
            rural_data = rural_loader.load_and_validate()
            if rural_data and rural_data.get('principal') is not None:
                dfs.append(rural_data['principal'])
                self.all_data['RURAL'] = rural_data
            else:
                logger.warning("Failed to load RURAL principal")
        else:
            logger.warning(f"RURAL.xlsx not found at {self.rural_path}")
            
        # Concatenate all principal DataFrames
        if dfs:
            self.master_df = pd.concat(dfs, axis=0, ignore_index=True)
            logger.info(f"Master proposals loaded: {len(self.master_df)} total rows")
            
            # Log breakdown by program
            program_counts = self.master_df['program_code'].value_counts()
            for prog, count in program_counts.items():
                logger.info(f"  {prog}: {count} projects")
        else:
            logger.error("No DataFrames to concatenate. Master_df is empty.")
            
        return self.master_df
    
    def get_summary(self):
        """Get summary statistics of the unified data"""
        if self.master_df is None:
            return None
            
        summary = {
            'total_projects': len(self.master_df),
            'by_program': self.master_df['program_code'].value_counts().to_dict(),
            'by_state': self.master_df['SG_UF'].value_counts().to_dict(),
            'total_expected_units': {
                'FAR': 133440,
                'FDS': 24606,
                'RURAL': 30729,
                'TOTAL': 188775
            }
        }
        
        return summary
