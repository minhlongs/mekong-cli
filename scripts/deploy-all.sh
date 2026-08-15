#!/usr/bin/env bash
#
# Unified Deployment Script for Mekong IDE
# Deploys all components in the correct order: dashboard, API, workers
#
# Usage:
#   ./scripts/deploy-all.sh                    # Deploy everything to production
#   ./scripts/deploy-all.sh --staging         # Deploy all to staging
#   ./scripts/deploy-all.sh --dashboard       # Deploy dashboard only
#   ./scripts/deploy-all.sh --api            # Deploy API only
#   ./scripts/deploy-all.sh --workers        # Deploy workers only
#   ./scripts/deploy-all.sh --dry-run        # Preview without deploying
#
# Examples:
#   ./scripts/deploy-all.sh                           # Full prod deployment
#   ./scripts/deploy-all.sh --staging --api --workers # Staging API + workers
#   ./scripts/deploy-all.sh --dashboard --dry-run     # Check dashboard deploy
#
# Environment variables:
#   CF_API_TOKEN    Cloudflare API token (optional, uses wrangler auth)
#   CF_ACCOUNT_ID   Cloudflare account ID (falls back to wrangler.toml)
#   SKIP_DASHBOARD  Set to "1" to skip dashboard
#   SKIP_API        Set to "1" to skip API
#   SKIP_WORKERS    Set to "1" to skip workers

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Default configuration
DEPLOY_DASHBOARD=true
DEPLOY_API=true
DEPLOY_WORKERS=true
ENVIRONMENT="production"
DRY_RUN=false
WAIT_FOR_HEALTH=true
PARALLEL=false
VERBOSE=false

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $*" >&2; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*" >&2; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*" >&2; }
log_error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

section() {
  echo ""
  echo "========================================"
  echo "$*"
  echo "========================================"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --staging)
      ENVIRONMENT="staging"
      shift
      ;;
    --dashboard)
      DEPLOY_API=false
      DEPLOY_WORKERS=false
      shift
      ;;
    --api)
      DEPLOY_DASHBOARD=false
      DEPLOY_WORKERS=false
      shift
      ;;
    --workers)
      DEPLOY_DASHBOARD=false
      DEPLOY_API=false
      shift
      ;;
    --all)
      DEPLOY_DASHBOARD=true
      DEPLOY_API=true
      DEPLOY_WORKERS=true
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
    --parallel)
      PARALLEL=true
      shift
      ;;
    -v|--verbose)
      VERBOSE=true
      shift
      ;;
    -h|--help)
      cat <<EOF
Usage: $0 [OPTIONS]

Unified Deployment Script for Mekong IDE

Deploys all components in the correct order: dashboard, API, workers

Options:
  --staging        Deploy to staging environment (default: production)
  --dashboard      Deploy dashboard only
  --api            Deploy API only
  --workers        Deploy workers only
  --all            Deploy all components (default)
  --dry-run        Preview without deploying
  --no-wait        Don't wait for health checks after deploy
  --parallel       Deploy independent components in parallel
  -v, --verbose    Show detailed output
  -h, --help       Show this help message

Examples:
  $0                           # Full production deployment
  $0 --staging                # Full staging deployment
  $0 --dashboard              # Deploy dashboard only
  $0 --api --staging          # Deploy API to staging only
  $0 --workers --dry-run      # Preview worker deployment

Environment variables:
  CF_API_TOKEN    Cloudflare API token (optional)
  CF_ACCOUNT_ID   Cloudflare account ID (fallback from wrangler.toml)
  SKIP_DASHBOARD  Set to "1" to skip dashboard
  SKIP_API        Set to "1" to skip API
  SKIP_WORKERS    Set to "1" to skip workers
EOF
      exit 0
      ;;
    *)
      log_error "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Allow environment variable overrides
