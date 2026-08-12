#!/usr/bin/env bash
# Deploy Mekong IDE Dashboard to Cloudflare Pages.
#
# Prereqs:
#   - wrangler installed:    npm install -g wrangler
#   - logged in:              wrangler login
#   - Cloudflare project:     mekong-ide  (auto-created on first deploy)
#   - Custom domain in CF:    ide.mekongmind.com → Pages project mekong-ide
#
# Usage:
#   ./scripts/deploy-dashboard.sh                # deploy to production
#   ./scripts/deploy-dashboard.sh --preview      # deploy to preview branch
#   ./scripts/deploy-dashboard.sh --staging      # alias for --preview
#   ./scripts/deploy-dashboard.sh --dry-run      # preview without deploying
#   ./scripts/deploy-dashboard.sh --no-wait      # skip health check
#
# Environment variables:
#   CF_API_TOKEN    Cloudflare API token (optional, uses wrangler auth)
#   CF_ACCOUNT_ID   Cloudflare account ID (falls back to wrangler.toml)
#
# Exit codes:
#   0 - Success
#   1 - Error (prerequisites, build failure, deployment failure, health check fail)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DASHBOARD="${REPO_ROOT}/apps/dashboard"
PROJECT_NAME="mekong-ide"
BRANCH="production"
ENVIRONMENT="production"
DRY_RUN=false
WAIT_FOR_HEALTH=true
HEALTH_CHECK_TIMEOUT=30
VERBOSE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --preview|--staging)
      BRANCH="preview"
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
    -v|--verbose)
      VERBOSE=true
      shift
      ;;
    -h|--help)
      cat <<EOF
Usage: $0 [OPTIONS]

Deploy Mekong IDE Dashboard to Cloudflare Pages

Options:
  --preview, --staging   Deploy to preview/staging branch (default: production)
  --dry-run              Preview deployment without executing
  --no-wait              Don't wait for health check after deploy
  -v, --verbose          Show detailed output
  -h, --help             Show this help message

Examples:
  $0                           # Deploy to production
  $0 --preview                # Deploy to staging/preview
  $0 --dry-run                # See what would be deployed
  $0 --staging --no-wait      # Deploy to staging without health check

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

  # Check if we're in the dashboard directory
  if [[ ! -f "${DASHBOARD}/package.json" ]]; then
    log_error "package.json not found in ${DASHBOARD}"
    return 1
  fi

  # Check Node.js
  if ! command -v node &> /dev/null; then
    log_error "Node.js not found. Please install Node.js 18+"
    return 1
  fi

  local node_version
  node_version=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
  if [[ "$node_version" -lt 18 ]]; then
    log_error "Node.js version 18+ required. Found: $(node --version)"
    return 1
  fi
  log_info "Node.js $(node --version)"

  # Check npm/pnpm
  if command -v pnpm &> /dev/null; then
    log_info "pnpm $(pnpm --version)"
  elif command -v npm &> /dev/null; then
    log_info "npm $(npm --version)"
  else
    log_error "Neither pnpm nor npm found"
    return 1
  fi

  # Check if wrangler is available (for deployment)
  if ! command -v wrangler &> /dev/null; then
    log_warn "wrangler CLI not found (optional for local build, required for deploy)"
    log_info "Install with: npm install -g wrangler"
    log_info "Then login: wrangler login"
  else
    log_info "wrangler $(wrangler --version 2>&1 || echo 'unknown')"
  fi

  log_success "Prerequisites check passed"
  return 0
}

# Build the dashboard
build_dashboard() {
  section "Building Dashboard"

  cd "${DASHBOARD}"

  # Install dependencies if needed
  if [[ ! -d "node_modules" ]]; then
    log_info "Installing dependencies..."
    if command -v pnpm &> /dev/null; then
      pnpm install --no-frozen-lockfile
    else
      npm install --no-audit --no-fund
    fi
  fi

  # Run build
  log_info "Running build: npm run build"
  if [[ "${DRY_RUN}" == "true" ]]; then
    log_info "DRY RUN: Would execute: npm run build"
    return 0
  fi

  if ! npm run build; then
    log_error "Build failed"
    return 1
  fi

  # Verify build output exists
  if [[ ! -d ".next" ]]; then
    log_error "Build output directory .next not found"
    return 1
  fi

  if [[ ! -d ".next/static" ]]; then
    log_warn ".next/static directory not found - Pages deployment may fail"
    log_info "For Cloudflare Pages, ensure next.config.js outputs to .next/static"
  fi

  log_success "Build completed successfully"
  return 0
}

