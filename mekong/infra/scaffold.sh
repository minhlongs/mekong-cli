#!/bin/bash
# Mekong CLI — Infrastructure Scaffold
# Usage: bash mekong/infra/scaffold.sh <project-name> <scale>
# Scales: solo | startup | growth | scale

set -euo pipefail

PROJECT="${1:?Usage: scaffold.sh <project-name> <scale>}"
SCALE="${2:-startup}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEMPLATES="$SCRIPT_DIR/templates"

echo "🏯 Mekong Infra Scaffold: $PROJECT ($SCALE)"
echo "=========================================="

mkdir -p "$PROJECT"

case "$SCALE" in
  solo)
    echo "📦 Solo: frontend only"
    mkdir -p "$PROJECT/frontend"
    cp -r "$TEMPLATES/cf-pages/"* "$PROJECT/frontend/"
    sed -i '' "s/{{PROJECT_NAME}}/$PROJECT/g" "$PROJECT/frontend/wrangler.toml"
    ;;

  startup)
    echo "📦 Startup: frontend + edge API"
    mkdir -p "$PROJECT/frontend" "$PROJECT/api"
    cp -r "$TEMPLATES/cf-pages/"* "$PROJECT/frontend/"
    cp -r "$TEMPLATES/cf-workers/"* "$PROJECT/api/"
    sed -i '' "s/{{PROJECT_NAME}}/$PROJECT/g" "$PROJECT/frontend/wrangler.toml" "$PROJECT/api/wrangler.toml"
    ;;

  growth)
    echo "📦 Growth: frontend + edge API + app"
    mkdir -p "$PROJECT/frontend" "$PROJECT/api" "$PROJECT/app"
    cp -r "$TEMPLATES/cf-pages/"* "$PROJECT/frontend/"
    cp -r "$TEMPLATES/cf-workers/"* "$PROJECT/api/"
    cp -r "$TEMPLATES/vercel-app/"* "$PROJECT/app/"
    sed -i '' "s/{{PROJECT_NAME}}/$PROJECT/g" "$PROJECT/frontend/wrangler.toml" "$PROJECT/api/wrangler.toml"
    ;;

  scale)
    echo "📦 Scale: all 4 layers"
    mkdir -p "$PROJECT/frontend" "$PROJECT/api" "$PROJECT/app" "$PROJECT/backend"
    cp -r "$TEMPLATES/cf-pages/"* "$PROJECT/frontend/"
    cp -r "$TEMPLATES/cf-workers/"* "$PROJECT/api/"
    cp -r "$TEMPLATES/vercel-app/"* "$PROJECT/app/"
    cp -r "$TEMPLATES/fly-backend/"* "$PROJECT/backend/"
    sed -i '' "s/{{PROJECT_NAME}}/$PROJECT/g" "$PROJECT/frontend/wrangler.toml" "$PROJECT/api/wrangler.toml" "$PROJECT/backend/fly.toml"
    ;;

  *)
    echo "❌ Unknown scale: $SCALE (use: solo|startup|growth|scale)"
    exit 1
    ;;
esac

echo ""
echo "✅ Scaffolded: $PROJECT/"
ls -la "$PROJECT/"
echo ""
echo "Next steps:"
echo "  cd $PROJECT/frontend && npm install && npm run dev"
