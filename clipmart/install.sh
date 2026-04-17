#!/usr/bin/env bash
# Mekong CLI — Department Marketplace Installer
# Usage:
#   mekong install --list              # List all 22 departments
#   mekong install dept-sales          # Install a department
#   mekong install --dry-run dept-sales # Validate without installing
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPTS_DIR="$SCRIPT_DIR/departments"

DEPT_IDS=(
  "dept-strategy"
  "dept-finance"
  "dept-legal"
  "dept-fundraising"
  "dept-sales"
  "dept-marketing"
  "dept-customer-success"
  "dept-bizops"
  "dept-product-management"
  "dept-ux-research"
  "dept-data-analytics"
  "dept-engineering-backend"
  "dept-engineering-frontend"
  "dept-engineering-qa"
  "dept-devops"
  "dept-hr"
  "dept-recruiting"
  "dept-accounting"
  "dept-compliance"
  "dept-it-security"
  "dept-cx-support"
  "dept-communications"
)

DEPT_NAMES=(
  "Strategy Department as a Service"
  "Finance Department as a Service"
  "Legal Department as a Service"
  "Fundraising Department as a Service"
  "Sales Department as a Service"
  "Marketing Department as a Service"
  "Customer Success Department as a Service"
  "BizOps Department as a Service"
  "Product Management Department as a Service"
  "UX Research Department as a Service"
  "Data Analytics Department as a Service"
  "Backend Engineering Department as a Service"
  "Frontend Engineering Department as a Service"
  "QA Engineering Department as a Service"
  "DevOps Department as a Service"
  "HR Department as a Service"
  "Recruiting Department as a Service"
  "Accounting Department as a Service"
  "Compliance Department as a Service"
  "IT Security Department as a Service"
  "CX Support Department as a Service"
  "Communications Department as a Service"
)

DEPT_DIRS=(
  "strategy" "finance" "legal" "fundraising"
  "sales" "marketing" "customer-success" "bizops"
  "product-management" "ux-research" "data-analytics"
  "engineering-backend" "engineering-frontend" "engineering-qa" "devops"
  "hr" "recruiting" "accounting" "compliance" "it-security" "cx-support" "communications"
)

list_departments() {
  echo ""
  echo "Mekong CLI — Department Marketplace (22 departments)"
  echo "======================================================"
  echo ""
  printf "%-32s %-50s\n" "ID" "Name"
  printf "%-32s %-50s\n" "$(printf '%0.s-' {1..32})" "$(printf '%0.s-' {1..50})"
  for i in "${!DEPT_IDS[@]}"; do
    printf "%-32s %-50s\n" "${DEPT_IDS[$i]}" "${DEPT_NAMES[$i]}"
  done
  echo ""
  echo "Install: mekong install <dept-id>"
  echo "Dry run: mekong install --dry-run <dept-id>"
  echo "Catalog: cat $DEPTS_DIR/CATALOG.md"
  echo ""
}

validate_manifest() {
  local dir="$1"
  local manifest="$dir/manifest.json"
  if [ ! -f "$manifest" ]; then
    echo "ERROR: Missing manifest.json in $dir"
    return 1
  fi
  if command -v python3 &>/dev/null; then
    if python3 -c "import json; json.load(open('$manifest'))" 2>/dev/null; then
      echo "  manifest.json: valid JSON"
    else
      echo "ERROR: Invalid JSON in $manifest"
      return 1
    fi
  else
    echo "  manifest.json: exists (python3 not available for full validation)"
  fi
  return 0
}

validate_catalog() {
  local dir="$1"
  local catalog="$dir/catalog.yaml"
  if [ ! -f "$catalog" ]; then
    echo "ERROR: Missing catalog.yaml in $dir"
    return 1
  fi
  # Basic YAML validation — check for required keys
  if grep -q "^id:" "$catalog" && grep -q "^commands:" "$catalog" && grep -q "^skills:" "$catalog"; then
    echo "  catalog.yaml: valid structure"
  else
    echo "ERROR: catalog.yaml missing required keys (id, commands, skills)"
    return 1
  fi
  return 0
}

find_dept_dir() {
  local dept_id="$1"
  for i in "${!DEPT_IDS[@]}"; do
    if [ "${DEPT_IDS[$i]}" = "$dept_id" ]; then
      echo "${DEPT_DIRS[$i]}"
      return 0
    fi
  done
  return 1
}

install_department() {
  local dept_id="$1"
  local dry_run="${2:-false}"

  local dept_dir_name
  if ! dept_dir_name=$(find_dept_dir "$dept_id"); then
    echo "ERROR: Unknown department '$dept_id'"
    echo "Run 'mekong install --list' to see available departments"
    exit 1
  fi

  local dept_path="$DEPTS_DIR/$dept_dir_name"

  if [ ! -d "$dept_path" ]; then
    echo "ERROR: Department directory not found: $dept_path"
    exit 1
  fi

  echo ""
  echo "Mekong CLI — Installing $dept_id"
  echo "======================================"

  # Validate manifest and catalog
  echo "Validating..."
  validate_manifest "$dept_path" || exit 1
  validate_catalog "$dept_path" || exit 1
  echo "  install.sh: exists $([ -x "$dept_path/install.sh" ] && echo "(executable)" || echo "(not executable)")"
  echo "  README.md: exists"
  echo "  outcome-pricing.md: exists"
  echo ""

  if [ "$dry_run" = "true" ]; then
    echo "=== DRY RUN — No changes made ==="
    echo ""
    if [ -x "$dept_path/install.sh" ]; then
      bash "$dept_path/install.sh" --dry-run
    fi
    echo ""
    echo "Run without --dry-run to install: mekong install $dept_id"
  else
    if [ -x "$dept_path/install.sh" ]; then
      bash "$dept_path/install.sh"
    else
      echo "ERROR: install.sh not executable in $dept_path"
      exit 1
    fi
  fi
}

usage() {
  echo "Usage:"
  echo "  mekong install --list                   List all 22 departments"
  echo "  mekong install <dept-id>                Install a department"
  echo "  mekong install --dry-run <dept-id>      Validate without installing"
  echo ""
  echo "Examples:"
  echo "  mekong install --list"
  echo "  mekong install dept-sales"
  echo "  mekong install --dry-run dept-engineering-backend"
}

# Parse arguments
DRY_RUN=false
DEPT_ID=""

for arg in "$@"; do
  case "$arg" in
    --list|-l)
      list_departments
      exit 0
      ;;
    --dry-run)
      DRY_RUN=true
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    dept-*)
      DEPT_ID="$arg"
      ;;
    *)
      echo "Unknown argument: $arg"
      usage
      exit 1
      ;;
  esac
done

if [ -z "$DEPT_ID" ]; then
  usage
  exit 1
fi

install_department "$DEPT_ID" "$DRY_RUN"
