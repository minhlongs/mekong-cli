#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Ensure we are at the project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo -e "${GREEN}🚀 Starting Full Stack Integration Test (Docker + DB)${NC}"

# 1. Start Docker Compose
echo "Starting services..."
cd infrastructure
docker compose up -d --build
cd ..

# 2. Wait for Postgres to be ready
echo "Waiting for Postgres..."
sleep 10 # Basic wait, could be improved with a loop checking pg_isready

# 3. Push Schema to DB (Running from host against localhost:5432 mapped port)
echo "Pushing DB Schema..."
export DATABASE_URL="postgresql://postgres:password@localhost:5432/agency_os?schema=public"
cd apps/engine
npx prisma db push
cd ../..

# 4. Send a Request
echo "Sending Chat Completion Request..."
RESPONSE=$(curl -s -X POST http://localhost:3000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dev-token" \
  -d '{
    "model": "gemini-1.5-pro",
    "messages": [{"role": "user", "content": "Hello from Integration Test!"}]
  }')

echo "Response: $RESPONSE"

# Extract Job ID (simple grep/sed as jq might not be installed, but assuming jq based on environment)
JOB_ID=$(echo $RESPONSE | jq -r '.id')
echo "Job ID: $JOB_ID"

# 5. Wait for Worker to Process
echo "Waiting for worker to process job..."
sleep 5

# 6. Check Job Status via API
echo "Checking Job Status API..."
STATUS_RESPONSE=$(curl -s -X GET http://localhost:3000/v1/jobs/$JOB_ID \
  -H "Authorization: Bearer dev-token")
echo "Status Response: $STATUS_RESPONSE"

# 7. Verify DB State
echo "Verifying Database State..."
node scripts/verify_db_integration.mjs

# 8. Cleanup (Optional, commented out for debugging)
# echo "Stopping services..."
# cd infrastructure && docker compose down && cd ..

echo -e "${GREEN}✅ Test Completed Successfully${NC}"
