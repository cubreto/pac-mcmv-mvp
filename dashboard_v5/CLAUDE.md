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

## 📊 DATA QUALITY AND UI FIXES (2025-07-16)

### Critical Field Mappings

**Dados Prioritários - UH Fields**:
- **Issue**: `uh_contratadas` field contains mostly zeros (only 21 records with values)
- **Solution**: Always use `uh_original_contratadas` for calculations
- **Impact**: Fixed delivery rate showing 20,726.85% instead of correct 83.82%

**RURAL Investment Calculation**:
- **Issue**: SQL using `COALESCE(vr_terreno, 0) + COALESCE(vr_ts, 0)` was 66.7x smaller
- **Solution**: Use `vr_total_investimento` field directly
- **Validation**: RURAL investments now show correctly (e.g., 7,500M instead of 113M)

### Date Field Clarifications

**Construction vs Delivery Dates**:
- **Field Used**: `dt_previsao_conclusao_obra` (construction completion)
- **Not Available**: `DT_PREVISAO_ENTREGA_DO_EMPREENDIMENTO` (delivery date)
- **UI Labels**: Changed from "Previsão de Entregas" to "Previsão de Conclusão de Obras"
- **Impact**: Aligns user expectations with available data

### Currency Formatting Standards

**formatCurrencyDashboard** (for KPI cards):
```typescript
- Values >= 1 billion: "R$ 24.7 bi"
- Values >= 1 million: "R$ 150.5M"
- Values >= 1 thousand: "R$ 850 mil"
- Values < 1 thousand: "R$ 250"
```

**formatCurrencyTable** (for data tables):
```typescript
- Values >= 1 million: "R$ 3.5M"
- Values >= 1 thousand: "R$ 750 mil"
- Values < 1 thousand: "R$ 500"
```

### UI Design Standards (v5.0.7)

**Clean Minimal Design**:
- **Icons**: Navigation menu keeps program icons (🌾 RURAL, 🏗️ FAR, 🏘️ FDS)
- **Other Icons**: Removed from section headers, charts, and content areas
- **Card Design**: White background with colored left border (4px)
- **Card Padding**: Reduced from p-6 to p-4 for compact display
- **Border Colors**: 
  - Blue (border-blue-500): Primary metrics
  - Green (border-green-500): Success metrics
  - Purple (border-purple-500): Percentage/rate metrics
  - Orange (border-orange-500): Count metrics

**Table Design**:
- **Headers**: Dark gradient background (from-gray-700 to-gray-800)
- **Text**: White bold uppercase headers
- **Rows**: Alternating white/gray-50 backgrounds
- **Status Pills**: Colored backgrounds with matching text

### Common Troubleshooting

**Cache Issues**:
```bash
# Clear Redis cache when data seems incorrect
docker exec mcmv-v5-redis redis-cli FLUSHALL
```

**API Base Path**:
- **Correct**: `/api/v5/dados-prioritarios`
- **Incorrect**: `/api/v1/dados-prioritarios`

**Container Health Checks**:
```bash
# Quick health check
curl http://localhost:8001/api/v5/health
curl http://localhost:8504/health
```

---

## 📊 DADOS PRIORITÁRIOS - TABLE IMPROVEMENTS (2025-07-18)

### Monthly Snapshot Handling

**Issue**: Todos os Dados table showed repeated rows without month/year indication
**Solution**: Implemented collapsible rows grouped by Programa → Situação → Month/Year

**Key Features**:
- Expandable/collapsible row groups with expand/collapse icons
- Month/Year extracted from `data_movimento` field
- Added columns: Valor Contratado, Valor Desembolsado
- Clean presentation without debugging text

### Estado Atual Tab Separation

**Implementation**:
- Separate API endpoint: `/api/v5/dados-prioritarios/estado-atual`
- Shows only May 2025 snapshot (latest data)
- Hides Ano/Mês de Movimento filters when Estado Atual tab is active
- Header indicates "Snapshot de Maio/2025"

**Grouping Order**:
- Changed from Situação/Modalidade to Programa/Situação
- Matches the structure of Todos os Dados tab

---

## 🎯 FILTER FIXES AND UI UPDATES (2025-07-18)

### Delivery Forecast Filter Fix

**Issue**: 500 error - "column sg_regiao does not exist" in projetos table
**Solution**: Implemented region-to-state mapping since projetos only has sg_uf

```python
region_states = {
    'Norte': ['AC', 'AP', 'AM', 'PA', 'RO', 'RR', 'TO'],
    'Nordeste': ['AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE'],
    'Centro-Oeste': ['DF', 'GO', 'MT', 'MS'],
    'Sudeste': ['ES', 'MG', 'RJ', 'SP'],
    'Sul': ['PR', 'RS', 'SC']
}
```

### Program Page Layout Reordering

**New Order**:
1. Program Banner (with full program name)
2. Global Filters
3. Tab Content

**Program Names Updated**:
- **FDS** - Fundo de Desenvolvimento Social
- **FAR** - Fundo de Arrendamento Residencial
- **RURAL** - Programa Nacional de Habitação Rural

### UI Cleanups

**Removed**:
- Blue banner from Resumo page
- Icons from Previsão de Conclusão cards
- Icons from section headers in program pages
- Icons from tab labels in program pages