[[ "${SKIP_DASHBOARD:-}" == "1" ]] && DEPLOY_DASHBOARD=false
[[ "${SKIP_API:-}" == "1" ]] && DEPLOY_API=false
[[ "${SKIP_WORKERS:-}" == "1" ]] && DEPLOY_WORKERS=false

# Script paths
DEPLOY_DASHBOARD_SCRIPT="${REPO_ROOT}/scripts/deploy-dashboard.sh"
DEPLOY_API_SCRIPT="${REPO_ROOT}/scripts/deploy-api.sh"
DEPLOY_WORKERS_SCRIPT="${REPO_ROOT}/scripts/deploy-workers.sh"

# Check what we're deploying
section "Deployment Plan"
echo "Environment:   ${ENVIRONMENT}"
echo "Dashboard:     ${DEPLOY_DASHBOARD}"
echo "API:           ${DEPLOY_API}"
echo "Workers:       ${DEPLOY_WORKERS}"
echo "Dry run:       ${DRY_RUN}"
echo "Wait for health: ${WAIT_FOR_HEALTH}"
if [[ "${PARALLEL}" == "true" ]] && [[ "${DEPLOY_DASHBOARD}" == "true" ]] && [[ "${DEPLOY_API}" == "true" ]]; then
  echo "Parallel:      Yes (dashboard + API can deploy simultaneously)"
fi
echo ""

# Confirm before proceeding if not dry-run
if [[ "${DRY_RUN}" != "true" ]]; then
  read -p "Proceed with deployment? (YES/no): " CONFIRM
  if [[ "${CONFIRM:-YES}" != "YES" ]]; then
    log_info "Deployment cancelled"
    exit 0
  fi
fi

# Track overall status
OVERALL_EXIT_CODE=0

# Deployment functions
deploy_dashboard() {
  section "Deploying Dashboard"

  if [[ ! -f "${DEPLOY_DASHBOARD_SCRIPT}" ]]; then
    log_error "Dashboard deploy script not found: ${DEPLOY_DASHBOARD_SCRIPT}"
    return 1
  fi

  if [[ "${DRY_RUN}" == "true" ]]; then
    log_info "DRY RUN: Would execute: ${DEPLOY_DASHBOARD_SCRIPT} ${ENVIRONMENT}"
    return 0
  fi

  local dashboard_args=()
  if [[ "${ENVIRONMENT}" != "production" ]]; then
    dashboard_args=(--preview)
  fi

  log_info "Executing: ${DEPLOY_DASHBOARD_SCRIPT} ${dashboard_args[*]}"
  if "${DEPLOY_DASHBOARD_SCRIPT}" "${dashboard_args[@]}"; then
    log_success "Dashboard deployed"
    return 0
  else
    log_error "Dashboard deployment failed"
    return 1
  fi
}

deploy_api() {
  section "Deploying API Worker"

  if [[ ! -f "${DEPLOY_API_SCRIPT}" ]]; then
    log_error "API deploy script not found: ${DEPLOY_API_SCRIPT}"
    return 1
  fi

  if [[ "${DRY_RUN}" == "true" ]]; then
    log_info "DRY RUN: Would execute: ${DEPLOY_API_SCRIPT} --${ENVIRONMENT}"
    return 0
  fi

  local api_args=()
  if [[ "${ENVIRONMENT}" == "staging" ]]; then
    api_args=(--staging)
  fi
  if [[ "${WAIT_FOR_HEALTH}" != "true" ]]; then
    api_args+=(--no-wait)
  fi

  log_info "Executing: ${DEPLOY_API_SCRIPT} ${api_args[*]}"
  if "${DEPLOY_API_SCRIPT}" "${api_args[@]}"; then
    log_success "API Worker deployed"
    return 0
  else
    log_error "API Worker deployment failed"
    return 1
  fi
}

