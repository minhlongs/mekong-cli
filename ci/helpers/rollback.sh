#!/usr/bin/env sh
# ci/helpers/rollback.sh - Rollback to previous deployment
# Usage: rollback.sh <service> <environment> [previous_commit]
# Example: rollback.sh api production abc123def

set -euo pipefail

SERVICE="${1:?Usage: rollback.sh <service> <environment> [commit]}"
ENVIRONMENT="${2:?Usage: rollback.sh <service> <environment> [commit]}"
PREVIOUS_COMMIT="${3:-}"

echo "==> [ROLLBACK] Initiating rollback for ${SERVICE} in ${ENVIRONMENT}"

# If no commit provided, try to find previous deployment from git history
if [ -z "${PREVIOUS_COMMIT}" ]; then
  echo "  No commit specified, finding last successful deployment..."

  # Look for last successful deployment in git history (excluding current commit)
  # This assumes deployment commits are tagged or have specific messages
  PREVIOUS_COMMIT=$(git log --oneline --grep="deploy:${SERVICE}" --grep="Deploy ${SERVICE}" -n 2 --skip=1 2>/dev/null | head -1 | cut -d' ' -f1)

  if [ -z "${PREVIOUS_COMMIT}" ]; then
    echo "  ERROR: Could not automatically determine previous commit."
    echo "  Please provide commit SHA explicitly or ensure deployment commits are in history."
    exit 1
  fi

  echo "  Found previous commit: ${PREVIOUS_COMMIT}"
fi

echo "==> [ROLLBACK] Rolling back ${SERVICE} to commit ${PREVIOUS_COMMIT}"

case "${SERVICE}" in
  api)
    cd apps/api
    # Checkout the previous version
    git checkout "${PREVIOUS_COMMIT}" -- .

    # Reinstall dependencies if needed
    if [ -f "pnpm-lock.yaml" ]; then
      echo "  Restoring dependencies..."
      pnpm install --frozen-lockfile || pnpm install
    fi

    # Deploy to Cloudflare Workers
    echo "  Deploying to ${ENVIRONMENT}..."
    if [ "${ENVIRONMENT}" = "production" ]; then
      ENV_FLAG="--env production"
    else
      ENV_FLAG="--env staging"
    fi

    wrangler deploy ${ENV_FLAG}
    ;;

  dashboard)
    cd apps/dashboard
    git checkout "${PREVIOUS_COMMIT}" -- .

    echo "  Rebuilding Next.js app..."
    pnpm install || npm install
    npm run build

    echo "  Deploying to Cloudflare Pages..."
    # Deploy to Pages (preview by default, production if main branch)
    if [ "${ENVIRONMENT}" = "production" ]; then
      wrangler pages deploy .next/static --project-name=mekong-dashboard --branch=main
    else
      wrangler pages deploy .next/static --project-name=mekong-dashboard --branch=staging
    fi
    ;;

  *)
    echo "  ERROR: Unknown service '${SERVICE}'. Supported: api, dashboard"
    exit 1
    ;;
esac

echo "==> [ROLLBACK] ✅ Rollback completed for ${SERVICE}"
echo "  Service: ${SERVICE}"
echo "  Environment: ${ENVIRONMENT}"
echo "  Rolled back to: ${PREVIOUS_COMMIT}"

# Optional: Run smoke test after rollback
if [ -f "/Users/macbook/mekong-cli/ci/helpers/post-deploy-smoke.sh" ]; then
  echo "==> [ROLLBACK] Running post-rollback smoke test..."

  case "${SERVICE}" in
    api)
      HEALTH_URL="https://mekong-api.${CF_ACCOUNT_ID}.workers.dev/healthz"
      /Users/macbook/mekong-cli/ci/helpers/post-deploy-smoke.sh "api-${ENVIRONMENT}" "${HEALTH_URL}"
      ;;
    dashboard)
      HEALTH_URL="https://${ENVIRONMENT}.mekong-ide.pages.dev"
      /Users/macbook/mekong-cli/ci/helpers/post-deploy-smoke.sh "dashboard-${ENVIRONMENT}" "${HEALTH_URL}"
      ;;
  esac
fi
