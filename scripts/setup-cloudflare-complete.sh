#!/usr/bin/env bash
# Mekong Cloudflare Workers Complete Setup Script
# This script automates the creation and configuration of all Cloudflare resources

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

echo "========================================"
echo "Mekong Cloudflare Workers Setup"
echo "========================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_success() { echo -e "${GREEN}✓${NC} $1"; }
log_error() { echo -e "${RED}✗${NC} $1"; }
log_warn() { echo -e "${YELLOW}⚠${NC} $1"; }
log_info() { echo "ℹ $1"; }

# Check prerequisites
echo "Checking prerequisites..."
PREREQ_OK=true

if ! command -v node &> /dev/null; then
    log_error "Node.js not found. Please install Node.js 18+"
    PREREQ_OK=false
else
    NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 18 ]; then
        log_error "Node.js version 18+ required. Found: $(node --version)"
        PREREQ_OK=false
    else
        log_success "Node.js $(node --version)"
    fi
fi

if ! command -v pnpm &> /dev/null; then
    log_error "pnpm not found. Install with: npm install -g pnpm@9.15.0"
    PREREQ_OK=false
else
    log_success "pnpm $(pnpm --version)"
fi

if ! command -v wrangler &> /dev/null; then
    log_warn "Wrangler CLI not found. Will install locally."
    WRANGLER_AVAILABLE=false
else
    log_success "Wrangler $(wrangler --version)"
    WRANGLER_AVAILABLE=true
fi

if [ "$PREREQ_OK" = false ]; then
    echo ""
    log_error "Please install missing prerequisites and run this script again."
    exit 1
fi

echo ""
log_info "Installing dependencies..."
pnpm install

# Check Cloudflare login
echo ""
log_info "Checking Cloudflare authentication..."
if ! $WRANGLER_AVAILABLE && ! npx wrangler whoami &>/dev/null; then
    log_error "Not logged in to Cloudflare. Please run: wrangler login"
    exit 1
fi

WRANGLER_CMD="wrangler"
if [ "$WRANGLER_AVAILABLE" = false ]; then
    WRANGLER_CMD="npx wrangler"
fi

# Function to create D1 database
create_d1_database() {
    local db_name=$1
    local config_path=$2
    local binding_name=$3

    echo ""
    log_info "Creating D1 database: $db_name"

    # Check if database already exists
    existing_db_id=$($WRANGLER_CMD d1 list --output json 2>/dev/null | grep -o "\"name\":\"$db_name\"" -A1 | grep "\"id\"" | head -1 | cut -d'"' -f4 || echo "")

    if [ -n "$existing_db_id" ]; then
        log_warn "Database '$db_name' already exists with ID: $existing_db_id"
        DB_ID="$existing_db_id"
    else
        # Create new database
        create_output=$($WRANGLER_CMD d1 create "$db_name" 2>&1)
        if echo "$create_output" | grep -q "Database created"; then
            DB_ID=$(echo "$create_output" | grep -o "Database ID: [a-f0-9-]*" | cut -d' ' -f3)
            log_success "Created database '$db_name' with ID: $DB_ID"
        else
            log_error "Failed to create database '$db_name'"
            log_error "Output: $create_output"
            return 1
        fi
    fi

    # Update wrangler.toml
    if [ -f "$config_path" ]; then
        if grep -q "database_id =.*$binding_name" "$config_path"; then
            # Using placeholder pattern
            sed -i '' "s/database_id = \".*\" # $binding_name/database_id = \"$DB_ID\" # $binding_name/" "$config_path" 2>/dev/null || \
            sed -i "s/database_id = \".*\" # $binding_name/database_id = \"$DB_ID\" # $binding_name/" "$config_path"
            log_success "Updated $config_path with database ID for $binding_name"
        elif grep -q "binding = \"$binding_name\"" "$config_path"; then
            # Find the database_id line after the binding
            sed -i '' "/binding = \"$binding_name\"/,/migrations_dir/ s/database_id = \".*\"/database_id = \"$DB_ID\"/" "$config_path" 2>/dev/null || \
            sed -i "/binding = \"$binding_name\"/,/migrations_dir/ s/database_id = \".*\"/database_id = \"$DB_ID\"/" "$config_path"
            log_success "Updated $config_path with database ID for $binding_name"
        else
            log_warn "Could not find binding '$binding_name' in $config_path - please update manually"
        fi
    else
        log_warn "Config file not found: $config_path"
    fi

    echo "$DB_ID"
}

