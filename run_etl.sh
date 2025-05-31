#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 PAC-MCMV ETL Runner${NC}"
echo "========================"

# Check if Excel file exists - CORRECT FILENAME
EXCEL_FILE="data/raw/REUNI_Operações_Novo_PAC_OGU_Interno_CAIXA_21-05-2025.xlsx"

if [ ! -f "$EXCEL_FILE" ]; then
    echo -e "${RED}❌ Excel file not found!${NC}"
    echo -e "${YELLOW}Please place the REUNI Excel file at:${NC}"
    echo "   $EXCEL_FILE"
    echo ""
    echo "You can download it from CAIXA's system or copy from your Downloads:"
    echo "   cp ~/Downloads/REUNI_*.xlsx data/raw/"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running!${NC}"
    echo "Please start Docker Desktop first"
    exit 1
fi

# Check if database is running
if ! docker compose ps | grep -q "db.*running"; then
    echo -e "${YELLOW}Starting database...${NC}"
    docker compose up -d db
    sleep 5
fi

# Run the ETL
echo -e "${GREEN}📊 Running ETL...${NC}"
python etl/test_etl.py

echo -e "${GREEN}✅ ETL Complete!${NC}"
