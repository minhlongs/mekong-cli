#!/bin/bash

# scripts/deploy-vps.sh
# Deploys the AgencyOS stack to a VPS using Docker Compose

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Starting AgencyOS Production Deployment...${NC}"

# 1. Check for Docker
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed."
    exit 1
fi

# 2. Check for .env.prod
if [ ! -f .env.prod ]; then
    echo "Creating .env.prod from example..."
    if [ -f .env ]; then
        cp .env .env.prod
    else
        echo "Error: No .env file found to copy."
        exit 1
    fi
fi

# 3. Build Images
echo -e "${BLUE}📦 Building Docker images...${NC}"
docker compose -f docker-compose.prod.yml build

# 4. Start Services
echo -e "${BLUE}🔥 Starting services...${NC}"
docker compose -f docker-compose.prod.yml up -d

# 5. Verify
echo -e "${BLUE}🔍 Verifying deployment...${NC}"
sleep 5
docker compose -f docker-compose.prod.yml ps

echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo -e "   - Engine: http://localhost:3000"
echo -e "   - API:    http://localhost:8000"
