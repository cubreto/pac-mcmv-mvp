# MCMV Dashboard v5

A high-performance dashboard for monitoring MCMV (Minha Casa Minha Vida) housing programs, built with React and FastAPI.

## Quick Start

```bash
# Start all services
docker compose -f docker-compose.v5.yml up --build

# Access dashboard
http://localhost:8504
```

## Features

- **Real-time KPIs**: Monitor 1,566 projects and 155,477 housing units
- **Regional Analysis**: Interactive maps and financial breakdowns by region
- **Program Tracking**: Detailed views for FAR, FDS, and RURAL programs
- **Delivery Forecasts**: AI-powered predictions for project completion
- **Performance Monitoring**: Built-in metrics and health checks

## Architecture

- **Frontend**: React 18 + TypeScript + TanStack Query + Recharts
- **Backend**: FastAPI + PostgreSQL + Redis + SQLAlchemy
- **Infrastructure**: Docker Compose + Nginx + Prometheus

## Documentation

- [Architecture Overview](./ARCHITECTURE.md) - System design and components
- [Implementation Guide](./IMPLEMENTATION_GUIDE.md) - Step-by-step development process
- [API Documentation](http://localhost:8504/docs) - Interactive API docs (dev only)

## Key Improvements Over v4

| Feature | v4 (Streamlit) | v5 (React + FastAPI) |
|---------|----------------|----------------------|
| Tab Switching | 3-5 seconds | Instant |
| Page Reloads | Yes | No |
| Caching | Basic | Multi-layer |
| Type Safety | No | Full TypeScript |
| API Response | 500ms+ | <100ms |
| Mobile Support | Limited | Fully Responsive |

## Project Structure

```
dashboard_v5/
├── backend/          # FastAPI application
├── frontend/         # React application
├── nginx/           # Proxy configuration
├── docker-compose.v5.yml
└── docs/            # Documentation
```

## Development

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Database
The dashboard connects to the existing PostgreSQL database with mcmv_v2 schema.

## Environment Variables

Create a `.env` file:
```env
DATABASE_URL=postgresql://dashboard_user:securepassword@mcmv-db:5432/mcmv_dashboard
REDIS_URL=redis://mcmv-v5-redis:6379/0
ENVIRONMENT=development
```

## Monitoring

- Health Check: http://localhost:8504/api/v5/health
- Metrics: http://localhost:8504/metrics (Prometheus format)

## Contributing

1. Follow the existing code style
2. Add tests for new features
3. Update documentation
4. Submit PR with clear description

## License

Private - MCMV Dashboard Project