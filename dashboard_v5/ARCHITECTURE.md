# MCMV Dashboard v5 Architecture Documentation

## Overview

Dashboard v5 is a complete rewrite of the MCMV dashboard, migrating from Streamlit (v4) to a modern React + FastAPI architecture. This provides significant performance improvements, better user experience, and more maintainable code.

## Key Improvements Over v4

1. **Performance**: 
   - Instant tab switching (no page reloads)
   - Smart caching with React Query
   - Materialized database views
   - Redis caching layer
   - Response times under 100ms

2. **User Experience**:
   - Modern React 18 UI with smooth animations
   - Real-time data updates
   - Responsive design with Tailwind CSS
   - Interactive Recharts visualizations

3. **Architecture**:
   - Separation of concerns (frontend/backend)
   - Type-safe API with Pydantic models
   - Async database operations
   - Container-based deployment

## Technology Stack

### Backend
- **FastAPI**: Modern async Python web framework
- **PostgreSQL**: Database with materialized views
- **Redis**: In-memory caching
- **SQLAlchemy**: Async ORM
- **Pydantic**: Data validation
- **Prometheus**: Metrics collection

### Frontend
- **React 18**: UI library with concurrent features
- **TypeScript**: Type safety
- **TanStack Query**: Data fetching and caching
- **Recharts**: Data visualization
- **Tailwind CSS**: Utility-first styling
- **Vite**: Fast build tool

### Infrastructure
- **Docker Compose**: Multi-container orchestration
- **Nginx**: Reverse proxy and static file serving
- **GitHub Actions**: CI/CD pipeline

## Project Structure

```
dashboard_v5/
├── docker-compose.v5.yml         # Main deployment configuration
├── backend/
│   ├── Dockerfile               # Backend container image
│   ├── requirements.txt         # Python dependencies
│   └── app/
│       ├── main.py             # FastAPI application
│       ├── config.py           # Configuration management
│       ├── database.py         # Database connection and queries
│       ├── models.py           # Pydantic models
│       ├── cache.py            # Redis caching
│       └── business_rules.yml  # Business configuration
├── frontend/
│   ├── Dockerfile              # Frontend container image
│   ├── package.json            # Node dependencies
│   ├── vite.config.ts          # Vite configuration
│   ├── tsconfig.json           # TypeScript configuration
│   └── src/
│       ├── App.tsx             # Main application component
│       ├── api/
│       │   ├── client.ts       # API client
│       │   └── hooks.ts        # React Query hooks
│       ├── components/
│       │   └── charts/         # Visualization components
│       └── pages/
│           └── Dashboard.tsx   # Main dashboard page
└── nginx/
    └── nginx.conf              # Proxy configuration
```

## API Endpoints

All endpoints are prefixed with `/api/v5`:

- `GET /health` - Health check
- `GET /kpis` - Key performance indicators
- `GET /regional` - Regional summary data
- `GET /programs` - Program summary data
- `GET /temporal` - Time series trends
- `GET /delivery-forecast` - Delivery predictions
- `GET /data-quality` - Data quality metrics
- `GET /config` - Frontend configuration

## Database Schema

The system uses the existing MCMV database with these key tables:
- `mcmv_v2.projetos` - Main projects table
- `mcmv_v2.dados_prioritarios` - Priority data (not used in Resumo)

Materialized views created for performance:
- `mcmv_v5.mv_kpi_summary` - Aggregated KPIs
- `mcmv_v5.mv_regional_summary` - Regional aggregations
- `mcmv_v5.mv_temporal_trends` - Time series data

## Data Flow

1. **User Request** → Nginx → React App
2. **API Call** → TanStack Query → FastAPI
3. **Cache Check** → Redis (if cached, return)
4. **Database Query** → PostgreSQL (materialized views)
5. **Response** → Cache Update → Frontend Update

## Caching Strategy

### Frontend (TanStack Query)
- KPIs: 30 minutes stale time
- Regional/Program data: 30 minutes
- Delivery forecast: 30 minutes
- Configuration: 1 hour

### Backend (Redis)
- Aggregated data: 30 minutes TTL
- Summary data: 30 minutes TTL
- Detailed data: 10 minutes TTL
- Static data: 1 hour TTL

## Key Components

### Frontend Components

1. **Dashboard.tsx**: Main dashboard with tabbed interface
2. **RegionalChart.tsx**: Regional analysis with financial table
3. **ProgramChart.tsx**: Program analysis with multiple views
4. **DeliveryForecastChart.tsx**: Time series delivery predictions
5. **PerformanceMetrics.tsx**: System performance monitoring

### Backend Services

1. **DatabaseManager**: Async database operations
2. **CacheManager**: Redis caching layer
3. **BusinessRules**: Configuration management
4. **MetricsMiddleware**: Performance monitoring

## Deployment

### Development
```bash
docker compose -f docker-compose.v5.yml up --build
```

### Production
- Frontend served on port 8504
- API available at localhost:8504/api/v5
- Redis on internal port 6380
- Metrics at /metrics (Prometheus format)

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `ENVIRONMENT`: development/staging/production
- `API_BASE_PATH`: API route prefix

## Performance Optimizations

1. **Materialized Views**: Pre-computed aggregations
2. **Connection Pooling**: Reused database connections
3. **Smart Caching**: Multi-layer cache strategy
4. **Lazy Loading**: Components loaded on demand
5. **Compression**: Gzip for API responses
6. **CDN Ready**: Static assets optimized

## Security Features

1. **CORS Configuration**: Controlled cross-origin access
2. **Input Validation**: Pydantic models
3. **SQL Injection Protection**: Parameterized queries
4. **Rate Limiting**: Via Nginx (configurable)
5. **Health Checks**: Kubernetes-ready endpoints

## Monitoring

1. **Prometheus Metrics**:
   - Request count by endpoint
   - Response time histograms
   - Cache hit rates
   - Error rates

2. **Application Logs**:
   - Structured JSON logging
   - Request/response tracking
   - Error stack traces
   - Performance metrics

## Migration from v4

The v5 dashboard maintains feature parity with v4 while adding:
- Faster performance (10x improvement in tab switching)
- Better user experience (no page reloads)
- More maintainable code (TypeScript + proper separation)
- Enhanced visualizations (interactive charts)
- Real-time updates (React Query polling)

Data compatibility is maintained - both v4 and v5 use the same database tables and business logic.

## Future Enhancements

1. **WebSocket Support**: Real-time data updates
2. **PWA Features**: Offline capability
3. **Advanced Analytics**: ML-based predictions
4. **Multi-tenancy**: Organization-based access
5. **GraphQL API**: More flexible data fetching