#!/usr/bin/env bash
#
# Deploy Cloudflare Workers (mekong-engine, zalo-parser)
#
# Usage:
#   ./scripts/deploy-workers.sh                # Deploy all workers to production
#   ./scripts/deploy-workers.sh --staging     # Deploy all to staging
#   ./scripts/deploy-workers.sh --dry-run     # Preview without deploying
#
# Environment variables:
#   CF_API_TOKEN    Cloudflare API token (optional)
#   CF_ACCOUNT_ID   Cloudflare account ID

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Configuration
ENVIRONMENT="production"
DRY_RUN=false
VERBOSE=false

# Workers to deploy (in order - dependencies first if any)
WORKERS=(
  "packages/mekong-engine"
  "packages/zalo-parser"
)

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
    -v|--verbose)
      VERBOSE=true
      shift
      ;;
    -h|--help)
      cat <<EOF
Usage: $0 [OPTIONS]

Deploy Cloudflare Workers (mekong-engine, zalo-parser)

Options:
  --staging        Deploy to staging environment
  --dry-run        Preview without deploying
  -v, --verbose    Show detailed output
  -h, --help       Show this help message

Examples:
  $0                      # Deploy all workers to production
  $0 --staging           # Deploy all workers to staging
  $0 --dry-run           # Preview deployment

Environment variables:
  CF_API_TOKEN    Cloudflare API token (uses wrangler auth if not set)
  CF_ACCOUNT_ID   Cloudflare account ID (fallback from wrangler.toml)
EOF
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

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

# Check prerequisites
check_prerequisites() {
  section "Checking Prerequisites"

  if ! command -v wrangler &> /dev/null; then
    log_error "wrangler CLI not found. Install with: npm install -g wrangler"
    return 1
  fi

  wrangler --version >/dev/null 2>&1 || {
    log_error "wrangler not working properly"
    return 1
  }

  log_success "Prerequisites check passed"
  return 0
}

# Deploy a single worker
deploy_worker() {
  local worker_dir="$1"
  local worker_name="$(basename "$worker_dir")"

  section "Deploying ${worker_name}"

  if [[ ! -d "$worker_dir" ]]; then
    log_error "Worker directory not found: ${worker_dir}"
    return 1
  fi

  if [[ ! -f "${worker_dir}/package.json" ]]; then
    log_warn "No package.json in ${worker_dir}, skipping"
    return 0
  fi

  # Check if deploy script exists
  if ! jq -e '.scripts.deploy' "${worker_dir}/package.json" >/dev/null 2>&1; then
    log_warn "No deploy script in ${worker_dir}/package.json, skipping"
    return 0
  fi

  cd "$worker_dir"

  if [[ "${DRY_RUN}" == "true" ]]; then
    log_info "DRY RUN: Would run 'npm run deploy' in ${worker_dir}"
    if [[ "${ENVIRONMENT}" == "staging" ]]; then
      log_info "  with environment: staging"
    fi
    return 0
  fi

  # Build deploy command
  local deploy_cmd=("npm" "run" "deploy")
  if [[ "${ENVIRONMENT}" == "staging" ]]; then
    # Some workers may support --env staging via wrangler
    deploy_cmd+=("--" "--env" "staging") 2>/dev/null || true
  fi

  log_info "Running: ${deploy_cmd[*]}"
  if "${deploy_cmd[@]}"; then
    log_success "${worker_name} deployed successfully"
    return 0
  else
    log_error "${worker_name} deployment failed"
    return 1
  fi
}

# Main deployment logic
main() {
  section "Mekong Workers - Unified Deployment"
  log_info "Environment: ${ENVIRONMENT}"
  log_info "Workers to deploy: ${#WORKERS[@]}"
  log_info "Starting at: $(date '+%Y-%m-%d %H:%M:%S')"

  check_prerequisites || exit 1

  local failed_workers=()
  local deployed_workers=()

  # Deploy each worker sequentially (in case of dependencies)
  for worker in "${WORKERS[@]}"; do
    if deploy_worker "$worker"; then
      deployed_workers+=("$(basename "$worker")")
    else
      failed_workers+=("$(basename "$worker")")
    fi
  done

  # Summary
  section "Deployment Summary"
  echo "Environment: ${ENVIRONMENT}"
  echo ""
  echo "Deployed successfully: ${#deployed_workers[@]}"
  for w in "${deployed_workers[@]}"; do
    echo "  ✅ ${w}"
  done
  echo ""

  if [[ ${#failed_workers[@]} -gt 0 ]]; then
    echo "Failed: ${#failed_workers[@]}"
    for w in "${failed_workers[@]}"; do
      echo "  ❌ ${w}"
    done
    echo ""
    log_error "Some workers failed to deploy"
    log_info "Completed at: $(date '+%Y-%m-%d %H:%M:%S')"
    return 1
  else
    log_success "All workers deployed successfully!"
    log_info "Completed at: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    echo "Verification:"
    echo "  - Check worker logs: wrangler tail <worker-name>"
    echo "  - View in Cloudflare Dashboard: https://dash.cloudflare.com"
    if [[ "${ENVIRONMENT}" == "production" ]]; then
      echo "  - Production URLs:"
      echo "      mekong-engine: https://mekong-engine.workers.dev"
      echo "      zalo-parser:   https://zalo-parser.workers.dev"
    fi
    echo ""
    return 0
  fi
}

main