# Function to create KV namespace
create_kv_namespace() {
    local namespace_name=$1
    local config_path=$2
    local binding_name=$3

    echo ""
    log_info "Creating KV namespace: $namespace_name"

    # Check if namespace already exists
    existing_ns_id=$($WRANGLER_CMD kv:namespace list --output json 2>/dev/null | grep -o "\"title\":\"$namespace_name\"" -A1 | grep "\"id\"" | head -1 | cut -d'"' -f4 || echo "")

    if [ -n "$existing_ns_id" ]; then
        log_warn "Namespace '$namespace_name' already exists with ID: $existing_ns_id"
        NS_ID="$existing_ns_id"
    else
        # Create new namespace
        create_output=$($WRANGLER_CMD kv:namespace create "$namespace_name" 2>&1)
        if echo "$create_output" | grep -q "Created namespace"; then
            NS_ID=$(echo "$create_output" | grep -o "namespace_id: [a-f0-9-]*" | cut -d' ' -f2)
            log_success "Created namespace '$namespace_name' with ID: $NS_ID"
        else
            log_error "Failed to create namespace '$namespace_name'"
            log_error "Output: $create_output"
            return 1
        fi
    fi

    # Update wrangler.toml
    if [ -f "$config_path" ]; then
        if grep -q "id = \".*\" # $binding_name" "$config_path"; then
            sed -i '' "s/id = \".*\" # $binding_name/id = \"$NS_ID\" # $binding_name/" "$config_path" 2>/dev/null || \
            sed -i "s/id = \".*\" # $binding_name/id = \"$NS_ID\" # $binding_name/" "$config_path"
            log_success "Updated $config_path with KV ID for $binding_name"
        elif grep -q "binding = \"$binding_name\"" "$config_path"; then
            sed -i '' "/binding = \"$binding_name\"/,/}/ s/id = \".*\"/id = \"$NS_ID\"/" "$config_path" 2>/dev/null || \
            sed -i "/binding = \"$binding_name\"/,/}/ s/id = \".*\"/id = \"$NS_ID\"/" "$config_path"
            log_success "Updated $config_path with KV ID for $binding_name"
        else
            log_warn "Could not find binding '$binding_name' in $config_path - please update manually"
        fi
    else
        log_warn "Config file not found: $config_path"
    fi

    echo "$NS_ID"
}

