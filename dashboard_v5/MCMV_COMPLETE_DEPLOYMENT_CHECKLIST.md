# MCMV Dashboard v5 - Complete Deployment Checklist

## Pre-Deployment Checklist

### 1. Code Preparation ✓
- [x] GitLab CI/CD pipeline configured (`.gitlab-ci.yml`)
- [x] Production Docker Compose file (`docker-compose.prod.yml`)
- [x] Production Dockerfiles for optimized builds
- [x] Environment configuration templates
- [x] Security configurations (nginx headers, CORS)
- [x] Production deployment guide documentation

### 2. Files to Add to GitLab Repository

```
dashboard_v5/
├── .gitlab-ci.yml              # CI/CD pipeline configuration
├── .gitignore                  # Ignore sensitive files
├── docker-compose.prod.yml     # Production deployment
├── docker-compose.v5.yml       # Development deployment
├── README.md                   # Project documentation
├── PRODUCTION_DEPLOYMENT_GUIDE.md  # Deployment instructions
├── backend/
│   ├── Dockerfile             # Development Dockerfile
│   ├── Dockerfile.prod        # Production Dockerfile  
│   ├── requirements.txt       # Python dependencies
│   └── app/                   # FastAPI application
├── frontend/
│   ├── Dockerfile             # Development Dockerfile
│   ├── Dockerfile.prod        # Production Dockerfile
│   ├── nginx.conf             # Development nginx
│   ├── nginx.prod.conf        # Production nginx
│   ├── nginx-security.conf    # Security headers
│   ├── package.json           # Node dependencies
│   └── src/                   # React application
└── database/
    ├── *.sql                  # Migration scripts
    └── README.md              # Database documentation
```

### 3. GitLab CI/CD Variables to Configure

In GitLab project settings > CI/CD > Variables:

```bash
# Docker Registry
CI_REGISTRY_USER              # GitLab username
CI_REGISTRY_PASSWORD          # GitLab access token

# Production Environment
PROD_SERVER_HOST              # Production server IP/hostname
PROD_SERVER_USER              # SSH user for deployment
PROD_SERVER_SSH_KEY           # Private SSH key (file type)

# Database Configuration
DATABASE_URL                  # PostgreSQL connection string
DB_HOST                       # Database host
DB_PORT                       # Database port (5432)
DB_NAME                       # Database name (pac_mcmv)
DB_USER                       # Database user
DB_PASSWORD                   # Database password

# Application Configuration  
CORS_ORIGINS                  # Allowed origins (https://your-domain.com)
SECRET_KEY                    # Application secret key
ENVIRONMENT                   # production
LOG_LEVEL                     # INFO

# Optional Services
SENTRY_DSN                    # Error tracking (optional)
```

### 4. Pre-Deployment Verification

- [ ] All tests pass locally
- [ ] Docker images build successfully
- [ ] Database migrations tested on staging
- [ ] Environment variables documented
- [ ] SSL certificates ready (Let's Encrypt or other)
- [ ] Domain name configured
- [ ] Firewall rules configured

### 5. Database Preparation

```bash
# Apply all migrations in order
psql -h $DB_HOST -U $DB_USER -d $DB_NAME < database/001_business_logic_foundation.sql
psql -h $DB_HOST -U $DB_USER -d $DB_NAME < database/002_create_refresh_function.sql
psql -h $DB_HOST -U $DB_USER -d $DB_NAME < database/003_create_quality_history.sql
psql -h $DB_HOST -U $DB_USER -d $DB_NAME < database/004_create_previsao_entrega_view.sql
psql -h $DB_HOST -U $DB_USER -d $DB_NAME < database/005_create_etl_quality_tables.sql
psql -h $DB_HOST -U $DB_USER -d $DB_NAME < database/006_fix_critical_data_issues.sql
psql -h $DB_HOST -U $DB_USER -d $DB_NAME < database/007_create_quality_procedures.sql
psql -h $DB_HOST -U $DB_USER -d $DB_NAME < database/008_add_rural_filter_columns.sql
psql -h $DB_HOST -U $DB_USER -d $DB_NAME < database/009_create_dados_prioritarios_materialized_views.sql

# Refresh materialized views
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT * FROM mcmv_v2.refresh_all_materialized_views();"
```

## Deployment Steps

### 1. Push to GitLab
```bash
# Create feature branch
git checkout -b feature/dashboard-v5-production

# Add all v5 files
git add dashboard_v5/
git add .gitlab-ci.yml

# Commit
git commit -m "feat: Add MCMV Dashboard v5 for production deployment"

# Push
git push origin feature/dashboard-v5-production
```

### 2. Create Merge Request
- Create MR from feature branch to main
- Wait for CI/CD pipeline to pass
- Get approval from team
- Merge to main (triggers deployment)

### 3. Monitor Deployment
- Watch GitLab CI/CD pipeline
- Check deployment logs
- Verify health endpoints

### 4. Post-Deployment Verification

```bash
# Check services are running
curl https://your-domain.com/api/v5/health
curl https://your-domain.com/health

# Test API endpoints
curl https://your-domain.com/api/v5/kpis/programa
curl https://your-domain.com/api/v5/projetos/regional

# Monitor logs
docker logs -f mcmv-v5-api
docker logs -f mcmv-v5-frontend
```

## Rollback Plan

### Quick Rollback
```bash
# SSH to production server
ssh user@production-server

# Stop current deployment
cd /path/to/deployment
docker-compose -f docker-compose.prod.yml down

# Checkout previous version
git checkout <previous-commit>

# Redeploy
docker-compose -f docker-compose.prod.yml up -d
```

### Database Rollback
```bash
# Only if schema changes were made
psql $DATABASE_URL < backup.sql
```

## Security Checklist

- [ ] Environment variables not in code repository
- [ ] Database credentials secured
- [ ] HTTPS/SSL configured
- [ ] Security headers enabled
- [ ] CORS properly configured
- [ ] Rate limiting active
- [ ] Input validation verified
- [ ] SQL injection prevention tested
- [ ] Container images scanned
- [ ] Firewall rules applied

## Monitoring Setup

### 1. Health Checks
- Frontend: https://your-domain.com/health
- API: https://your-domain.com/api/v5/health
- Metrics: https://your-domain.com/api/v5/metrics

### 2. Log Aggregation
```bash
# Add to crontab for log rotation
0 0 * * * docker logs mcmv-v5-api 2>&1 | gzip > /var/log/mcmv-api-$(date +\%Y\%m\%d).log.gz
0 0 * * * docker logs mcmv-v5-frontend 2>&1 | gzip > /var/log/mcmv-frontend-$(date +\%Y\%m\%d).log.gz
```

### 3. Backup Schedule
```bash
# Database backup (daily at 2 AM)
0 2 * * * pg_dump $DATABASE_URL | gzip > /backup/mcmv-db-$(date +\%Y\%m\%d).sql.gz

# Redis backup (if using persistence)
0 3 * * * docker exec mcmv-v5-redis redis-cli BGSAVE
```

## Support Contacts

- DevOps Team: [Contact Info]
- Database Admin: [Contact Info]
- Development Team: rangel@digiteam.cloud
- Emergency: [24/7 Contact]

## Final Checklist

- [ ] All services healthy
- [ ] SSL/HTTPS working
- [ ] All endpoints responding
- [ ] Monitoring configured
- [ ] Backups scheduled
- [ ] Documentation updated
- [ ] Team notified

---
**Created**: 2025-08-12
**Version**: 1.0
**Status**: Ready for deployment