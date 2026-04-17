#!/usr/bin/env bash
# deploy.sh — CF Pages deploy helper for Mekong-ecosystem domains
#
# SCOPE: Documents deploy commands per project. Does NOT auto-apply.
#        Run each section manually after building the project locally
#        or via GitHub Actions (preferred — auto-triggers on push to main).
#
# PLATFORM: Cloudflare Pages only (Vercel BANNED 2026-03-27)
# AUTH: Requires CF API token in environment (never hardcoded here)
#
# REQUIRED ENV VARS:
#   CLOUDFLARE_API_TOKEN   — scoped to Pages:Edit + Zone:Read (not Account Admin)
#   CLOUDFLARE_ACCOUNT_ID  — find in CF dashboard > right sidebar
#
# USAGE:
#   source this file, then call individual functions:
#     ./deploy.sh agencyos-site
#     ./deploy.sh cashclaw
#     ./deploy.sh all
#
# NOTE: For production, prefer git push → GitHub Actions → CF Pages auto-deploy.
#       Use this script only for manual emergency deploys or first-time setup.

set -euo pipefail

# ─── GUARD: validate env ────────────────────────────────────────────────────
check_env() {
  if [[ -z "${CLOUDFLARE_API_TOKEN:-}" ]]; then
    echo "ERROR: CLOUDFLARE_API_TOKEN not set"
    echo "  export CLOUDFLARE_API_TOKEN=<token-from-cf-dashboard>"
    exit 1
  fi
  if [[ -z "${CLOUDFLARE_ACCOUNT_ID:-}" ]]; then
    echo "ERROR: CLOUDFLARE_ACCOUNT_ID not set"
    echo "  export CLOUDFLARE_ACCOUNT_ID=<account-id-from-cf-dashboard>"
    exit 1
  fi
  command -v wrangler >/dev/null 2>&1 || {
    echo "ERROR: wrangler not found. Install: npm i -g wrangler"
    exit 1
  }
}

# ─── PROJECT DEFINITIONS ────────────────────────────────────────────────────
# Format: project_name|repo_dir|build_output_dir|custom_domain
PROJECTS=(
  "agencyos-site|packages/agencyos-site|dist|agencyos.network"
  "algo-trader|apps/cashclaw|dist|cashclaw.cc"
  "wellnexus|apps/wellnexus|dist|wellnexus.vn"
  "mekong-ide-landing|apps/mekong-ide-landing|dist|ide.mekongmind.com"
  "mekong-landing|packages/mekong-landing|dist|mekongmind.com"
)

# ─── DEPLOY FUNCTION ────────────────────────────────────────────────────────
deploy_project() {
  local project_name="$1"
  local repo_dir="$2"
  local build_output="$3"
  local custom_domain="$4"

  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  Deploying: $project_name → $custom_domain"
  echo "  Source:    $repo_dir/$build_output"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  if [[ ! -d "$repo_dir/$build_output" ]]; then
    echo "ERROR: Build output not found at $repo_dir/$build_output"
    echo "  Run build first: cd $repo_dir && npm run build"
    return 1
  fi

  wrangler pages deploy "$repo_dir/$build_output" \
    --project-name "$project_name" \
    --commit-dirty=true

  echo "OK: $project_name deployed"
  echo "    Preview: https://$project_name.pages.dev"
  echo "    Custom:  https://$custom_domain"
  echo ""
}

# ─── LIST EXISTING CF PAGES PROJECTS ────────────────────────────────────────
list_projects() {
  check_env
  echo "Listing CF Pages projects for account $CLOUDFLARE_ACCOUNT_ID..."
  wrangler pages project list
}

# ─── CREATE PROJECT (first-time setup) ─────────────────────────────────────
create_project() {
  local project_name="$1"
  check_env
  echo "Creating CF Pages project: $project_name"
  wrangler pages project create "$project_name" --production-branch main
  echo "OK: Project created. Add custom domain in CF Dashboard:"
  echo "  Pages > $project_name > Custom domains > Add custom domain"
}

# ─── MAIN DISPATCH ──────────────────────────────────────────────────────────
main() {
  local target="${1:-help}"

  case "$target" in
    agencyos-site)
      check_env
      deploy_project "agencyos-site" "packages/agencyos-site" "dist" "agencyos.network"
      ;;
    cashclaw)
      check_env
      deploy_project "algo-trader" "apps/cashclaw" "dist" "cashclaw.cc"
      ;;
    wellnexus)
      check_env
      deploy_project "wellnexus" "apps/wellnexus" "dist" "wellnexus.vn"
      ;;
    mekong-ide-landing)
      check_env
      deploy_project "mekong-ide-landing" "apps/mekong-ide-landing" "dist" "ide.mekongmind.com"
      ;;
    mekong-landing)
      check_env
      deploy_project "mekong-landing" "packages/mekong-landing" "dist" "mekongmind.com"
      ;;
    list)
      list_projects
      ;;
    create)
      local project_name="${2:-}"
      [[ -z "$project_name" ]] && { echo "Usage: $0 create <project-name>"; exit 1; }
      create_project "$project_name"
      ;;
    all)
      check_env
      echo "WARNING: Deploying ALL projects. Press Ctrl+C within 5s to abort."
      sleep 5
      for entry in "${PROJECTS[@]}"; do
        IFS='|' read -r name dir output domain <<< "$entry"
        deploy_project "$name" "$dir" "$output" "$domain"
      done
      echo "All projects deployed."
      ;;
    help|*)
      cat <<EOF
Usage: ./deploy.sh <target>

Targets:
  agencyos-site     Deploy agencyos.network (Astro monolith)
  cashclaw          Deploy cashclaw.cc (algo-trader CF project)
  wellnexus         Deploy wellnexus.vn
  mekong-ide-landing Deploy ide.mekongmind.com
  mekong-landing    Deploy mekongmind.com
  list              List all CF Pages projects
  create <name>     Create new CF Pages project (first-time setup)
  all               Deploy all projects (use with caution)

Required env vars:
  CLOUDFLARE_API_TOKEN    CF API token (Pages:Edit + Zone:Read scope)
  CLOUDFLARE_ACCOUNT_ID   CF account ID

Preferred deploy path: git push origin main → GitHub Actions → CF Pages auto-deploy
Manual deploy: only for emergency hotfixes or first-time project setup
EOF
      ;;
  esac
}

main "$@"
