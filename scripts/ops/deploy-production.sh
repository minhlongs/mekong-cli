#!/bin/bash
# deploy-production.sh - AgencyOS Production Deployment Script
set -e

echo "🚀 Starting AgencyOS Production Deployment"

# Validate environment
if [ ! -f ".env.production" ]; then
    echo "❌ .env.production file not found"
    exit 1
fi

# Build validation
echo "📦 Building applications..."
npm run build

# Run tests
echo "🧪 Running test suite..."
npm run test

# Environment validation
echo "🔍 Validating environment variables..."
node scripts/validate-environment.js

# Deploy to staging first
echo "🚀 Deploying to staging..."
npm run deploy:staging

# Health check staging
echo "🏥 Running health checks..."
npm run health-check

# Deploy to production
echo "🌟 Deploying to production..."
npm run deploy:production

# Final health check
echo "🏥 Final health verification..."
npm run health-check:production

echo "✅ Production deployment complete!"
echo "📊 Monitoring: https://monitoring.mekongmind.com"
echo "📈 Dashboard: https://dashboard.mekongmind.com"