deploy_workers() {
  section "Deploying Workers"

  if [[ ! -f "${DEPLOY_WORKERS_SCRIPT}" ]]; then
    log_warn "Workers deploy script not found: ${DEPLOY_WORKERS_SCRIPT}"
    log_info "Workers (mekong-engine, zalo-parser) can be deployed individually"
    return 0
  fi

  if [[ "${DRY_RUN}" == "true" ]]; then
    log_info "DRY RUN: Would execute: ${DEPLOY_WORKERS_SCRIPT} ${ENVIRONMENT}"
    return 0
  fi

  local workers_args=()
  [[ "${ENVIRONMENT}" == "staging" ]] && workers_args=(--staging)

  log_info "Executing: ${DEPLOY_WORKERS_SCRIPT} ${workers_args[*]}"
  if "${DEPLOY_WORKERS_SCRIPT}" "${workers_args[@]}"; then
    log_success "Workers deployed"
    return 0
  else
    log_error "Workers deployment failed"
    return 1
  fi
}

# Execute deployment plan
main() {
  section "Mekong IDE - Unified Deployment"
  log_info "Starting deployment at: $(date '+%Y-%m-%d %H:%M:%S')"

  # Track individual component statuses
  local dashboard_status=0
  local api_status=0
  local workers_status=0

  if [[ "${PARALLEL}" == "true" ]] && [[ "${DEPLOY_DASHBOARD}" == "true" ]] && [[ "${DEPLOY_API}" == "true" ]]; then
    # Parallel deployment for independent components
    section "Deploying Dashboard and API in parallel"

    if [[ "${DRY_RUN}" != "true" ]]; then
      # Run in background
      deploy_dashboard &
      local dashboard_pid=$!
      deploy_api &
      local api_pid=$!

      # Wait for both
      wait ${dashboard_pid} || dashboard_status=$?
      wait ${api_pid} || api_status=$?
    else
      deploy_dashboard
      dashboard_status=$?
      deploy_api
      api_status=$?
    fi

    if [[ "${DEPLOY_WORKERS}" == "true" ]]; then
      deploy_workers
      workers_status=$?
    fi
  else
    # Sequential deployment
    if [[ "${DEPLOY_DASHBOARD}" == "true" ]]; then
      deploy_dashboard
      dashboard_status=$?
    fi

    if [[ "${DEPLOY_API}" == "true" ]]; then
      deploy_api
      api_status=$?
    fi

    if [[ "${DEPLOY_WORKERS}" == "true" ]]; then
      deploy_workers
      workers_status=$?
    fi
  fi

  # Summary
  section "Deployment Summary"
  echo "Dashboard:  $( [[ ${dashboard_status} -eq 0 ]] && echo -e "${GREEN}✅ Success${NC}" || echo -e "${RED}❌ Failed${NC}" )"
  echo "API:        $( [[ ${api_status} -eq 0 ]] && echo -e "${GREEN}✅ Success${NC}" || echo -e "${RED}❌ Failed${NC}" )"
  echo "Workers:    $( [[ ${workers_status} -eq 0 ]] && echo -e "${GREEN}✅ Success${NC}" || echo -e "${RED}❌ Failed${NC}" )"
  echo ""

  # Determine overall exit code
  if [[ ${dashboard_status} -eq 0 ]] && [[ ${api_status} -eq 0 ]] && [[ ${workers_status} -eq 0 ]]; then
    log_success "All deployments completed successfully!"
    log_info "Completed at: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    echo "Verification:"
    echo "  Dashboard:  https://ide.mekongmind.com"
    echo "  API:        https://api.cashclaw.cc/health"
    echo "  Workers:    wrangler tail"
    echo ""
    return 0
  else
    log_error "Some deployments failed"
    log_info "Completed at: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    echo "Troubleshooting:"
    echo "  - Check individual deployment logs above"
    echo "  - View Cloudflare dashboard: https://dash.cloudflare.com"
    echo "  - Check wrangler logs: wrangler tail <worker-name>"
    echo "  - Run rollback: make rollback-full"
    echo ""
    return 1
  fi
}

main
