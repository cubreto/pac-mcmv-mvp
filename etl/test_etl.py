"""Test the REUNI ETL locally"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from etl.scripts.load_reuni_data import ReuniETL

# Test with local file
if __name__ == "__main__":
    # Path to Excel file in data/raw directory
    excel_path = "data/raw/REUNI_Operações_Novo_PAC_OGU_Interno_CAIXA_21-05-2025.xlsx"
    
    # Try different connection options
    # Option 1: Using Docker service name (when running inside Docker network)
    # db_url = "postgresql://pac_user:pac_password@db:5432/pac_mcmv"
    
    # Option 2: Using localhost with mapped port (when running from host)
    db_url = "postgresql://pac_user:pac_password@localhost:5432/pac_mcmv"
    
    print(f"📂 Looking for Excel file at: {os.path.abspath(excel_path)}")
    print(f"🔌 Connecting to database: {db_url}")
    
    if not os.path.exists(excel_path):
        print("❌ Excel file not found! Please place it in data/raw/")
        print(f"   Expected location: {os.path.abspath(excel_path)}")
        sys.exit(1)
    
    etl = ReuniETL(excel_path, db_url)
    etl.run()
