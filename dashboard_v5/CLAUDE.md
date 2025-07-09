# CLAUDE.md - Important Project Notes

## 🚨 CRITICAL ARCHITECTURE SEPARATION

**NEVER MIX DASHBOARD VERSIONS - THEY ARE COMPLETELY SEPARATE SYSTEMS**

### Dashboard Architecture Overview

**Port 8503 - Legacy Streamlit Dashboard (mcmv-custom)**
- **Directory**: `/streamlit_app/` (root level)
- **Technology**: Streamlit + Python
- **Purpose**: Legacy v3/v4 dashboard for comparison and fallback
- **Container**: `mcmv-custom`
- **URL**: http://54.90.170.181:8503/
- **Docker Compose**: `docker-compose.mcmv-custom.yml`

**Port 8504 - Modern React Dashboard v5**
- **Directory**: `/dashboard_v5/` (completely separate)
- **Technology**: React + TypeScript + FastAPI + Redis + Nginx
- **Purpose**: Production v5 dashboard with modern architecture
- **Containers**: `mcmv-v5-frontend`, `mcmv-v5-api`, `mcmv-v5-proxy`, `mcmv-v5-redis`
- **URL**: http://54.90.170.181:8504/
- **Docker Compose**: `dashboard_v5/docker-compose.v5.yml`

### 🔒 STRICT SEPARATION RULES

1. **File Isolation**: 
   - v5 work = ONLY in `/dashboard_v5/` directory
   - Legacy work = ONLY in `/streamlit_app/` directory
   - NEVER modify files across directories

2. **Container Isolation**:
   - v5 containers: Use `docker-compose.v5.yml`
   - Legacy containers: Use `docker-compose.mcmv-custom.yml`
   - Different container names, networks, and volumes

3. **Port Isolation**:
   - Port 8503: Legacy Streamlit dashboard
   - Port 8504: v5 React frontend
   - Port 8505: v5 Nginx proxy (alternative access)
   - Port 8001: v5 FastAPI backend

### ⚠️ LESSON LEARNED (2025-07-02)

**What Happened**: During v5 development, we accidentally overwrote legacy dashboard files in `/streamlit_app/` causing the mcmv-custom service to fail with missing component errors. This required extracting files from backup zip files.

**Root Cause**: File contamination between dashboard versions sharing similar directory structures.

**Prevention**: Maintain strict directory separation and never work across versions simultaneously.

### 🛠️ Development Guidelines

- **When working on v5**: `cd dashboard_v5/` and stay there
- **When working on legacy**: `cd /` and work in `streamlit_app/`
- **Always verify working directory** before making changes
- **Use version-specific docker-compose files**
- **Test each dashboard independently**

### 📋 Quick Reference Commands

**V5 Dashboard**:
```bash
cd dashboard_v5/
docker-compose -f docker-compose.v5.yml up -d
# Access: http://54.90.170.181:8504/
```

**Legacy Dashboard**:
```bash
# From project root
docker-compose -f docker-compose.mcmv-custom.yml up -d
# Access: http://54.90.170.181:8503/
```

**Database** (shared by both):
```bash
docker-compose up -d  # Main postgres container
```

---

## 🐳 DOCKER ARCHITECTURE - DASHBOARD V5

### Service Architecture

Dashboard v5 uses a microservices architecture with 4 containers:

1. **mcmv-v5-frontend** (Port 8504)
   - React 18 + TypeScript + Vite
   - Served by Nginx with gzip compression
   - Multi-stage Docker build for optimization

2. **mcmv-v5-api** (Port 8001)
   - FastAPI + Python 3.11
   - 4 Uvicorn workers for concurrent requests
   - Async PostgreSQL connections
   - Health checks and metrics

3. **mcmv-v5-redis** (Port 6380)
   - Redis 7 Alpine for caching
   - 512MB memory limit with LRU eviction
   - Persistent volume for data

4. **mcmv-v5-proxy** (Port 8505)
   - Optional Nginx reverse proxy
   - Alternative access point

