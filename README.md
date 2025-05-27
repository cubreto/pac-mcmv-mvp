# PAC-MCMV MVP - Production Ready

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
