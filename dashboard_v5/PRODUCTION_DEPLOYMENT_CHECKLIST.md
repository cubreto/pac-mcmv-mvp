# Production Deployment Checklist - MCMV Dashboard v5

## Pre-Deployment Checklist

### 1. Code Quality & Testing
- [ ] All TypeScript/JavaScript linting passes
- [ ] No console.log statements in production code
- [ ] All tests pass (if applicable)
- [ ] Code review completed
- [ ] Security scan completed

### 2. Environment Variables
- [ ] Database credentials secured
- [ ] API keys properly configured
- [ ] Redis connection string set
- [ ] CORS origins configured for production
- [ ] Rate limiting configured

### 3. Build & Optimization
- [ ] Frontend built in production mode
- [ ] Assets minified and compressed
- [ ] Docker images optimized (multi-stage builds)
- [ ] Unused dependencies removed

### 4. Database
- [ ] Database migrations tested
- [ ] Backup strategy in place
- [ ] Connection pooling configured
- [ ] Indexes verified for performance

### 5. Security
- [ ] HTTPS/TLS certificates configured
- [ ] Security headers implemented
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention verified
- [ ] XSS protection enabled

### 6. Monitoring & Logging
- [ ] Application logs configured
- [ ] Error tracking setup
- [ ] Performance monitoring enabled
- [ ] Health check endpoints verified
- [ ] Metrics collection configured

### 7. Documentation
- [ ] README updated
- [ ] API documentation current
- [ ] Deployment guide complete
- [ ] Rollback procedure documented

### 8. Infrastructure
- [ ] Docker registry access configured
- [ ] Container orchestration ready
- [ ] Load balancer configured
- [ ] Auto-scaling policies set (if applicable)
- [ ] Backup and disaster recovery plan

## Files to Include in GitLab

### Essential Files
```
dashboard_v5/
├── backend/
│   ├── app/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── Dockerfile.prod
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   ├── package-lock.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── Dockerfile
│   ├── Dockerfile.prod
│   └── nginx.prod.conf
├── nginx/
│   └── conf.d/
│       └── default.conf
├── docker-compose.yml
├── docker-compose.prod.yml
├── .gitlab-ci.yml
├── .dockerignore
├── .gitignore
└── README.md
```

### Files to Exclude
- node_modules/
- dist/
- *.log
- .env files with secrets
- __pycache__/
- *.pyc
- .DS_Store
- *.swp
- *.swo

## Post-Deployment Verification

- [ ] Application accessible via production URL
- [ ] All API endpoints responding
- [ ] Database connections working
- [ ] Redis caching operational
- [ ] Monitoring dashboards active
- [ ] SSL certificate valid
- [ ] Performance benchmarks met