# Deploy to Cloudflare Pages
deploy_dashboard() {
  section "Deploying Dashboard"

  cd "${DASHBOARD}"

  if [[ "${DRY_RUN}" == "true" ]]; then
    log_info "DRY RUN: Would deploy to Cloudflare Pages"
    log_info "  Project: ${PROJECT_NAME}"
    log_info "  Branch:  ${BRANCH}"
    log_info "  Directory: .next/static"
    return 0
  fi

  # Determine deploy command
  if command -v wrangler &> /dev/null; then
    deploy_cmd="wrangler"
  else
    deploy_cmd="npx wrangler"
  fi

  log_info "Deploying with: ${deploy_cmd}"
  log_info "Project: ${PROJECT_NAME}"
  log_info "Branch:  ${BRANCH}"
  echo ""

  if ! ${deploy_cmd} pages deploy .next/static \
    --project-name "${PROJECT_NAME}" \
    --branch "${BRANCH}" \
    --commit-dirty=true; then
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

  # Determine URL based on environment
  local expected_url
  if [[ "${ENVIRONMENT}" == "production" ]]; then
    expected_url="https://ide.mekongmind.com"
  else
    expected_url="https://mekong-ide.pages.dev"
  fi

  log_info "Checking: ${expected_url}"
  echo ""

  # Wait for deployment to propagate
  local i
  for i in $(seq 1 ${HEALTH_CHECK_TIMEOUT}); do
    echo -n "  Attempt ${i}/${HEALTH_CHECK_TIMEOUT}... " >&2

    local http_code
    http_code=$(curl -s -o /dev/null -w "%{http_code}" "${expected_url}" \
      2>/dev/null || echo "000")

    if [[ "${http_code}" == "200" ]]; then
      echo "✅ Healthy!" >&2
      log_success "Dashboard is responding with HTTP 200"

      # Fetch and display basic info
      local content_length
      content_length=$(curl -sI "${expected_url}" | grep -i '^content-length:' | \
        awk '{print $2}' | tr -d '\r' || echo "unknown")
      echo ""
      log_info "Response OK - Content-Length: ${content_length} bytes"
      return 0
    elif [[ "${http_code}" == "000" ]]; then
      echo "⏳ Waiting..." >&2
    else
      echo "⚠️  HTTP ${http_code}" >&2
    fi

    sleep 1
  done

  log_error "Health check failed - dashboard not responding with 200 OK after ${HEALTH_CHECK_TIMEOUT}s"
  log_info "URL: ${expected_url}"
  log_info "Check Cloudflare Pages dashboard for deployment status"
  return 1
}

# Print deployment summary
print_summary() {
  section "Deployment Summary"

  echo "Environment:   ${ENVIRONMENT}"
  echo "Project:       ${PROJECT_NAME}"
  echo "Branch:        ${BRANCH}"
  echo "Directory:     ${DASHBOARD}"
  echo ""

  if [[ "${DRY_RUN}" == "true" ]]; then
    log_warn "This was a DRY RUN - no changes were made"
  else
    log_success "Dashboard deployment completed successfully!"
    echo ""
    echo "URLs:"
    if [[ "${ENVIRONMENT}" == "production" ]]; then
      echo "  Production:  https://ide.mekongmind.com"
    else
      echo "  Staging:     https://mekong-ide.pages.dev"
    fi
    echo ""
    echo "Next steps:"
    echo "  1. Verify dashboard loads correctly"
    echo "  2. Check Cloudflare Pages dashboard for build logs"
    echo "  3. If issues: review wrangler output above"
  fi
  echo ""
}

# Main execution
main() {
  local exit_code=0

  log_info "Mekong IDE Dashboard Deployment"
  log_info "==============================="
  log_info "Environment: ${ENVIRONMENT}"
  log_info "Starting at: $(date '+%Y-%m-%d %H:%M:%S')"

  if [[ "${DRY_RUN}" == "true" ]]; then
    log_warn "RUNNING IN DRY-RUN MODE"
  fi

  # Execute deployment steps
  check_prerequisites || exit_code=$?

  if [[ ${exit_code} -eq 0 ]]; then
    build_dashboard || exit_code=$?
  fi

  if [[ ${exit_code} -eq 0 ]]; then
    deploy_dashboard || exit_code=$?
  fi

  if [[ ${exit_code} -eq 0 ]]; then
    health_check || exit_code=$?
  fi

  print_summary

  exit ${exit_code}
}

main
