# Production Deployment Guide - MCMV Dashboard v5

## Prerequisites

- GitLab account with access to the repository
- Docker and Docker Compose installed on production server
- PostgreSQL database (can be external)
- Domain name and SSL certificates
- Environment variables configured

## Step 1: Prepare the Code

1. **Ensure all tests pass locally**
```bash
cd dashboard_v5
# Backend tests
cd backend && pytest
# Frontend checks
cd ../frontend && npm run lint && npm run type-check
```

2. **Update version numbers**
- Update version in `frontend/package.json`
- Update version in `backend/app/main.py` (if applicable)

3. **Build and test locally**
```bash
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up
```

## Step 2: Push to GitLab

1. **Create a new branch**
```bash
git checkout -b feature/dashboard-v5-production
```

2. **Add all files**
```bash
git add dashboard_v5/
git add .gitlab-ci.yml
git commit -m "feat: Add MCMV Dashboard v5 for production deployment"
```

3. **Push to GitLab**
```bash
git push origin feature/dashboard-v5-production
```

4. **Create Merge Request**
- Go to GitLab
- Create MR from `feature/dashboard-v5-production` to `main`
- Ensure CI/CD pipeline passes

## Step 3: Configure GitLab CI/CD Variables

In GitLab project settings > CI/CD > Variables, add:

```
# Docker Registry
CI_REGISTRY_USER=<gitlab-username>
CI_REGISTRY_PASSWORD=<gitlab-token>

# Database (Production)
DATABASE_URL=postgresql://user:password@host:5432/pac_mcmv

# Application
CORS_ORIGINS=https://your-domain.com
FRONTEND_PORT=80

# Optional: External services
SENTRY_DSN=<if-using-sentry>
```

## Step 4: Deploy to Production

### Option A: Automated Deployment (Recommended)

1. **Merge to main branch**
   - After approval, merge the MR
   - This triggers the production deployment pipeline

2. **Monitor deployment**
   - Go to GitLab > CI/CD > Pipelines
   - Watch the deployment stages
   - Check health checks pass

### Option B: Manual Deployment

1. **SSH to production server**
```bash
ssh user@production-server
```

2. **Clone/update repository**
```bash
git clone https://gitlab.com/your-org/your-repo.git
cd your-repo/dashboard_v5
git checkout main
git pull
```

3. **Create .env file**
```bash
cat > .env << EOF
DATABASE_URL=postgresql://user:password@host:5432/pac_mcmv
REDIS_HOST=redis
API_IMAGE=registry.gitlab.com/your-org/your-repo/api:latest
FRONTEND_IMAGE=registry.gitlab.com/your-org/your-repo/frontend:latest
CORS_ORIGINS=https://your-domain.com
EOF
```

4. **Deploy with Docker Compose**
```bash
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

## Step 5: Post-Deployment Verification

1. **Check container status**
```bash
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs --tail=50
```

2. **Verify endpoints**
```bash
# API health
curl https://your-domain.com/api/v5/health

# Frontend
curl https://your-domain.com/health

# Check specific endpoints
curl https://your-domain.com/api/v5/kpis/programa
```

3. **Monitor logs**
```bash
# API logs
docker logs -f mcmv-v5-api

# Frontend logs
docker logs -f mcmv-v5-frontend
```

## Step 6: Configure SSL/TLS

### Using Let's Encrypt with Certbot

1. **Install Certbot**
```bash
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx
```

2. **Obtain certificate**
```bash
sudo certbot --nginx -d your-domain.com
```

3. **Update nginx configuration**
- Certbot will automatically update nginx config
- Restart containers to apply changes

### Using CloudFlare or AWS Certificate Manager

- Configure at the load balancer level
- Ensure proper SSL termination

## Rollback Procedure

If issues occur:

1. **Quick rollback**
```bash
# Stop current deployment
docker-compose -f docker-compose.prod.yml down

# Deploy previous version
docker-compose -f docker-compose.prod.yml up -d --build
```

2. **Database rollback** (if schema changed)
```bash
# Restore from backup
psql $DATABASE_URL < backup.sql
```

## Monitoring and Maintenance

### Health Checks
- API: `https://your-domain.com/api/v5/health`
- Frontend: `https://your-domain.com/health`
- Metrics: `https://your-domain.com/api/v5/metrics`

### Log Rotation
```bash
# Add to crontab
0 0 * * * docker logs mcmv-v5-api 2>&1 | gzip > /var/log/mcmv-api-$(date +\%Y\%m\%d).log.gz
0 0 * * * docker logs mcmv-v5-frontend 2>&1 | gzip > /var/log/mcmv-frontend-$(date +\%Y\%m\%d).log.gz
```

### Backup Strategy
```bash
# Database backup (daily)
pg_dump $DATABASE_URL | gzip > backup-$(date +\%Y\%m\%d).sql.gz

# Redis backup (if persistent data)
docker exec mcmv-v5-redis redis-cli BGSAVE
```

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs api
docker-compose -f docker-compose.prod.yml logs frontend

# Check resources
docker system df
df -h
```

### API connection issues
```bash
# Test from frontend container
docker exec mcmv-v5-frontend curl http://api:8000/api/v5/health

# Check network
docker network ls
docker network inspect dashboard_v5_app-network
```

### Performance issues
```bash
# Check resource usage
docker stats

# Scale API workers
docker-compose -f docker-compose.prod.yml up -d --scale api=3
```

## Security Checklist

- [ ] Environment variables not in code
- [ ] Database credentials secure
- [ ] HTTPS enforced
- [ ] Security headers configured
- [ ] Rate limiting enabled
- [ ] Input validation active
- [ ] SQL injection prevention verified
- [ ] XSS protection enabled
- [ ] CORS properly configured
- [ ] Container images scanned for vulnerabilities

## Support

For issues:
1. Check application logs
2. Review GitLab CI/CD pipeline logs
3. Consult CLAUDE.md for architecture details
4. Contact DevOps team