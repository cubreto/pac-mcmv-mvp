#!/usr/bin/env python3
"""
Database connection and operations for PAC-MCMV MVP
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, database_url=None):
        if not database_url:
            # Build URL from environment variables
            host = os.getenv('DB_HOST', 'localhost')
            port = os.getenv('DB_PORT', '5432')
            database = os.getenv('DB_NAME', 'pac_mcmv')
            user = os.getenv('DB_USER', 'postgres')
            password = os.getenv('DB_PASSWORD', 'postgres123')
            
            self.database_url = f'postgresql://{user}:{password}@{host}:{port}/{database}'
        else:
            self.database_url = database_url
            
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def test_connection(self):
        """Test database connection"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                logger.info("✅ Database connection successful")
                return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def execute_query(self, query, params=None):
        """Execute a raw SQL query"""
        with self.engine.connect() as conn:
            return conn.execute(text(query), params or {})



    # ───────────────────────────────────────────────
    # helper readers  ←  ★ ADD THESE ★
    # ───────────────────────────────────────────────
    def fetch_one(self, sql: str, params: dict | None = None):
        """Return a single row as a dict (raises if none)."""
        with self.engine.connect() as conn:
            row = conn.execute(text(sql), params or {}).mappings().first()
            if row is None:
                raise ValueError("query returned no rows")
            return dict(row)

    def fetch_all(self, sql: str, params: dict | None = None):
        """Return a list of rows as dicts."""
        with self.engine.connect() as conn:
            return [
                dict(r) for r in conn.execute(text(sql), params or {}).mappings()
            ]

    
    def load_dataframe(self, query, params=None):
        """Load data into pandas DataFrame"""
        return pd.read_sql(query, self.engine, params=params)
    
    def save_dataframe(self, df, table_name, if_exists='replace'):
        """Save DataFrame to database"""
        df.to_sql(table_name, self.engine, if_exists=if_exists, index=False, method='multi')
        logger.info(f"Saved {len(df)} records to {table_name}")
    
    def get_projeto_count(self):
        """Get total project count"""
        query = "SELECT COUNT(*) as total FROM projeto_status"
        result = self.load_dataframe(query)
        return result['total'].iloc[0] if len(result) > 0 else 0
    
    def create_tables(self):
        """Create necessary tables"""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS projeto_status (
            id SERIAL PRIMARY KEY,
            programa VARCHAR(255),
            projeto_id VARCHAR(255) UNIQUE,
            nome_projeto TEXT,
            situacao_atual TEXT,
            uf VARCHAR(2),
            municipio VARCHAR(255),
            valor_repasse DECIMAL(15,2),
            percentual_executado DECIMAL(5,2),
            data_inicio DATE,
            data_fim_prevista DATE,
            beneficiarios_previstos INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        try:
            self.execute_query(create_table_query)
            logger.info("✅ Tables created/verified")
            return True
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            return False

    def get_all_projects(self):
        """Get all projects from the database"""
        query = """
        SELECT 
            programa,
            projeto_id,
            nome_projeto,
            situacao_atual,
            uf,
            municipio,
            valor_repasse,
            percentual_executado,
            data_inicio,
            data_fim_prevista,
            beneficiarios_previstos
        FROM projeto_status
        """
        return self.load_dataframe(query)

    def get_all_projects(self):
        """Get all projects from the database using actual column names"""
        query = """
        SELECT 
            programa,
            proposta as projeto_id,
            municipio_beneficiado || ' - ' || uf as nome_projeto,
            situacao_atual,
            uf,
            municipio_beneficiado as municipio,
            valor_repasse,
            percentual_obra_realizado as percentual_executado,
            data_inicio_obra as data_inicio,
            data_atualizacao_situacao as data_fim_prevista,
            0 as beneficiarios_previstos
        FROM projeto_status
        """
        return self.load_dataframe(query)