### Essential Docker Commands

**Build and Deploy**:
```bash
cd dashboard_v5/

# Build and start all services
docker-compose -f docker-compose.v5.yml up -d --build

# View logs for all services
docker-compose -f docker-compose.v5.yml logs -f

# Check service status
docker-compose -f docker-compose.v5.yml ps
```

**Service Management**:
```bash
# Restart specific service
docker-compose -f docker-compose.v5.yml restart mcmv-v5-api

# Rebuild specific service
docker-compose -f docker-compose.v5.yml build mcmv-v5-frontend
docker-compose -f docker-compose.v5.yml up -d mcmv-v5-frontend

# Stop specific service
docker-compose -f docker-compose.v5.yml stop mcmv-v5-api

# View specific service logs
docker-compose -f docker-compose.v5.yml logs -f mcmv-v5-api
```

**Full Deployment Process**:
```bash
# 1. Stop existing containers
docker-compose -f docker-compose.v5.yml down

# 2. Pull latest code (if using git)
git pull

# 3. Clean build (no cache)
docker-compose -f docker-compose.v5.yml build --no-cache

# 4. Start services
docker-compose -f docker-compose.v5.yml up -d

# 5. Verify health
curl http://localhost:8504/health
curl http://localhost:8001/health
```

**Debugging Commands**:
```bash
# Access container shell
docker exec -it mcmv-v5-api /bin/sh
docker exec -it mcmv-v5-frontend /bin/sh

# Check resource usage
docker stats

# View build logs
docker-compose -f docker-compose.v5.yml logs --tail=100

# Check for errors
docker-compose -f docker-compose.v5.yml logs | grep ERROR

# Inspect network
docker network inspect dashboard_v5_mcmv-v5-network
```

**Zero-Downtime Update**:
```bash
# Update single service without affecting others
docker-compose -f docker-compose.v5.yml up -d --no-deps --build mcmv-v5-api
```

### Networks and Volumes

- **Networks**:
  - `mcmv-v5-network`: Internal network for v5 services (172.26.0.0/16)
  - `pac-mcmv-mvp_default`: External network for database access

- **Volumes**:
  - `mcmv_v5_redis_data`: Persistent Redis storage
  - `./logs`: API logs mounted to host
  - `./docs`: Documentation served by frontend

### Environment Configuration

Services use smart defaults with environment variable overrides:
- Database: `pac_mcmv` (schema: `mcmv_v2`)
- Redis: Internal port 6379, external 6380
- API: 300 requests/minute rate limit
- CORS: Configured for production

### Health Monitoring

```bash
# Check all health endpoints
curl http://localhost:8504/health     # Frontend
curl http://localhost:8001/health      # API
curl http://localhost:8001/metrics     # Prometheus metrics
docker exec mcmv-v5-redis redis-cli ping  # Redis
```

### 🗃️ Backup Strategy

- **Legacy files backed up in**: `mcmv_dashboard_v4_correct.zip`
- **V5 files**: Git version controlled in `/dashboard_v5/`
- **Never rely on container storage** - always use volume mounts or git

---

## 🗄️ DATABASE CONNECTION REQUIREMENTS

**MANDATORY**: Claude MUST read and follow `DATABASE_CONNECTION_GUIDE.md` for all database operations.

### Critical Database Configuration
- **Database**: `pac_mcmv` (NOT `mcmv_db`)
- **Schema**: `mcmv_v2` (NOT `public` or `mcmv_v5`)
- **Container**: `pac-mcmv-mvp-db-1`
- **Credentials**: `postgres` / `postgres123`

### Before Any Database Changes
1. **READ** `DATABASE_CONNECTION_GUIDE.md` completely
2. **VERIFY** schema and table existence  
3. **TEST** connection with specified credentials
4. **NEVER** assume database structure

**Reference Document**: `/home/ec2-user/pac-mcmv-mvp/DATABASE_CONNECTION_GUIDE.md`

---
**Last Updated**: 2025-07-09
**Importance**: CRITICAL - Prevents development conflicts and data loss