#!/usr/bin/env bash
# Roll back a deployed Cloudflare service without changing the local checkout.
# Usage: rollback.sh <api|dashboard|site> <staging|production> [previous-pages-deployment-id]
set -euo pipefail

SERVICE="${1:?Usage: rollback.sh <api|dashboard|site> <staging|production> [pages-deployment-id]}"
ENVIRONMENT="${2:?Usage: rollback.sh <api|dashboard|site> <staging|production> [pages-deployment-id]}"
ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

if [[ "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "production" ]]; then
  echo "ERROR: environment must be staging or production" >&2
  exit 2
fi

cd "$ROOT_DIR"
echo "==> Rolling back ${SERVICE} in ${ENVIRONMENT}"

case "$SERVICE" in
  api)
    API_BASE_URL="${API_BASE_URL:-}"
    if [[ -z "$API_BASE_URL" ]]; then
      if [[ "$ENVIRONMENT" == "production" ]]; then
        API_BASE_URL="https://api.cashclaw.cc"
      else
        API_BASE_URL="https://mekong-engine-staging.workers.dev"
      fi
    fi
    cd "$ROOT_DIR/packages/mekong-engine"
    if [[ "$ENVIRONMENT" == "staging" ]]; then
      pnpm exec wrangler rollback --env staging --message "Automatic rollback after failed staging health check"
    else
      pnpm exec wrangler rollback --message "Automatic rollback after failed production health check"
    fi
    response="$(curl --fail --silent --show-error --retry 10 --retry-delay 2 --retry-all-errors "${API_BASE_URL%/}/health")"
    printf '%s' "$response" | jq -e '.status == "ok" and .database.connected == true and .bindings.d1 == true and .pilot.invite_only == true and .pilot.llm_only == true' >/dev/null
    ;;
  dashboard)
    DASHBOARD_URL="${DASHBOARD_URL:-}"
    if [[ -z "$DASHBOARD_URL" ]]; then
      echo "ERROR: set DASHBOARD_URL to the dashboard URL for this environment" >&2
      exit 2
    fi
    cd "$ROOT_DIR/apps/dashboard"
    if [[ "$ENVIRONMENT" == "staging" ]]; then
      pnpm exec wrangler rollback --env staging --message "Automatic rollback after failed staging health check"
    else
      pnpm exec wrangler rollback --message "Automatic rollback after failed production health check"
    fi
    page="$(curl --fail --silent --show-error --retry 10 --retry-delay 2 --retry-all-errors "$DASHBOARD_URL")"
    [[ "$page" == *'Synthetic'* || "$page" == *'synthetic'* ]]
    ;;
  site)
    if [[ "$ENVIRONMENT" != "production" ]]; then
      echo "ERROR: Cloudflare Pages rollback only supports a successful production deployment" >&2
      exit 2
    fi
    PREVIOUS_DEPLOYMENT_ID="${3:-${CF_PAGES_DEPLOYMENT_ID:-}}"
    CLOUDFLARE_API_TOKEN="${CLOUDFLARE_API_TOKEN:-${CF_API_TOKEN:-}}"
    CF_ACCOUNT_ID="${CF_ACCOUNT_ID:-${CLOUDFLARE_ACCOUNT_ID:-}}"
    SITE_URL="${SITE_URL:-https://mekongmind.com}"
    if [[ -z "$PREVIOUS_DEPLOYMENT_ID" || -z "$CLOUDFLARE_API_TOKEN" || -z "$CF_ACCOUNT_ID" ]]; then
      echo "ERROR: Pages rollback requires the previous deployment ID and Cloudflare credentials" >&2
      exit 2
    fi
    response="$(curl --fail --silent --show-error \
      -X POST \
      -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
      -H 'Content-Type: application/json' \
      "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/pages/projects/mekongmind/deployments/$PREVIOUS_DEPLOYMENT_ID/rollback")"
    printf '%s' "$response" | jq -e '.success == true' >/dev/null
    "$ROOT_DIR/ci/helpers/site-smoke.sh" "$SITE_URL"
    ;;
  *)
    echo "ERROR: unknown service '$SERVICE'; supported services are api, dashboard, site" >&2
    exit 2
    ;;
esac

echo "==> Rollback health check passed for ${SERVICE} (${ENVIRONMENT})"
