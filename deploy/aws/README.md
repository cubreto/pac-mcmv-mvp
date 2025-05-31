# PAC-MCMV AWS Deployment Guide

## Prerequisites

1. AWS CLI installed and configured
2. Docker installed locally
3. Access to AWS account: DIGITEAM_BI_IA

## Quick Start

1. Copy `.env.template` to `.env` and fill in values
2. Run `./deploy.sh` and select deployment option

## Architecture Options

### Option 1: EC2 with Docker Compose (Simplest)
- Single EC2 instance
- Docker Compose manages containers
- Good for MVP/testing

### Option 2: ECS with Fargate (Scalable)
- Managed container service
- Auto-scaling capabilities
- Better for production

### Option 3: Elastic Beanstalk (Managed)
- Fully managed platform
- Easy deployment
- Good balance of simplicity and features

## Estimated Costs

- EC2 t3.medium: ~$30/month
- RDS PostgreSQL: ~$15/month
- Load Balancer: ~$20/month
- Total: ~$65/month for MVP

## Security Considerations

- Use AWS Secrets Manager for credentials
- Enable VPC for database isolation
- Use HTTPS with ACM certificates
- Enable CloudWatch logging

## Data Upload

The REUNI Excel file needs to be uploaded after deployment:
1. SSH into EC2 or use ECS Exec
2. Copy Excel file to container
3. Run ETL script
