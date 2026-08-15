#!/usr/bin/env bash
# Deploy Mekong API Worker to Cloudflare Workers.
#
# Prereqs:
#   - wrangler installed:    npm install -g wrangler
#   - logged in:             wrangler login
#   - Cloudflare account:    account_id set in wrangler.toml
#   - Databases created:     mekong-sessions, mekong-audit
#   - KV namespaces created: RATE_LIMIT_KV, CACHE_KV
#   - Secrets set:           WEBHOOK_SECRET, JWT_SECRET (if needed)
#
# Usage:
#   ./scripts/deploy-api.sh                # deploy to production
#   ./scripts/deploy-api.sh --staging      # deploy to staging
#   ./scripts/deploy-api.sh --dry-run      # preview only
#
# Environment:
#   CF_API_TOKEN   - Cloudflare API token (optional, uses wrangler auth)
#   CF_ACCOUNT_ID  - Cloudflare account ID (falls back to wrangler.toml)
#
# Exit codes:
#   0 - Success
#   1 - Error (prerequisites, deployment failure, health check fail)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_DIR="${REPO_ROOT}/apps/api"
PROJECT_NAME="mekong-api"
ENVIRONMENT="production"
DRY_RUN=false
WAIT_FOR_HEALTH=true
HEALTH_CHECK_TIMEOUT=30

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --staging)
      ENVIRONMENT="staging"
      shift
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --no-wait)
      WAIT_FOR_HEALTH=false
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Deploy Mekong API Worker to Cloudflare Workers"
      echo ""
      echo "Options:"
      echo "  --staging      Deploy to staging environment"
      echo "  --dry-run      Preview deployment without executing"
      echo "  --no-wait      Don't wait for health check after deploy"
      echo "  -h, --help     Show this help message"
      echo ""
      echo "Examples:"
      echo "  $0                      # Deploy to production"
      echo "  $0 --staging           # Deploy to staging"
      echo "  $0 --dry-run           # See what would be deployed"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
  echo -e "${BLUE}[INFO]${NC} $*" >&2
}

log_success() {
  echo -e "${GREEN}[SUCCESS]${NC} $*" >&2
}

log_warn() {
  echo -e "${YELLOW}[WARN]${NC} $*" >&2
}

log_error() {
  echo -e "${RED}[ERROR]${NC} $*" >&2
}

section() {
  echo ""
  echo "========================================"
  echo "$*"
  echo "========================================"
}

# Check prerequisites
check_prerequisites() {
  section "Checking Prerequisites"

  # Check if wrangler is available
  if ! command -v wrangler &> /dev/null; then
    log_error "wrangler CLI not found. Install with: npm install -g wrangler"
    return 1
  fi

  local wrangler_version
  wrangler_version=$(wrangler --version 2>&1 || true)
  log_info "wrangler version: ${wrangler_version}"

  # Check if we're in the API directory
  if [[ ! -f "${API_DIR}/wrangler.toml" ]]; then
    log_error "wrangler.toml not found in ${API_DIR}"
    return 1
  fi

  # Check Node.js for building
  if ! command -v node &> /dev/null; then
    log_warn "Node.js not found. Skipping build step."
  else
    log_info "Node.js version: $(node --version)"
  fi

  log_success "Prerequisites check passed"
  return 0
}

# Run database migrations
run_migrations() {
  section "Running Database Migrations"

  cd "${API_DIR}"

  log_info "Applying D1 database migrations..."

  # Check if migrations exist
  if [[ ! -d "migrations/sessions" ]] || [[ ! -d "migrations/audit" ]]; then
    log_warn "Migration directories not found. Skipping migrations."
    return 0
  fi

  # Apply sessions database migration
  if [[ -f "migrations/sessions/001_initial.sql" ]]; then
    log_info "Applying sessions database migration..."
    if ! wrangler d1 execute mekong-sessions --file=migrations/sessions/001_initial.sql; then
      log_error "Failed to apply sessions migration"
      return 1
    fi
    log_success "Sessions database migration applied"
  else
    log_warn "Sessions migration file not found"
  fi

  # Apply audit database migration
  if [[ -f "migrations/audit/001_initial.sql" ]]; then
    log_info "Applying audit database migration..."
    if ! wrangler d1 execute mekong-audit --file=migrations/audit/001_initial.sql; then
      log_error "Failed to apply audit migration"
      return 1
    fi
    log_success "Audit database migration applied"
  else
    log_warn "Audit migration file not found"
  fi

  return 0
}

# Build the TypeScript code
build_api() {
  section "Building API Worker"

  cd "${API_DIR}"

  # Check if package.json exists and has build script
  if [[ ! -f "package.json" ]]; then
    log_warn "package.json not found. Skipping build."
    return 0
  fi

  # Check if node_modules exists
  if [[ ! -d "node_modules" ]]; then
    log_info "Installing dependencies..."
    npm ci || npm install
  fi

  log_info "Running TypeScript build..."
  if ! npm run build; then
    log_error "Build failed"
    return 1
  fi

  log_success "Build completed"
  return 0
}

