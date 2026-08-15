#!/bin/bash
# Mekong Cloudflare Deployment Setup Script
# This script initializes the Cloudflare deployment infrastructure

set -e

echo "========================================"
echo "Mekong Cloudflare Deployment Setup"
echo "========================================"
echo ""

# Check prerequisites
echo "Checking prerequisites..."

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 22+"
    exit 1
fi
NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js version 18+ required. Found: $(node --version)"
    exit 1
fi
echo "✓ Node.js $(node --version)"

# Check pnpm
if ! command -v pnpm &> /dev/null; then
    echo "❌ pnpm not found. Installing pnpm..."
    npm install -g pnpm@9.15.0
else
    echo "✓ pnpm $(pnpm --version)"
fi

# Check Wrangler
if ! command -v wrangler &> /dev/null; then
    echo "⚠️  Wrangler CLI not found."
    echo "   Install with: npm install -g wrangler"
    echo "   Then login: wrangler login"
else
    echo "✓ Wrangler $(wrangler --version)"
fi

echo ""
echo "Installing dependencies..."
pnpm install

echo ""
echo "Setting up API worker databases..."

# Check if wrangler is available for db setup
if command -v wrangler &> /dev/null; then
    echo "To create D1 databases, run:"
    echo "  cd apps/api"
    echo "  wrangler d1 create mekong-sessions"
    echo "  wrangler d1 create mekong-audit"
    echo ""
    echo "Then update apps/api/wrangler.toml with the database IDs."
    echo ""
    echo "To create KV namespaces:"
    echo "  wrangler kv:namespace create RATE_LIMIT_KV"
    echo "  wrangler kv:namespace create CACHE_KV"
    echo ""
else
    echo "⚠️  Install Wrangler to set up databases and KV namespaces."
fi

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Configure Cloudflare credentials:"
echo "   - Login: wrangler login"
echo "   - Get your account ID from Cloudflare dashboard"
echo ""
echo "2. Create databases and KV namespaces (see above)"
echo ""
echo "3. Set secrets for API worker:"
echo "   cd apps/api && wrangler secret put WEBHOOK_SECRET"
echo ""
echo "4. Test locally:"
echo "   cd apps/dashboard && pnpm dev"
echo "   cd apps/api && pnpm dev"
echo ""
echo "5. Deploy to staging:"
echo "   cd apps/api && npm run deploy:staging"
echo ""
echo "6. View documentation:"
echo "   cat CLOUD_FLARE_DEPLOYMENT.md"
echo "   cat docs/deployment-guide.md"
echo ""
