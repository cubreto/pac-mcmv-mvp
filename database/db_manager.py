#!/usr/bin/env python3
"""
Database manager for PAC-MCMV project
"""

import os
import logging
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

def get_db_url():
    """Get database URL from environment variables"""
    host = os.getenv('DB_HOST', 'localhost')
    port = os.getenv('DB_PORT', '5432')
    database = os.getenv('DB_NAME', 'pac_mcmv')
    user = os.getenv('DB_USER', 'postgres')
    password = os.getenv('DB_PASSWORD', 'postgres123')
    
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"

def get_engine():
    """Create database engine"""
    try:
        db_url = get_db_url()
        engine = create_engine(db_url, pool_pre_ping=True)
        # Test connection
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("✅ Database connection successful")
        return engine
    except SQLAlchemyError as e:
        logger.error(f"Database connection failed: {e}")
        raise

def get_session():
    """Get database session"""
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()

def create_tables(engine):
    """Create database tables"""
    metadata = MetaData()
    metadata.reflect(bind=engine)
    metadata.create_all(bind=engine)
    logger.info("✅ Tables created/verified")

if __name__ == "__main__":
    # Test connection
    logging.basicConfig(level=logging.INFO)
    try:
        engine = get_engine()
        print("✅ Database connection successful!")
        print(f"Connected to: {get_db_url().replace(os.getenv('DB_PASSWORD'), '***')}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
