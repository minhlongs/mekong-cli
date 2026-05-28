#!/bin/bash
# 🚀 Start Gemini CLI with PayPal MCP environment
cd /Users/macbook/mekong-cli

# Load environment variables from .env
if [ -f .env ]; then
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
    echo "✅ Environment loaded from .env"
fi

# Verify PayPal credentials
if [ -n "$PAYPAL_CLIENT_ID" ]; then
    echo "✅ PayPal credentials found"
else
    echo "⚠️ PAYPAL_CLIENT_ID not set"
fi

# Start Gemini
echo "🚀 Starting Gemini CLI..."
exec gemini "$@"
