# MCMV Database Connection Guide

## 🚨 CRITICAL DATABASE CONFIGURATION

**This document defines the MANDATORY database configuration for all MCMV dashboard implementations. Claude MUST adhere to these specifications exactly.**

---

## Database Connection Details

### Primary Database Container
- **Container Name**: `pac-mcmv-mvp-db-1`
- **Image**: `postgres:15-alpine`
- **Host**: `pac-mcmv-mvp-db-1` (for docker containers)
- **Port**: `5432` (internal), `5432` (external)
- **Database Name**: `pac_mcmv`
- **Username**: `postgres`
- **Password**: `postgres123`

### Schema Structure
```sql
-- Primary schema containing MCMV data
Schema: mcmv_v2

-- Available tables in mcmv_v2 schema:
- dados_prioritarios
- projetos
- projetos_backup_june27
```

## Connection Configuration for Different Services

### Dashboard v5 (Current)
```yaml
# docker-compose.v5.yml
environment:
  - DB_HOST=pac-mcmv-mvp-db-1
  - DB_PORT=5432
  - DB_NAME=pac_mcmv
  - DB_USER=postgres
  - DB_PASSWORD=postgres123
```

### Backend Database Configuration
```python
# backend/app/database.py
metadata = MetaData(schema="mcmv_v2")  # MUST use mcmv_v2 schema
```

### Connection String Format
```
postgresql://postgres:postgres123@pac-mcmv-mvp-db-1:5432/pac_mcmv
```

---

## 🔒 MANDATORY RULES FOR CLAUDE

### 1. Schema Requirements
- **ALWAYS** use schema `mcmv_v2` for MCMV data access
- **NEVER** assume schema `public` contains MCMV data
- **NEVER** create new schemas without explicit instruction

### 2. Database Connection
- **ALWAYS** connect to database `pac_mcmv` 
- **ALWAYS** use container name `pac-mcmv-mvp-db-1` as host
- **NEVER** modify database credentials without explicit instruction

### 3. Table Access Patterns
```sql
-- Correct table references
SELECT * FROM mcmv_v2.projetos;
SELECT * FROM mcmv_v2.dados_prioritarios;

-- Incorrect table references (DO NOT USE)
SELECT * FROM projetos;  -- Wrong: missing schema
SELECT * FROM public.projetos;  -- Wrong: wrong schema
```

### 4. Configuration Validation
Before making any database-related changes, Claude MUST:
1. Verify the schema exists: `\dn` in psql
2. Verify tables exist: `\dt mcmv_v2.*` in psql
3. Test connection with correct credentials
4. Confirm data accessibility

---

## Verification Commands

### Check Database Exists
```bash
docker exec pac-mcmv-mvp-db-1 psql -U postgres -l | grep pac_mcmv
```

### Check Schema Exists
```bash
docker exec pac-mcmv-mvp-db-1 psql -U postgres -d pac_mcmv -c "\dn mcmv_v2"
```

### List MCMV Tables
```bash
docker exec pac-mcmv-mvp-db-1 psql -U postgres -d pac_mcmv -c "\dt mcmv_v2.*"
```

### Test Data Access
```bash
docker exec pac-mcmv-mvp-db-1 psql -U postgres -d pac_mcmv -c "SELECT COUNT(*) FROM mcmv_v2.projetos;"
```

---

## Common Connection Issues & Solutions

### Issue: "relation does not exist"
**Cause**: Using wrong schema or missing schema prefix
**Solution**: Always prefix tables with `mcmv_v2.`

### Issue: "database does not exist"
**Cause**: Wrong database name
**Solution**: Use `pac_mcmv` (not `mcmv_db` or others)

### Issue: "connection timeout"
**Cause**: Wrong host or container not accessible
**Solution**: Use `pac-mcmv-mvp-db-1` and ensure network connectivity

### Issue: "authentication failed"
**Cause**: Wrong credentials
**Solution**: Use `postgres` / `postgres123`

---

## Network Configuration

### Docker Networks
- v5 services connect via network: `pac-mcmv-mvp_default` (external)
- Database container is part of: `pac-mcmv-mvp_default`

### Service Dependencies
```yaml
# Any service accessing database MUST include:
networks:
  - mcmv-v5-network          # Internal network
  - pac-mcmv-mvp_default     # External network for DB access
```

---

## 🚨 CRITICAL REMINDER

**NEVER change these database settings without explicit user permission:**
- Database container name
- Database name (`pac_mcmv`)
- Schema name (`mcmv_v2`) 
- Credentials (`postgres` / `postgres123`)
- Port mappings

**ALWAYS verify database connectivity before deploying changes.**

**This configuration has been validated and is in production use.**

---

## Maintenance Notes

- Database container: `pac-mcmv-mvp-db-1` (shared with legacy v4 dashboard)
- Schema `mcmv_v2` contains production MCMV data
- Schema `public` contains PAC data (different project)
- Backup procedures should target `mcmv_v2` schema specifically

---

**Last Updated**: 2025-07-03  
**Version**: 1.0  
**Status**: PRODUCTION - DO NOT MODIFY