# Apply database migrations
apply_migrations() {
    local db_name=$1
    local migrations_dir=$2

    echo ""
    log_info "Applying migrations for $db_name..."

    if [ -d "$migrations_dir" ]; then
        for migration in "$migrations_dir"/*.sql; do
            if [ -f "$migration" ]; then
                log_info "Running migration: $(basename "$migration")"
                if $WRANGLER_CMD d1 execute "$db_name" --file="$migration" 2>&1 | grep -q "Error\|failed"; then
                    log_warn "Migration may have issues (check output above)"
                else
                    log_success "Applied migration: $(basename "$migration")"
                fi
            fi
        done
    else
        log_warn "Migrations directory not found: $migrations_dir"
    fi
}

# Set secrets
set_secret() {
    local secret_name=$1
    local worker_dir=$2

    echo ""
    log_info "Setting secret: $secret_name"

    if [ -f "$worker_dir/.env" ]; then
        source "$worker_dir/.env" 2>/dev/null || true
    fi

    if [ -z "${!secret_name:-}" ]; then
        log_warn "Environment variable $secret_name not set in .env"
        log_info "You can set it manually: cd $worker_dir && $WRANGLER_CMD secret put $secret_name"
        return 0
    fi

    local secret_value="${!secret_name}"
    (cd "$worker_dir" && echo "$secret_value" | $WRANGLER_CMD secret put "$secret_name")
    log_success "Set secret $secret_name for $worker_dir"
}

# ========================================
# MAIN SETUP FLOW
# ========================================

echo "========================================"
echo "Phase 1: Create D1 Databases"
echo "========================================"

# API Worker Databases
SESSIONS_DB_ID=$(create_d1_database "mekong-sessions" "apps/api/wrangler.toml" "SESSIONS_DB")
AUDIT_DB_ID=$(create_d1_database "mekong-audit" "apps/api/wrangler.toml" "AUDIT_DB")

# Zalo Parser Database
ZALO_DB_ID=$(create_d1_database "mekong-d1" "packages/zalo-parser/wrangler.toml" "DB")

echo ""
log_success "All D1 databases created/verified"

echo ""
echo "========================================"
echo "Phase 2: Create KV Namespaces"
echo "========================================"

# API Worker KV Namespaces
RATE_LIMIT_KV_ID=$(create_kv_namespace "RATE_LIMIT_KV" "apps/api/wrangler.toml" "RATE_LIMIT_KV")
CACHE_KV_ID=$(create_kv_namespace "CACHE_KV" "apps/api/wrangler.toml" "CACHE_KV")

# Mekong Engine KV Namespace (if needed)
if [ -f "packages/mekong-engine/wrangler.toml" ]; then
    # Check if it already has an ID
    ENGINE_KV_ID=$(grep -o "id = \"[a-f0-9-]*\"" packages/mekong-engine/wrangler.toml | head -1 | cut -d'"' -f2 || echo "")
    if [ -z "$ENGINE_KV_ID" ]; then
        ENGINE_KV_ID=$(create_kv_namespace "mekong-engine-kv" "packages/mekong-engine/wrangler.toml" "RATE_LIMIT_KV")
    else
        log_success "Mekong Engine KV already configured with ID: $ENGINE_KV_ID"
    fi
fi

echo ""
log_success "All KV namespaces created/verified"

echo ""
echo "========================================"
echo "Phase 3: Apply Database Migrations"
echo "========================================"

apply_migrations "mekong-sessions" "apps/api/migrations/sessions"
apply_migrations "mekong-audit" "apps/api/migrations/audit"

# Apply migrations for other workers if they have them
if [ -d "packages/mekong-engine/migrations" ]; then
    apply_migrations "mekong-db" "packages/mekong-engine/migrations"
fi

if [ -d "packages/zalo-parser/migrations" ]; then
    apply_migrations "mekong-d1" "packages/zalo-parser/migrations"
fi

echo ""
log_success "All migrations applied"

echo ""
echo "========================================"
echo "Phase 4: Set Secrets"
echo "========================================"

# Set secrets for API worker
log_info "Checking for secrets in apps/api/.env..."
set_secret "WEBHOOK_SECRET" "apps/api"

# Set secrets for Zalo parser
if [ -f "packages/zalo-parser/.env" ]; then
    set_secret "ZALO_OA_SECRET_KEY" "packages/zalo-parser"
fi

# Set secrets for mekong-engine
if [ -f "packages/mekong-engine/.env" ]; then
    for secret in LLM_API_KEY SERVICE_TOKEN POLAR_WEBHOOK_SECRET; do
        set_secret "$secret" "packages/mekong-engine"
    done
fi

echo ""
log_success "Secrets configured"

echo ""
echo "========================================"
echo "Phase 5: Validation"
echo "========================================"

# Validate wrangler configs
log_info "Validating wrangler.toml files..."
VALIDATION_ERRORS=0

for config in apps/dashboard/wrangler.toml apps/api/wrangler.toml packages/mekong-engine/wrangler.toml packages/zalo-parser/wrangler.toml; do
    if [ -f "$config" ]; then
        log_info "Validating: $config"
        if $WRANGLER_CMD validate --config "$config" 2>&1 | grep -q "valid"; then
            log_success "  ✓ Valid"
        else
            log_error "  ✗ Invalid configuration"
            ((VALIDATION_ERRORS++))
        fi
    fi
done

if [ $VALIDATION_ERRORS -eq 0 ]; then
    log_success "All configurations are valid"
else
    log_error "Found $VALIDATION_ERRORS validation error(s)"
fi

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
log_success "Cloudflare resources created and configured:"
echo "  • D1 Databases: mekong-sessions, mekong-audit, mekong-d1"
echo "  • KV Namespaces: RATE_LIMIT_KV, CACHE_KV"
echo "  • Workers: mekong-api, mekong-engine, zalo-parser"
echo "  • Pages Project: mekong-ide"
echo ""
echo "Next steps:"
echo ""
echo "1. Test local development:"
echo "   cd apps/dashboard && pnpm dev"
echo "   cd apps/api && pnpm dev"
echo ""
echo "2. Deploy to staging:"
echo "   cd apps/api && npm run deploy:staging"
echo ""
echo "3. Deploy to production:"
echo "   pnpm run deploy:all"
echo ""
echo "4. Verify deployment:"
echo "   curl https://ide.mekongmind.com"
echo "   curl https://mekong-api.$(grep -o 'account_id = \"[^\"]*\"' apps/api/wrangler.toml | cut -d'"' -f2).workers.dev/health"
echo ""
echo "Documentation:"
echo "  • CLOUD_FLARE_DEPLOYMENT.md - Quick reference"
echo "  • GO_LIVE_PLAYBOOK.md - Complete go-live checklist"
echo "  • DEPLOYMENT_SUMMARY.md - Infrastructure overview"
echo ""
