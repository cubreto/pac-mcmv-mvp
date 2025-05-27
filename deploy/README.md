# AWS Deployment Guide

## Architecture
- **ECS Fargate**: Streamlit app container
- **RDS PostgreSQL**: Database 
- **ALB**: Load balancer
- **ECR**: Container registry

## Steps

1. **Setup ECR**
   ```bash
   aws ecr create-repository --repository-name pac-mcmv-mvp
   ```

2. **Build & Push**
   ```bash
   ./deploy/aws_deploy.sh
   aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_URI
   docker push $ECR_URI:latest
   ```

3. **Setup RDS**
   - Create PostgreSQL instance
   - Run `database/init.sql` 
   - Update DATABASE_URL

4. **Deploy ECS**
   - Create ECS cluster
   - Create task definition
   - Create service with ALB

5. **Run ETL**
   ```bash
   python etl/run_etl.py
   ```

Ready for production! 🎉