**Applied**:
- Clean white cards with colored left ribbon design
- Consistent formatting across all pages

---

## 📊 DADOS PRIORITÁRIOS - CRITICAL ISSUES AND FIXES (2025-07-31)

### Issue 1: Dados Históricos Only Showing Latest Snapshot

**Problem**: 
- The "Dados Históricos" tab was showing only 13,656 unique projects instead of ~66,000 historical records
- This was caused by using GROUP BY in the SQL query which aggregated data instead of returning individual records

**Root Cause**: 
- The query was grouping by programa/situacao/data_movimento, creating summaries instead of showing all historical data
- ETL process is correct (database has 66,130 records), but the API endpoint was aggregating them

**Solution**:
```sql
-- Changed from GROUP BY query to individual records:
SELECT apf, modalidade, situacao_empreendimento, data_movimento, ...
FROM mcmv_v2.dados_prioritarios
ORDER BY data_movimento DESC, programa, situacao_empreendimento, apf
```

**Fix Applied**: Modified `/dashboard_v5/backend/app/main.py` get_dados_prioritarios endpoint

### Issue 2: Frontend Showing 0 Projects in Table

**Problem**: 
- After fixing the backend to return individual records, the frontend showed 0 in the "Projetos" column
- The frontend was expecting pre-aggregated data with a "projetos" field

**Root Cause**:
- Frontend was looking for `item.projetos` (aggregated count) but receiving individual records with `item.apf`
- Need to count unique APF values instead of using pre-calculated counts

**Solution**:
- Modified TodosOsDadosTab component to:
  - Count unique projects using `new Set(situacaoData.monthlyData.map(item => item.apf))`
  - Sum UH and financial values from the latest month for each unique project
  - Display correct totals in all columns

**Fix Applied**: Modified `/dashboard_v5/frontend/src/components/TodosOsDadosTab.tsx`

### Issue 3: KPI Cards Showing on Wrong Tabs

**Problem**:
- KPI cards (Total Projetos, UH Contratadas, Taxa de Entrega) were showing on all tabs
- Should only appear on "Estado Atual" tab

**Solution**:
- Modified condition from `(activeTab === 'estado-atual' || activeTab === 'previsao-entrega')` to just `activeTab === 'estado-atual'`

**Fix Applied**: Modified `/dashboard_v5/frontend/src/pages/DadosPrioritariosPage.tsx`

### Important Notes for Future ETL

1. **Data Structure**: 
   - Dados Prioritários contains monthly snapshots (same project appears multiple times)
   - Always preserve all historical records during ETL
   - Use DISTINCT ON (apf) only for summaries, not for historical views

2. **Frontend Handling**:
   - When backend returns individual records, frontend must aggregate for display
   - Count unique projects, don't expect pre-aggregated counts
   - Always use latest month's data for totals per project

3. **Testing After ETL**:
   - Verify total record count: ~66k for 5 months of data
   - Check unique project count: ~13.6k unique APFs
   - Ensure historical progression is preserved

---

## 🔧 RURAL FILTERS IMPLEMENTATION (2025-07-31)

### New Filters Added
- **tipo**: RURAL, RURAL-CALAMIDADES
- **modalidade_proposta**: Produção Habitacional, Melhoria Habitacional

### Implementation Details
1. **Database**: Added columns to mcmv_v2.projetos with partial indexes
2. **ETL**: Loaded data from Excel file, handled NaN values
3. **API**: Updated all RURAL endpoints to accept new filters
4. **Frontend**: Created RuralFilters component
5. **KPIs Fix**: Updated KPIs endpoint to accept tipo/modalidade_proposta filters

### Known Issues Fixed
- KPIs not filtering: Added tipo and modalidade_proposta to get_kpi_data method
- NULL modalidade: Fixed 1 record with missing modalidade_proposta
- Filter counts: Modalidade shows total across all tipos (correct behavior)

---

## 🚀 PERFORMANCE OPTIMIZATIONS (2025-07-31)

### Dados Prioritários Historical Data Performance

**Issue**: Dados Prioritários históricos (66,000+ records) was loading slowly
**Root Cause**: No database indexes on the dados_prioritarios table

**Solution Applied**: Created 6 strategic indexes
```sql
idx_dados_prioritarios_filters     -- (data_movimento DESC, modalidade, situacao_empreendimento)
idx_dados_prioritarios_dates       -- (data_movimento DESC, data_contratacao)
idx_dados_prioritarios_uf          -- (sg_uf)
idx_dados_prioritarios_apf         -- (apf)
idx_dados_prioritarios_composite   -- (data_movimento DESC, modalidade, situacao_empreendimento, sg_uf)
idx_dados_prioritarios_year_month  -- (EXTRACT(year), EXTRACT(month))
```

**Result**: Significantly faster query performance + Redis caching for repeated queries

### Empty Data Handling

**Issue**: 500 errors when filters returned no data (e.g., PARALISADO in 2025)
**Root Cause**: `float(None)` conversion error in summary calculations
**Solution**: Added proper None handling with `or 0` fallbacks
**Result**: Shows "Nenhum dado encontrado" message instead of errors

---
**Last Updated**: 2025-07-31
**Importance**: CRITICAL - Prevents development conflicts and data loss