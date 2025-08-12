# MCMV Dashboard v5

A modern, high-performance dashboard for monitoring and analyzing MCMV (Minha Casa Minha Vida) program data.

## Overview

This dashboard provides comprehensive visualization and analysis tools for:
- FAR (Fundo de Arrendamento Residencial)
- FDS (Fundo de Desenvolvimento Social) 
- RURAL (Programa Nacional de Habitação Rural)
- Dados Prioritários (Priority Data monitoring)

## Technology Stack

- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS
- **Backend**: FastAPI + Python 3.11 + AsyncPG
- **Database**: PostgreSQL with materialized views
- **Cache**: Redis 7
- **Deployment**: Docker + Docker Compose

## Quick Start

### Prerequisites
- Docker 20.10+
- Docker Compose 1.29+
- PostgreSQL database with MCMV data

### Development

```bash
# Clone the repository
git clone <your-gitlab-repo>
cd dashboard_v5

# Start all services
docker-compose -f docker-compose.v5.yml up -d

# Access the dashboard
# Frontend: http://localhost:8504
# API Docs: http://localhost:8001/docs
```

### Production

```bash
# Deploy with production compose file
docker-compose -f docker-compose.prod.yml up -d
```

See [PRODUCTION_DEPLOYMENT_GUIDE.md](PRODUCTION_DEPLOYMENT_GUIDE.md) for detailed instructions.

## Features

### Program Monitoring
- Real-time KPIs and metrics
- Status distribution charts
- Timeline visualization
- Financial analysis tables

### Data Quality
- Automated quality checks
- Missing data analysis
- Trend monitoring
- ETL validation reports

### Filtering System
- Global filters (Region, State, Municipality)
- Program-specific filters
- Date range selection
- Export capabilities

### Performance
- Materialized views for fast queries
- Redis caching
- Optimized database indexes
- Async API endpoints

## Documentation

See `PRODUCTION_DEPLOYMENT_GUIDE.md` for detailed deployment instructions.

## Development

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Backend Development
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## License

Proprietary - Digiteam

## Contact

For support and inquiries: rangel@digiteam.cloud

---
Developed by Digiteam
Version: 5.0.7