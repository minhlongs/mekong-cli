#!/usr/bin/env sh
# ci/helpers/post-deploy-smoke.sh - Post-deployment health checks
# Usage: post-deploy-smoke.sh <service> <url>
# Example: post-deploy-smoke.sh api https://mekong-api.workers.dev/healthz

set -euo pipefail

SERVICE="${1:?Usage: post-deploy-smoke.sh <service> <url>}"
URL="${2:?Usage: post-deploy-smoke.sh <service> <url>}"
MAX_RETRIES=30
RETRY_INTERVAL=1

echo "==> [SMOKE: ${SERVICE}] Checking health endpoint: ${URL}"
START_TIME=$(date +%s)

for i in $(seq 1 ${MAX_RETRIES}); do
  echo "Attempt ${i}/${MAX_RETRIES}..."

  # Get HTTP status code
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${URL}" || echo "000")

  if [ "${HTTP_CODE}" = "200" ]; then
    # Try to get response body for additional validation
    RESPONSE=$(curl -s "${URL}" || echo "{}")

    # Check if response is valid JSON (optional)
    if echo "${RESPONSE}" | jq . > /dev/null 2>&1; then
      echo "==> [SMOKE: ${SERVICE}] ✅ Healthy! Response:"
      echo "${RESPONSE}" | jq .
    else
      echo "==> [SMOKE: ${SERVICE}] ✅ Healthy (non-JSON response received)"
    fi

    END_TIME=$(date +%s)
    ELAPSED=$((END_TIME - START_TIME))
    echo "==> [SMOKE: ${SERVICE}] PASSED in ${ELAPSED}s"
    exit 0
  fi

  # Show non-200 responses
  echo "  HTTP ${HTTP_CODE} - waiting ${RETRY_INTERVAL}s..."
  sleep ${RETRY_INTERVAL}
done

echo "==> [SMOKE: ${SERVICE}] ❌ FAILED: Health endpoint did not return 200 after ${MAX_RETRIES} attempts"
echo "URL: ${URL}"
exit 1
