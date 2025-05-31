# Data Directory

## Structure

- `raw/` - Original data files from CAIXA (Excel, CSV, etc.)
- `processed/` - Transformed data ready for analysis

## Required Files

### REUNI Excel File
Place the REUNI Excel file in the `raw/` directory:
data/raw/REUNI_Operações_Novo_PAC_OGU_Interno_CAIXA_21-05-2025.xlsx

This file contains:
- 4,899 PAC operations
- 78 columns of data
- Latest update from CAIXA system (21/05/2025)

### How to obtain the file
1. Access CAIXA's REUNI system
2. Export the full operations report
3. Save as Excel format
4. Copy to `data/raw/` directory

## Running the ETL

After placing the Excel file, run:
```bash
./run_etl.sh
Or manually:
bashpython etl/test_etl.py
