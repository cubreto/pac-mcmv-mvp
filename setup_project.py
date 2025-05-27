#!/usr/bin/env python3
"""
PAC-MCMV MVP Project Generator with Docker & Database Strategy
- Docker setup for easy development and deployment
- PostgreSQL database for production-ready data storage
- ETL pipeline for PAC + Habitação data combination
- Faker data generator for Habitação placeholder
"""

import os
import sys
from pathlib import Path

def create_directory_structure():
    """Create project directory structure with Docker support"""
    directories = [
        "data",
        "streamlit_app", 
        "etl",
        "database",
        "database/migrations",
        "tests"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {directory}")

def create_files():
    """Create all project files with Docker and database support"""
    
    files = {
        # Root level files
        "README.md": """# PAC-MCMV MVP - Production Ready

Análise da "Situação Atual" com estratégia de banco de dados e containerização.

## 🏗️ Arquitetura

```
├── PostgreSQL     # Database (PAC + Habitação unified)
├── ETL Pipeline   # Excel → Database transformation
├── Streamlit App  # Dashboard (reads from database)
└── Docker         # Containerization
```

## 🚀 Quick Start

### Development (Mac)
```bash
# 1. Start database
docker-compose up -d db

# 2. Run ETL (load sample data)
python etl/run_etl.py

# 3. Start dashboard
streamlit run streamlit_app/dashboard.py
```

### Production (Docker)
```bash
# Start everything
docker-compose up --build

# Access dashboard
open http://localhost:8501
```

## 📊 Data Strategy

- **Single unified table**: `projeto_status`
- **Combined PAC + Habitação** data in one view
- **ETL handles data transformation** from Excel files
- **Dashboard reads only from database** (no file uploads)

## 🎯 MVP Focus

Simple analysis of "Situação Atual" field:
- Problem categorization
- Delay detection  
- Geographic distribution
- Executive-friendly dashboards

*Ready for AWS deployment*
""",

        "docker-compose.yml": """version: '3.8'

services:
  db:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: pac_mcmv
      POSTGRES_USER: pac_user
      POSTGRES_PASSWORD: pac_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/01-init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U pac_user -d pac_mcmv"]
      interval: 30s
      timeout: 10s
      retries: 3

  streamlit:
    build: .
    restart: unless-stopped
    environment:
      DATABASE_URL: postgresql://pac_user:pac_password@db:5432/pac_mcmv
    depends_on:
      db:
        condition: service_healthy
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data:ro

volumes:
  postgres_data:
""",

        "Dockerfile": """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "streamlit_app/dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
""",

        "requirements.txt": """streamlit==1.28.1
pandas==2.1.3
plotly==5.17.0
psycopg2-binary==2.9.9
sqlalchemy==2.0.23
openpyxl==3.1.2
numpy==1.25.2
nltk==3.8.1
textblob==0.17.1
scikit-learn==1.3.2
faker==19.12.0
python-dotenv==1.0.0
""",

        ".env.example": """# Database Configuration
DATABASE_URL=postgresql://pac_user:pac_password@localhost:5432/pac_mcmv

# Development settings
DEBUG=true
""",

        ".gitignore": """data/*.xlsx
data/*.xls  
data/*.csv
__pycache__/
*.pyc
.DS_Store
.env
.vscode/
.idea/
postgres_data/
""",

        # Database schema
        "database/init.sql": """-- PAC-MCMV Unified Database Schema
-- Single table strategy for MVP simplicity

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Unified project status table
CREATE TABLE IF NOT EXISTS projeto_status (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Basic project info
    proposta VARCHAR(100),
    uf CHAR(2) NOT NULL,
    municipio_beneficiado VARCHAR(255),
    
    -- Program identification
    programa VARCHAR(255) NOT NULL,
    tipo_programa VARCHAR(20) CHECK (tipo_programa IN ('PAC', 'HABITACAO')),
    
    -- Financial data
    valor_repasse DECIMAL(15,2),
    valor_investimento DECIMAL(15,2),
    valor_empenhado DECIMAL(15,2),
    valor_pago DECIMAL(15,2),
    
    -- Progress tracking
    percentual_obra_realizado DECIMAL(5,2),
    data_inicio_obra DATE,
    
    -- Key field for analysis
    situacao_atual TEXT NOT NULL,
    data_atualizacao_situacao DATE,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes for performance
    CONSTRAINT valid_percentage CHECK (percentual_obra_realizado >= 0 AND percentual_obra_realizado <= 100)
);

-- Indexes for common queries
CREATE INDEX idx_projeto_uf ON projeto_status(uf);
CREATE INDEX idx_projeto_programa ON projeto_status(programa);
CREATE INDEX idx_projeto_tipo ON projeto_status(tipo_programa);
CREATE INDEX idx_situacao_text ON projeto_status USING gin(to_tsvector('portuguese', situacao_atual));

-- View for dashboard queries (optional optimization)
CREATE OR REPLACE VIEW dashboard_summary AS
SELECT 
    uf,
    tipo_programa,
    COUNT(*) as total_projetos,
    SUM(valor_repasse) as valor_total,
    AVG(percentual_obra_realizado) as progresso_medio,
    COUNT(CASE WHEN situacao_atual ~* 'atras|problem|pendente|paralis' THEN 1 END) as projetos_problema
FROM projeto_status 
GROUP BY uf, tipo_programa;

-- Update trigger for metadata
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_projeto_status_modtime 
    BEFORE UPDATE ON projeto_status 
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();
""",

        # ETL Pipeline
        "etl/database.py": """#!/usr/bin/env python3
\"\"\"
Database connection and operations for PAC-MCMV MVP
\"\"\"

import os
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, database_url=None):
        self.database_url = database_url or os.getenv('DATABASE_URL', 
            'postgresql://pac_user:pac_password@localhost:5432/pac_mcmv')
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def test_connection(self):
        \"\"\"Test database connection\"\"\"
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                logger.info("Database connection successful")
                return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def execute_query(self, query, params=None):
        \"\"\"Execute a raw SQL query\"\"\"
        with self.engine.connect() as conn:
            return conn.execute(text(query), params or {})
    
    def load_dataframe(self, query, params=None):
        \"\"\"Load data into pandas DataFrame\"\"\"
        return pd.read_sql(query, self.engine, params=params)
    
    def save_dataframe(self, df, table_name, if_exists='replace'):
        \"\"\"Save DataFrame to database\"\"\"
        df.to_sql(table_name, self.engine, if_exists=if_exists, index=False, method='multi')
        logger.info(f"Saved {len(df)} records to {table_name}")
    
    def get_projeto_count(self):
        \"\"\"Get total project count\"\"\"
        query = "SELECT COUNT(*) as total FROM projeto_status"
        result = self.load_dataframe(query)
        return result['total'].iloc[0]
    
    def get_projects_by_state(self):
        \"\"\"Get project summary by state\"\"\"
        query = \"\"\"
        SELECT 
            uf,
            COUNT(*) as total_projetos,
            COUNT(CASE WHEN situacao_atual ~* 'atras|problem|pendente|paralis' THEN 1 END) as projetos_problema,
            AVG(percentual_obra_realizado) as progresso_medio
        FROM projeto_status 
        GROUP BY uf 
        ORDER BY total_projetos DESC
        \"\"\"
        return self.load_dataframe(query)
    
    def get_all_projects(self):
        \"\"\"Get all projects for analysis\"\"\"
        query = \"\"\"
        SELECT 
            proposta, uf, municipio_beneficiado, programa, tipo_programa,
            valor_repasse, percentual_obra_realizado, situacao_atual,
            data_atualizacao_situacao
        FROM projeto_status 
        ORDER BY created_at DESC
        \"\"\"
        return self.load_dataframe(query)

if __name__ == "__main__":
    # Test database connection
    db = DatabaseManager()
    if db.test_connection():
        print("✅ Database connection successful")
        try:
            count = db.get_projeto_count()
            print(f"📊 Total projects in database: {count}")
        except Exception as e:
            print(f"⚠️ No data yet (expected for fresh setup): {e}")
    else:
        print("❌ Database connection failed")
""",

        "etl/fake_data_generator.py": """#!/usr/bin/env python3
\"\"\"
Generate fake data for PAC and Habitação programs
Used as placeholder until real Habitação data arrives
\"\"\"

import pandas as pd
import numpy as np
from faker import Faker
from faker.providers import BaseProvider
import random
from datetime import datetime, timedelta

fake = Faker('pt_BR')

class PACProvider(BaseProvider):
    \"\"\"Custom provider for PAC/MCMV specific data\"\"\"
    
    pac_programs = [
        "Construção de Hospitais e UBS",
        "Pavimentação de Vias Urbanas", 
        "Construção de Escolas",
        "Saneamento Básico",
        "Construção de Pontes",
        "Drenagem Urbana",
        "Energia Elétrica Rural",
        "Abastecimento de Água"
    ]
    
    habitacao_programs = [
        "Minha Casa Minha Vida - Faixa 1",
        "Minha Casa Minha Vida - Faixa 2", 
        "Minha Casa Minha Vida - Faixa 3",
        "Casa Verde e Amarela",
        "Regularização Fundiária",
        "Urbanização de Assentamentos",
        "Habitação Rural",
        "Reabilitação de Áreas Centrais"
    ]
    
    situacao_templates = {
        'normal': [
            "Obra em execução conforme cronograma estabelecido",
            "Projeto aprovado e em fase de licitação",
            "Execução dentro do prazo previsto", 
            "Obra concluída e entregue à população",
            "Em processo de medição de obra executada",
            "Aguardando vistoria técnica para liberação"
        ],
        'problema_recursos': [
            "Obra paralisada por falta de recursos financeiros",
            "Aguardando liberação de verba para continuidade",
            "Cronograma atrasado devido atraso no repasse",
            "Suspensa temporariamente por contingenciamento orçamentário"
        ],
        'problema_documentacao': [
            "Pendente documentação técnica para aprovação",
            "Aguardando regularização documental do terreno",
            "Falta de certidões necessárias para prosseguimento",
            "Documentação em análise pelos órgãos competentes"
        ],
        'problema_ambiental': [
            "Aguardando licenciamento ambiental do IBAMA",
            "Pendente parecer técnico ambiental",
            "Em processo de compensação ambiental",
            "Suspenso para adequação às normas ambientais"
        ],
        'problema_tecnico': [
            "Obra paralisada por problemas técnicos no projeto",
            "Necessária revisão das especificações técnicas",
            "Aguardando aprovação de projeto executivo",
            "Em adequação às normas técnicas vigentes"
        ]
    }
    
    def pac_programa(self):
        return self.random_element(self.pac_programs)
    
    def habitacao_programa(self):
        return self.random_element(self.habitacao_programs)
    
    def situacao_atual(self):
        # 60% normal, 40% problems
        if random.random() < 0.6:
            category = 'normal'
        else:
            category = random.choice(['problema_recursos', 'problema_documentacao', 
                                    'problema_ambiental', 'problema_tecnico'])
        
        return self.random_element(self.situacao_templates[category])

fake.add_provider(PACProvider)

def generate_pac_data(n_records=500):
    \"\"\"Generate fake PAC data\"\"\"
    
    records = []
    brazilian_states = [
        'AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 
        'MA', 'MG', 'MS', 'MT', 'PA', 'PB', 'PE', 'PI', 'PR', 
        'RJ', 'RN', 'RO', 'RR', 'RS', 'SC', 'SE', 'SP', 'TO'
    ]
    
    for _ in range(n_records):
        uf = random.choice(brazilian_states)
        
        record = {
            'proposta': f"PAC-{fake.random_int(10000, 99999)}",
            'uf': uf,
            'municipio_beneficiado': fake.city(),
            'programa': fake.pac_programa(),
            'tipo_programa': 'PAC',
            'valor_repasse': round(random.uniform(100000, 50000000), 2),
            'valor_investimento': round(random.uniform(150000, 60000000), 2),
            'valor_empenhado': round(random.uniform(50000, 45000000), 2),
            'valor_pago': round(random.uniform(10000, 40000000), 2),
            'percentual_obra_realizado': round(random.uniform(0, 100), 1),
            'data_inicio_obra': fake.date_between(start_date='-2y', end_date='today'),
            'situacao_atual': fake.situacao_atual(),
            'data_atualizacao_situacao': fake.date_between(start_date='-6m', end_date='today')
        }
        
        records.append(record)
    
    return pd.DataFrame(records)

def generate_habitacao_data(n_records=300):
    \"\"\"Generate fake Habitação data\"\"\"
    
    records = []
    brazilian_states = [
        'AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 
        'MA', 'MG', 'MS', 'MT', 'PA', 'PB', 'PE', 'PI', 'PR', 
        'RJ', 'RN', 'RO', 'RR', 'RS', 'SC', 'SE', 'SP', 'TO'
    ]
    
    for _ in range(n_records):
        uf = random.choice(brazilian_states)
        
        record = {
            'proposta': f"HAB-{fake.random_int(10000, 99999)}",
            'uf': uf,
            'municipio_beneficiado': fake.city(),
            'programa': fake.habitacao_programa(),
            'tipo_programa': 'HABITACAO',
            'valor_repasse': round(random.uniform(50000, 20000000), 2),
            'valor_investimento': round(random.uniform(80000, 25000000), 2),
            'valor_empenhado': round(random.uniform(30000, 18000000), 2),
            'valor_pago': round(random.uniform(5000, 15000000), 2),
            'percentual_obra_realizado': round(random.uniform(0, 100), 1),
            'data_inicio_obra': fake.date_between(start_date='-2y', end_date='today'),
            'situacao_atual': fake.situacao_atual(),
            'data_atualizacao_situacao': fake.date_between(start_date='-6m', end_date='today')
        }
        
        records.append(record)
    
    return pd.DataFrame(records)

def generate_combined_dataset(pac_records=500, habitacao_records=300):
    \"\"\"Generate combined PAC + Habitação dataset\"\"\"
    
    print(f"Generating {pac_records} PAC records...")
    pac_df = generate_pac_data(pac_records)
    
    print(f"Generating {habitacao_records} Habitação records...")
    habitacao_df = generate_habitacao_data(habitacao_records)
    
    # Combine datasets
    combined_df = pd.concat([pac_df, habitacao_df], ignore_index=True)
    
    print(f"✅ Generated {len(combined_df)} total records")
    print(f"   - PAC: {len(pac_df)} records")
    print(f"   - Habitação: {len(habitacao_df)} records")
    
    return combined_df

if __name__ == "__main__":
    # Generate sample data
    df = generate_combined_dataset()
    
    # Save to CSV for inspection
    df.to_csv('data/sample_combined_data.csv', index=False)
    print("Sample data saved to data/sample_combined_data.csv")
    
    # Show sample
    print("\\nSample records:")
    print(df[['proposta', 'uf', 'programa', 'tipo_programa', 'situacao_atual']].head())
""",

        "etl/excel_loader.py": """#!/usr/bin/env python3
\"\"\"
Excel data loader for real PAC data
Transforms Excel format to database schema
\"\"\"

import pandas as pd
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_pac_excel(file_path):
    \"\"\"Load PAC data from Excel file\"\"\"
    
    # Try different sheet names
    sheet_names = ["Analítico Proposta", "Sheet1", "Dados", "PAC"]
    
    df = None
    for sheet in sheet_names:
        try:
            df = pd.read_excel(file_path, sheet_name=sheet)
            logger.info(f"Successfully loaded sheet: {sheet}")
            break
        except:
            continue
    
    if df is None:
        df = pd.read_excel(file_path)  # Load first sheet
        logger.info("Loaded first sheet by default")
    
    return df

def transform_pac_data(df):
    \"\"\"Transform Excel PAC data to database schema\"\"\"
    
    # Column mapping from Excel to database schema
    column_mapping = {
        'Proposta': 'proposta',
        'UF': 'uf', 
        'Município Beneficiado': 'municipio_beneficiado',
        'Programa': 'programa',
        'Valor Repasse': 'valor_repasse',
        'Valor Investimento': 'valor_investimento', 
        'Valor Empenhado': 'valor_empenhado',
        'Valor Pago C.Convênio': 'valor_pago',
        'Percentual de obra realizado': 'percentual_obra_realizado',
        'Data início de Obra': 'data_inicio_obra',
        'Situação Atual': 'situacao_atual',
        'Data atualização da Situação Atual': 'data_atualizacao_situacao'
    }
    
    # Find available columns (case-insensitive)
    available_mapping = {}
    df_columns_lower = {col.lower(): col for col in df.columns}
    
    for excel_col, db_col in column_mapping.items():
        excel_col_lower = excel_col.lower()
        if excel_col_lower in df_columns_lower:
            available_mapping[df_columns_lower[excel_col_lower]] = db_col
        elif excel_col in df.columns:
            available_mapping[excel_col] = db_col
    
    logger.info(f"Found {len(available_mapping)} matching columns")
    
    # Select and rename columns
    df_transformed = df[list(available_mapping.keys())].copy()
    df_transformed = df_transformed.rename(columns=available_mapping)
    
    # Add required fields
    df_transformed['tipo_programa'] = 'PAC'
    
    # Clean data
    df_transformed = clean_transformed_data(df_transformed)
    
    logger.info(f"Transformed {len(df_transformed)} PAC records")
    return df_transformed

def clean_transformed_data(df):
    \"\"\"Clean and validate transformed data\"\"\"
    
    # Remove rows without situacao_atual
    df = df.dropna(subset=['situacao_atual'])
    df = df[df['situacao_atual'].astype(str).str.strip() != '']
    
    # Clean numeric fields
    numeric_fields = ['valor_repasse', 'valor_investimento', 'valor_empenhado', 
                     'valor_pago', 'percentual_obra_realizado']
    
    for field in numeric_fields:
        if field in df.columns:
            df[field] = pd.to_numeric(df[field], errors='coerce')
    
    # Clean date fields
    date_fields = ['data_inicio_obra', 'data_atualizacao_situacao']
    
    for field in date_fields:
        if field in df.columns:
            df[field] = pd.to_datetime(df[field], errors='coerce')
    
    # Clean text fields
    text_fields = ['proposta', 'uf', 'municipio_beneficiado', 'programa', 'situacao_atual']
    
    for field in text_fields:
        if field in df.columns:
            df[field] = df[field].astype(str).str.strip()
    
    # Validate UF format
    if 'uf' in df.columns:
        df['uf'] = df['uf'].str.upper()
        valid_ufs = {
            'AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 
            'MA', 'MG', 'MS', 'MT', 'PA', 'PB', 'PE', 'PI', 'PR', 
            'RJ', 'RN', 'RO', 'RR', 'RS', 'SC', 'SE', 'SP', 'TO'
        }
        df = df[df['uf'].isin(valid_ufs)]
    
    # Ensure required fields are present
    required_fields = ['uf', 'situacao_atual', 'tipo_programa']
    missing_fields = [field for field in required_fields if field not in df.columns]
    
    if missing_fields:
        raise ValueError(f"Missing required fields: {missing_fields}")
    
    logger.info(f"Cleaned data: {len(df)} valid records")
    return df

def process_excel_files(data_dir="data"):
    \"\"\"Process all Excel files in data directory\"\"\"
    
    data_path = Path(data_dir)
    excel_files = list(data_path.glob("*.xlsx")) + list(data_path.glob("*.xls"))
    
    if not excel_files:
        raise FileNotFoundError(f"No Excel files found in {data_dir}")
    
    all_dataframes = []
    
    for file_path in excel_files:
        logger.info(f"Processing {file_path}")
        try:
            df = load_pac_excel(file_path)
            df_transformed = transform_pac_data(df)
            all_dataframes.append(df_transformed)
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            continue
    
    if not all_dataframes:
        raise ValueError("No valid data could be loaded from Excel files")
    
    # Combine all dataframes
    combined_df = pd.concat(all_dataframes, ignore_index=True)
    logger.info(f"Combined {len(combined_df)} total records from {len(all_dataframes)} files")
    
    return combined_df

if __name__ == "__main__":
    try:
        df = process_excel_files()
        print(f"✅ Loaded {len(df)} records")
        print("Sample data:")
        print(df[['proposta', 'uf', 'programa', 'situacao_atual']].head())
    except Exception as e:
        print(f"❌ Error: {e}")
""",

        "etl/run_etl.py": """#!/usr/bin/env python3
\"\"\"
Main ETL script for PAC-MCMV MVP
Loads Excel data + generates fake Habitação data, saves to database
\"\"\"

import sys
import os
from pathlib import Path
import pandas as pd
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from database import DatabaseManager
from excel_loader import process_excel_files
from fake_data_generator import generate_habitacao_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_etl():
    \"\"\"Main ETL process\"\"\"
    
    logger.info("🚀 Starting PAC-MCMV ETL process...")
    
    # Initialize database
    db = DatabaseManager()
    
    if not db.test_connection():
        logger.error("❌ Database connection failed")
        return False
    
    all_data = []
    
    # Try to load real PAC data from Excel
    try:
        logger.info("📊 Loading PAC data from Excel files...")
        pac_df = process_excel_files("../data")  # Look in data folder
        logger.info(f"✅ Loaded {len(pac_df)} PAC records from Excel")
        all_data.append(pac_df)
    except Exception as e:
        logger.warning(f"⚠️ Could not load Excel data: {e}")
        logger.info("📊 Generating fake PAC data instead...")
        from fake_data_generator import generate_pac_data
        pac_df = generate_pac_data(400)
        logger.info(f"✅ Generated {len(pac_df)} fake PAC records")
        all_data.append(pac_df)
    
    # Generate fake Habitação data (placeholder until real data arrives)
    logger.info("🏠 Generating fake Habitação data...")
    habitacao_df = generate_habitacao_data(250) 
    logger.info(f"✅ Generated {len(habitacao_df)} fake Habitação records")
    all_data.append(habitacao_df)
    
    # Combine all data
    combined_df = pd.concat(all_data, ignore_index=True)
    logger.info(f"📋 Combined dataset: {len(combined_df)} total records")
    
    # Save to database
    logger.info("💾 Saving to database...")
    try:
        db.save_dataframe(combined_df, 'projeto_status', if_exists='replace')
        logger.info("✅ Data saved successfully")
        
        # Verify data
        count = db.get_projeto_count()
        logger.info(f"📊 Database now contains {count} projects")
        
        # Show summary by program type
        summary = db.load_dataframe(\"\"\"
            SELECT tipo_programa, COUNT(*) as count 
            FROM projeto_status 
            GROUP BY tipo_programa
        \"\"\")
        
        logger.info("📈 Data summary:")
        for _, row in summary.iterrows():
            logger.info(f"   {row['tipo_programa']}: {row['count']} projects")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database save failed: {e}")
        return False

if __name__ == "__main__":
    success = run_etl()
    if success:
        print("\\n🎉 ETL completed successfully!")
        print("You can now run the Streamlit dashboard:")
        print("   streamlit run streamlit_app/dashboard.py")
    else:
        print("\\n💥 ETL failed - check the logs above")
        sys.exit(1)
""",

        # Updated Streamlit app with database connectivity
        "streamlit_app/dashboard.py": """import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
from pathlib import Path
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from etl.database import DatabaseManager

# Simple text analysis functions
from text_analyzer import analyze_situacao_texts, categorize_problems, detect_delays

st.set_page_config(
    page_title="PAC-MCMV MVP Dashboard",
    page_icon="🏗️",
    layout="wide"
)

@st.cache_data
def load_data_from_database():
    \"\"\"Load data from PostgreSQL database\"\"\"
    try:
        db = DatabaseManager()
        df = db.get_all_projects()
        return df
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None

def main():
    st.title("🏗️ PAC-MCMV MVP Dashboard")
    st.markdown("**Análise unificada PAC + Habitação - Foco na 'Situação Atual'**")
    
    # Load data from database
    with st.spinner("Carregando dados do banco..."):
        df = load_data_from_database()
    
    if df is None or df.empty:
        st.error("Não foi possível carregar dados do banco de dados")
        st.info("Execute primeiro: `python etl/run_etl.py`")
        return
    
    # Sidebar filters
    st.sidebar.header("🎛️ Filtros")
    
    # Program type filter
    program_types = ['Todos'] + sorted(df['tipo_programa'].unique().tolist())
    selected_program = st.sidebar.selectbox("Tipo de Programa", program_types)
    
    if selected_program != 'Todos':
        df = df[df['tipo_programa'] == selected_program]
    
    # State filter
    estados = ['Todos'] + sorted(df['uf'].dropna().unique().tolist())
    selected_estado = st.sidebar.selectbox("Estado", estados)
    
    if selected_estado != 'Todos':
        df = df[df['uf'] == selected_estado]
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Visão Geral", 
        "📝 Análise de Texto",
        "🚨 Problemas por Programa", 
        "🗺️ Análise Geográfica"
    ])
    
    with tab1:
        render_overview(df)
    
    with tab2:
        render_text_analysis(df)
    
    with tab3:
        render_program_problems(df)
    
    with tab4:
        render_geographic_analysis(df)

def render_overview(df):
    \"\"\"Render overview tab\"\"\"
    st.header("📊 Visão Geral dos Projetos")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de Projetos", len(df))
    
    with col2:
        pac_count = len(df[df['tipo_programa'] == 'PAC'])
        st.metric("Projetos PAC", pac_count)
    
    with col3:
        hab_count = len(df[df['tipo_programa'] == 'HABITACAO'])
        st.metric("Projetos Habitação", hab_count)
    
    with col4:
        # Count projects with delay indicators
        delay_count = sum(detect_delays(text) for text in df['situacao_atual'].fillna(''))
        delay_pct = (delay_count / len(df)) * 100 if len(df) > 0 else 0
        st.metric("Com Atrasos", f"{delay_count} ({delay_pct:.1f}%)")
    
    # Program distribution
    col1, col2 = st.columns(2)
    
    with col1:
        program_counts = df['tipo_programa'].value_counts()
        fig = px.pie(
            values=program_counts.values,
            names=program_counts.index,
            title="Distribuição PAC vs Habitação"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Financial summary
        financial_summary = df.groupby('tipo_programa').agg({
            'valor_repasse': 'sum',
            'valor_investimento': 'sum'
        }).reset_index()
        
        fig = px.bar(
            financial_summary,
            x='tipo_programa',
            y=['valor_repasse', 'valor_investimento'],
            title="Valores Financeiros por Programa",
            labels={'value': 'Valor (R$)', 'tipo_programa': 'Tipo de Programa'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent projects table
    st.subheader("Projetos Recentes")
    recent_df = df.nlargest(10, 'data_atualizacao_situacao')[
        ['proposta', 'uf', 'programa', 'tipo_programa', 'situacao_atual']
    ]
    st.dataframe(recent_df, use_container_width=True)

def render_text_analysis(df):
    \"\"\"Render text analysis tab\"\"\"
    st.header("📝 Análise de Texto - Situação Atual")
    
    # Analyze all situacao_atual texts
    texts = df['situacao_atual'].fillna('').tolist()
    
    with st.spinner("Analisando textos..."):
        analysis_results = analyze_situacao_texts(texts)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Most common words
        st.subheader("Palavras Mais Frequentes")
        words_data = pd.DataFrame(analysis_results['common_words'], columns=['Palavra', 'Frequência'])
        
        fig = px.bar(
            words_data.head(10),
            x='Frequência',
            y='Palavra',
            orientation='h',
            title="Top 10 Palavras"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Problem categories
        st.subheader("Categorias de Problemas")
        
        problem_counts = {}
        for text in texts:
            problems = categorize_problems(text)
            for problem in problems:
                problem_counts[problem] = problem_counts.get(problem, 0) + 1
        
        if problem_counts:
            problems_df = pd.DataFrame(list(problem_counts.items()), columns=['Categoria', 'Frequência'])
            problems_df = problems_df.sort_values('Frequência', ascending=False)
            
            fig = px.bar(
                problems_df,
                x='Frequência',
                y='Categoria',
                orientation='h',
                title="Tipos de Problemas Identificados"
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhuma categoria específica identificada")
    
    # Status classification
    st.subheader("Classificação de Status")
    
    status_counts = {'Com Problemas': 0, 'Normal': 0, 'Neutro': 0}
    
    for text in texts:
        if detect_delays(text):
            status_counts['Com Problemas'] += 1
        elif any(word in text.lower() for word in ['concluído', 'finalizada', 'executada', 'aprovada']):
            status_counts['Normal'] += 1
        else:
            status_counts['Neutro'] += 1
    
    status_df = pd.DataFrame(list(status_counts.items()), columns=['Status', 'Quantidade'])
    
    fig = px.pie(
        status_df,
        values='Quantidade',
        names='Status',
        title="Distribuição de Status dos Projetos",
        color_discrete_map={
            'Com Problemas': '#ff4444',
            'Normal': '#44ff44', 
            'Neutro': '#ffaa44'
        }
    )
    st.plotly_chart(fig, use_container_width=True)

def render_program_problems(df):
    \"\"\"Render program-specific problems analysis\"\"\"
    st.header("🚨 Problemas por Tipo de Programa")
    
    # Analyze problems by program type
    program_analysis = {}
    
    for program_type in df['tipo_programa'].unique():
        program_df = df[df['tipo_programa'] == program_type]
        texts = program_df['situacao_atual'].fillna('').tolist()
        
        # Count delays and problems
        delay_count = sum(detect_delays(text) for text in texts)
        delay_rate = (delay_count / len(texts)) * 100 if texts else 0
        
        # Categorize problems
        all_problems = []
        for text in texts:
            if detect_delays(text):
                all_problems.extend(categorize_problems(text))
        
        problem_counts = pd.Series(all_problems).value_counts().to_dict()
        
        program_analysis[program_type] = {
            'total_projects': len(program_df),
            'delay_count': delay_count,
            'delay_rate': delay_rate,
            'top_problems': problem_counts
        }
    
    # Display comparison
    col1, col2 = st.columns(2)
    
    with col1:
        # Delay rates by program
        delay_data = []
        for program, stats in program_analysis.items():
            delay_data.append({
                'Programa': program,
                'Taxa_Atraso': stats['delay_rate'],
                'Total_Projetos': stats['total_projects']
            })
        
        delay_df = pd.DataFrame(delay_data)
        
        fig = px.bar(
            delay_df,
            x='Programa',
            y='Taxa_Atraso',
            title="Taxa de Atrasos por Tipo de Programa",
            labels={'Taxa_Atraso': 'Taxa de Atrasos (%)'},
            color='Taxa_Atraso',
            color_continuous_scale='Reds'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Problem breakdown
        st.subheader("Principais Problemas por Programa")
        
        for program_type, stats in program_analysis.items():
            st.write(f"**{program_type}**")
            st.write(f"- {stats['delay_count']} projetos com atrasos de {stats['total_projects']} ({stats['delay_rate']:.1f}%)")
            
            if stats['top_problems']:
                top_3_problems = dict(list(stats['top_problems'].items())[:3])
                for problem, count in top_3_problems.items():
                    st.write(f"  • {problem}: {count}")
            else:
                st.write("  • Nenhum problema específico identificado")
            st.write("")

def render_geographic_analysis(df):
    \"\"\"Render geographic analysis\"\"\"
    st.header("🗺️ Análise Geográfica")
    
    # State-level analysis
    state_summary = []
    
    for uf in df['uf'].dropna().unique():
        state_df = df[df['uf'] == uf]
        texts = state_df['situacao_atual'].fillna('').tolist()
        
        total_projects = len(state_df)
        delay_projects = sum(detect_delays(text) for text in texts)
        delay_rate = (delay_projects / total_projects) * 100 if total_projects > 0 else 0
        
        pac_count = len(state_df[state_df['tipo_programa'] == 'PAC'])
        hab_count = len(state_df[state_df['tipo_programa'] == 'HABITACAO'])
        
        total_investment = state_df['valor_investimento'].fillna(0).sum()
        
        state_summary.append({
            'UF': uf,
            'Total_Projetos': total_projects,
            'Projetos_PAC': pac_count,
            'Projetos_Habitacao': hab_count,
            'Projetos_Atraso': delay_projects,
            'Taxa_Atraso': delay_rate,
            'Investimento_Total': total_investment
        })
    
    state_df = pd.DataFrame(state_summary)
    state_df = state_df.sort_values('Total_Projetos', ascending=False)
    
    # Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        # Projects by state
        fig = px.bar(
            state_df.head(15),  # Top 15 states
            x='UF',
            y='Total_Projetos',
            title="Projetos por Estado (Top 15)",
            labels={'Total_Projetos': 'Total de Projetos'},
            color='Total_Projetos',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Delay rate by state
        fig = px.bar(
            state_df.sort_values('Taxa_Atraso', ascending=False).head(15),
            x='UF', 
            y='Taxa_Atraso',
            title="Taxa de Atrasos por Estado (Top 15)",
            labels={'Taxa_Atraso': 'Taxa de Atrasos (%)'},
            color='Taxa_Atraso',
            color_continuous_scale='Reds'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed table
    st.subheader("Resumo Detalhado por Estado")
    
    display_df = state_df.copy()
    display_df['Taxa_Atraso'] = display_df['Taxa_Atraso'].round(1)
    display_df['Investimento_Total'] = display_df['Investimento_Total'].apply(
        lambda x: f"R$ {x/1000000:.1f}M" if x >= 1000000 else f"R$ {x/1000:.0f}K"
    )
    
    display_df = display_df.rename(columns={
        'UF': 'Estado',
        'Total_Projetos': 'Total',
        'Projetos_PAC': 'PAC',
        'Projetos_Habitacao': 'Habitação',
        'Projetos_Atraso': 'Atrasos',
        'Taxa_Atraso': 'Taxa (%)',
        'Investimento_Total': 'Investimento'
    })
    
    st.dataframe(display_df, use_container_width=True)

if __name__ == "__main__":
    main()
""",

        # Keep the simple text analyzer
        "streamlit_app/text_analyzer.py": """#!/usr/bin/env python3
\"\"\"
Simple text analyzer for PAC "Situação Atual" field - no over-engineering
\"\"\"

import re
from collections import Counter
import pandas as pd

# Portuguese stopwords (simplified list)
STOPWORDS = {
    'a', 'ao', 'aos', 'as', 'à', 'às', 'da', 'das', 'de', 'do', 'dos', 'e', 'em', 
    'na', 'nas', 'no', 'nos', 'o', 'os', 'para', 'por', 'com', 'um', 'uma', 'uns', 
    'umas', 'se', 'que', 'não', 'mais', 'muito', 'como', 'mas', 'já', 'também', 
    'só', 'até', 'isso', 'ela', 'ele', 'eles', 'elas', 'seu', 'sua', 'seus', 'suas',
    'foi', 'ser', 'está', 'tem', 'ter', 'são', 'foram', 'será', 'sendo', 'sido'
}

def clean_text(text):
    \"\"\"Basic text cleaning\"\"\"
    if pd.isna(text) or not isinstance(text, str):
        return ""
    
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\d+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def get_word_frequency(texts):
    \"\"\"Get word frequency from list of texts\"\"\"
    all_words = []
    
    for text in texts:
        cleaned = clean_text(text)
        words = cleaned.split()
        filtered_words = [w for w in words if len(w) > 2 and w not in STOPWORDS]
        all_words.extend(filtered_words)
    
    return Counter(all_words).most_common(20)

def detect_delays(text):
    \"\"\"Detect if text indicates delays or problems\"\"\"
    if pd.isna(text) or not isinstance(text, str):
        return False
    
    text_lower = text.lower()
    
    delay_indicators = [
        'atras', 'demora', 'pendente', 'aguardando', 'paralisad', 'suspend',
        'problem', 'dificuldade', 'impedimento', 'bloqueado', 'travado',
        'falta', 'ausência', 'carente', 'insuficiente', 'inadequado',
        'rejeitado', 'não aprovado', 'não concluído', 'incompleto'
    ]
    
    return any(indicator in text_lower for indicator in delay_indicators)

def categorize_problems(text):
    \"\"\"Categorize types of problems\"\"\"
    if pd.isna(text) or not isinstance(text, str):
        return []
    
    text_lower = text.lower()
    problems = []
    
    categories = {
        'Documentação': ['document', 'certidão', 'comprovante', 'anexo', 'papelada'],
        'Recursos Financeiros': ['recurso', 'verba', 'financeiro', 'orçamento', 'pagamento'],
        'Aprovação/Licenças': ['aprovação', 'licença', 'autorização', 'alvará'],
        'Questões Técnicas': ['técnico', 'engenharia', 'projeto', 'especificação'],
        'Questões Ambientais': ['ambiental', 'ibama', 'meio ambiente', 'licenciamento'],
        'Questões Legais': ['jurídico', 'legal', 'lei', 'judicial', 'processo']
    }
    
    for category, keywords in categories.items():
        if any(keyword in text_lower for keyword in keywords):
            problems.append(category)
    
    return problems

def analyze_situacao_texts(texts):
    \"\"\"Main analysis function\"\"\"
    results = {
        'total_texts': len(texts),
        'common_words': get_word_frequency(texts),
        'delay_count': sum(detect_delays(text) for text in texts)
    }
    
    return results
""",

        # Development configuration
        "docker-compose.dev.yml": """version: '3.8'

# Development override - just database
services:
  db:
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: pac_mcmv
      POSTGRES_USER: pac_user
      POSTGRES_PASSWORD: pac_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/01-init.sql

volumes:
  postgres_data:
""",

        # Simple test suite
        "tests/test_basic.py": """#!/usr/bin/env python3
\"\"\"
Basic tests for PAC-MCMV MVP
\"\"\"

import sys
from pathlib import Path
import unittest
import pandas as pd

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from streamlit_app.text_analyzer import detect_delays, categorize_problems
from etl.fake_data_generator import generate_pac_data

class TestTextAnalyzer(unittest.TestCase):
    
    def test_delay_detection(self):
        \"\"\"Test delay detection\"\"\"
        # Should detect delays
        self.assertTrue(detect_delays("Obra paralisada por falta de recursos"))
        self.assertTrue(detect_delays("Projeto aguardando aprovação"))
        self.assertTrue(detect_delays("Pendente documentação"))
        
        # Should not detect delays  
        self.assertFalse(detect_delays("Obra concluída com sucesso"))
        self.assertFalse(detect_delays("Projeto em execução normal"))
    
    def test_problem_categorization(self):
        \"\"\"Test problem categorization\"\"\"
        problems = categorize_problems("Aguardando documentação técnica")
        self.assertIn("Documentação", problems)
        
        problems = categorize_problems("Falta de recursos financeiros")
        self.assertIn("Recursos Financeiros", problems)
        
        problems = categorize_problems("Pendente licenciamento ambiental")
        self.assertIn("Questões Ambientais", problems)

class TestDataGeneration(unittest.TestCase):
    
    def test_fake_data_generation(self):
        \"\"\"Test fake data generation\"\"\"
        df = generate_pac_data(10)
        
        self.assertEqual(len(df), 10)
        self.assertIn('situacao_atual', df.columns)
        self.assertIn('uf', df.columns)
        self.assertIn('tipo_programa', df.columns)
        
        # All records should be PAC type
        self.assertTrue(all(df['tipo_programa'] == 'PAC'))

if __name__ == '__main__':
    unittest.main()
""",

        # Deployment helper
        "deploy/aws_deploy.sh": """#!/bin/bash
# AWS Deployment Script for PAC-MCMV MVP

echo "🚀 Starting AWS deployment for PAC-MCMV MVP..."

# Build and tag Docker image
echo "🐳 Building Docker image..."
docker build -t pac-mcmv-mvp .

# Tag for ECR (replace with your ECR URI)
ECR_URI="your-account.dkr.ecr.us-east-1.amazonaws.com/pac-mcmv-mvp"
docker tag pac-mcmv-mvp:latest $ECR_URI:latest

echo "📦 Image built and tagged"
echo "Next steps:"
echo "1. Push to ECR: docker push $ECR_URI:latest"
echo "2. Deploy to ECS/Fargate"
echo "3. Set up RDS PostgreSQL"
echo "4. Configure environment variables"

echo "✅ Build complete - ready for AWS deployment"
""",

        # Make deploy script executable
        "deploy/README.md": """# AWS Deployment Guide

## Architecture
- **ECS Fargate**: Streamlit app container
- **RDS PostgreSQL**: Database 
- **ALB**: Load balancer
- **ECR**: Container registry

## Steps

1. **Setup ECR**
   ```bash
   aws ecr create-repository --repository-name pac-mcmv-mvp
   ```

2. **Build & Push**
   ```bash
   ./deploy/aws_deploy.sh
   aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_URI
   docker push $ECR_URI:latest
   ```

3. **Setup RDS**
   - Create PostgreSQL instance
   - Run `database/init.sql` 
   - Update DATABASE_URL

4. **Deploy ECS**
   - Create ECS cluster
   - Create task definition
   - Create service with ALB

5. **Run ETL**
   ```bash
   python etl/run_etl.py
   ```

Ready for production! 🎉
"""
    }
    
    # Create files
    for file_path, content in files.items():
        file_obj = Path(file_path)
        file_obj.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_obj, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✓ Created file: {file_path}")

def setup_instructions():
    """Show detailed setup instructions"""
    print("\n" + "="*60)
    print("🏗️ PAC-MCMV MVP - PRODUCTION READY!")
    print("="*60)
    print("\n📋 DEVELOPMENT SETUP (Mac):")
    print("\n1. Start database:")
    print("   docker-compose -f docker-compose.dev.yml up -d")
    print("\n2. Install Python dependencies:")
    print("   pip install -r requirements.txt")
    print("\n3. Copy environment file:")
    print("   cp .env.example .env")
    print("\n4. Run ETL (loads fake data):")
    print("   python etl/run_etl.py")
    print("\n5. Start dashboard:")
    print("   streamlit run streamlit_app/dashboard.py")
    print("\n🐳 FULL DOCKER SETUP:")
    print("\n1. Start everything:")
    print("   docker-compose up --build")
    print("\n2. Access dashboard:")
    print("   http://localhost:8501")
    print("\n☁️ AWS DEPLOYMENT:")
    print("\n1. Follow deploy/README.md")
    print("2. Use deploy/aws_deploy.sh")
    print("\n" + "="*60)
    print("🎯 FEATURES:")
    print("✅ PostgreSQL database strategy")
    print("✅ ETL pipeline (Excel → Database)")
    print("✅ Fake Habitação data generator")
    print("✅ Docker containerization")
    print("✅ Simple 'Situação Atual' analysis")
    print("✅ Ready for AWS deployment")
    print("="*60)

if __name__ == "__main__":
    print("🏗️ Creating Production-Ready PAC-MCMV MVP...")
    print("=" * 50)
    
    try:
        create_directory_structure()
        print()
        create_files()
        setup_instructions()
        
    except Exception as e:
        print(f"❌ Error creating project: {e}")
        sys.exit(1)
