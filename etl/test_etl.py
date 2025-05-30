"""Test the REUNI ETL locally"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from etl.scripts.load_reuni_data import ReuniETL

# Test with local file
if __name__ == "__main__":
    # Adjust path to your Excel file
    excel_path = "../REUNI_Operações_Novo_PAC_OGU_Interno_CAIXA_21052025.xlsx"
    
    # Use the same database URL as Docker
    db_url = "postgresql://pac_user:pac_password@localhost:5433/pac_mcmv"
    
    etl = ReuniETL(excel_path, db_url)
    etl.run()