# Deploy to Cloudflare Workers
deploy_worker() {
  section "Deploying API Worker"

  cd "${API_DIR}"

  local deploy_cmd=("wrangler" "deploy")

  if [[ "${ENVIRONMENT}" != "production" ]]; then
    deploy_cmd+=("--env" "${ENVIRONMENT}")
  fi

  if [[ "${DRY_RUN}" == "true" ]]; then
    log_info "DRY RUN: Would execute: ${deploy_cmd[*]}"
    log_info "From directory: ${API_DIR}"
    return 0
  fi

  log_info "Executing: ${deploy_cmd[*]}"
  log_info "Environment: ${ENVIRONMENT}"
  echo ""

  if ! "${deploy_cmd[@]}"; then
    log_error "Deployment failed"
    return 1
  fi

  log_success "Deployment completed"
  return 0
}

# Health check after deployment
health_check() {
  if [[ "${WAIT_FOR_HEALTH}" != "true" ]]; then
    log_info "Skipping health check (--no-wait)"
    return 0
  fi

  section "Post-Deployment Health Check"

  # Determine worker URL
  local worker_url=""
  if [[ "${ENVIRONMENT}" == "production" ]]; then
    worker_url="https://mekong-api.workers.dev/healthz"
    # Try to get account ID from wrangler.toml or env
    local account_id="${CF_ACCOUNT_ID:-}"
    if [[ -z "${account_id}" ]] && [[ -f "${API_DIR}/wrangler.toml" ]]; then
      account_id=$(grep -E '^account_id\s*=' "${API_DIR}/wrangler.toml" | head -1 | cut -d'=' -f2 | tr -d ' "')
    fi
    if [[ -n "${account_id}" ]]; then
      worker_url="https://mekong-api.${account_id}.workers.dev/healthz"
    fi
  else
    # Staging URL format
    worker_url="https://mekong-api-staging.workers.dev/healthz"
  fi

  log_info "Checking health endpoint: ${worker_url}"
  echo ""

  # Wait for deployment to propagate (max ${HEALTH_CHECK_TIMEOUT}s)
  local i
  for i in $(seq 1 ${HEALTH_CHECK_TIMEOUT}); do
    echo -n "  Attempt ${i}/${HEALTH_CHECK_TIMEOUT}... " >&2

    local http_code
    http_code=$(curl -s -o /dev/null -w "%{http_code}" "${worker_url}" 2>/dev/null || echo "000")

    if [[ "${http_code}" == "200" ]]; then
      echo "✅ Healthy!" >&2
      log_success "Worker is responding with HTTP 200"

      # Fetch and display health info
      local health_response
      health_response=$(curl -s "${worker_url}" 2>/dev/null || echo "{}")
      echo ""
      echo "Health response:"
      echo "${health_response}" | python3 -m json.tool 2>/dev/null || echo "${health_response}"

      return 0
    elif [[ "${http_code}" == "000" ]]; then
      echo "⏳ Waiting..." >&2
    else
      echo "⚠️  HTTP ${http_code}" >&2
    fi

    sleep 1
  done

  log_error "Health check failed - worker not responding with 200 OK after ${HEALTH_CHECK_TIMEOUT}s"
  log_info "URL: ${worker_url}"
  log_info "Check logs with: wrangler tail mekong-api${ENVIRONMENT:+ --env ${ENVIRONMENT}}"

  return 1
}

# Print deployment summary
print_summary() {
  section "Deployment Summary"

  echo "Environment:   ${ENVIRONMENT}"
  echo "Worker Name:   ${PROJECT_NAME}${ENVIRONMENT:+ (- ${ENVIRONMENT})}"
  echo "Directory:     ${API_DIR}"
  echo ""

  if [[ "${DRY_RUN}" == "true" ]]; then
    log_warn "This was a DRY RUN - no changes were made"
  else
    log_success "Deployment completed successfully!"
    echo ""
    echo "Next steps:"
    echo "  1. Verify health: curl ${worker_url:-<health-endpoint>}"
    echo "  2. View logs:     wrangler tail mekong-api${ENVIRONMENT:+ --env ${ENVIRONMENT}}"
    echo "  3. Test API:      curl https://api.cashclaw.cc/health"
    if [[ "${ENVIRONMENT}" == "production" ]]; then
      echo "  4. Monitor:       https://dash.cloudflare.com/workers/services"
    fi
  fi
  echo ""
}

# Main execution
main() {
  local exit_code=0

  log_info "Mekong API Worker Deployment"
  log_info "============================"
  log_info "Environment: ${ENVIRONMENT}"
  log_info "Directory:   ${API_DIR}"

  if [[ "${DRY_RUN}" == "true" ]]; then
    log_warn "RUNNING IN DRY-RUN MODE"
  fi

  # Execute deployment steps
  check_prerequisites || exit_code=$?

  if [[ ${exit_code} -eq 0 ]]; then
    run_migrations || exit_code=$?
  fi

  if [[ ${exit_code} -eq 0 ]]; then
    build_api || exit_code=$?
  fi

  if [[ ${exit_code} -eq 0 ]]; then
    deploy_worker || exit_code=$?
  fi

  if [[ ${exit_code} -eq 0 ]]; then
    health_check || exit_code=$?
  fi

  print_summary

  exit ${exit_code}
}

main
