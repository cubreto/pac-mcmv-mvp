#!/bin/bash

echo "🚀 PAC-MCMV AWS Deployment Script"
echo "=================================="

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

# Options:
# 1. Deploy to EC2
# 2. Deploy to ECS/Fargate
# 3. Deploy to Elastic Beanstalk

echo "Deployment options:"
echo "1. EC2 with Docker Compose"
echo "2. ECS with Fargate"
echo "3. Elastic Beanstalk"
echo ""
read -p "Select deployment option (1-3): " option

case $option in
    1)
        echo "Deploying to EC2..."
        # EC2 deployment steps
        ;;
    2)
        echo "Deploying to ECS..."
        # ECS deployment steps
        ;;
    3)
        echo "Deploying to Elastic Beanstalk..."
        # EB deployment steps
        ;;
    *)
        echo "Invalid option"
        exit 1
        ;;
esac
