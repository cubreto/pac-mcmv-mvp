#!/bin/bash
# AWS Deployment Script for PAC-MCMV MVP

echo "🚀 Starting AWS deployment for PAC-MCMV MVP..."

# Build and tag Docker image
echo "🐳 Building Docker image..."
docker build -t pac-mcmv-mvp .

# Tag for ECR (replace with your ECR URI)
ECR_URI="your-account.dkr.ecr.us-east-1.amazonaws.com/pac-mcmv-mvp"
docker tag pac-mcmv-mvp:latest $ECR_URI:latest

echo "📦 Image built and tagged"
echo "Next steps:"
echo "1. Push to ECR: docker push $ECR_URI:latest"
echo "2. Deploy to ECS/Fargate"
echo "3. Set up RDS PostgreSQL"
echo "4. Configure environment variables"

echo "✅ Build complete - ready for AWS deployment"
