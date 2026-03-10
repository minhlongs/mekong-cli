#!/usr/bin/env bash
# Vibe Coding Factory — Role-Based Setup Script
# Usage: bash factory/bootstrap.sh [role]
# Roles: founder | dev | business | product | ops
# Default: dev

set -euo pipefail

ROLE="${1:-dev}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MEKONG_DIR="$HOME/.mekong"
LINEAGE_DIR="$MEKONG_DIR/lineage"
FACTORY_DIR="$REPO_ROOT/factory"

_log()  { echo "[factory] $*"; }
_ok()   { echo "[factory] OK: $*"; }
_warn() { echo "[factory] WARN: $*" >&2; }
_fail() { echo "[factory] ERROR: $*" >&2; exit 1; }

# ── Validate role ──────────────────────────────────────────────────────────────
VALID_ROLES=("founder" "dev" "business" "product" "ops")
VALID=false
for r in "${VALID_ROLES[@]}"; do
  [[ "$ROLE" == "$r" ]] && VALID=true && break
done
$VALID || _fail "Unknown role '$ROLE'. Valid: ${VALID_ROLES[*]}"

_log "Bootstrapping Vibe Coding Factory for role: $ROLE"

# ── Create ~/.mekong directories ───────────────────────────────────────────────
mkdir -p "$LINEAGE_DIR"
_ok "Created $LINEAGE_DIR"

# ── Validate layers.yaml exists ────────────────────────────────────────────────
[[ -f "$FACTORY_DIR/layers.yaml" ]] || _fail "layers.yaml not found at $FACTORY_DIR/layers.yaml"
_ok "layers.yaml found"

# ── Load profile for role ──────────────────────────────────────────────────────
PROFILE_MAP_dev="$FACTORY_DIR/profiles/dev.yaml"
PROFILE_MAP_founder="$FACTORY_DIR/profiles/founder.yaml"
PROFILE_MAP_business="$FACTORY_DIR/profiles/founder.yaml"  # fallback
PROFILE_MAP_product="$FACTORY_DIR/profiles/founder.yaml"   # fallback
PROFILE_MAP_ops="$FACTORY_DIR/profiles/dev.yaml"           # fallback

PROFILE_VAR="PROFILE_MAP_${ROLE}"
PROFILE_PATH="${!PROFILE_VAR}"

if [[ -f "$PROFILE_PATH" ]]; then
  _ok "Profile loaded: $PROFILE_PATH"
else
  _warn "No profile file found for role '$ROLE' (looked at $PROFILE_PATH)"
fi

# ── Check Python dependencies ──────────────────────────────────────────────────
PYTHON="${PYTHON:-python3}"
$PYTHON -c "import yaml" 2>/dev/null || _fail "pyyaml not installed. Run: pip install pyyaml"
_ok "pyyaml available"

# ── Compile-check all factory Python files ────────────────────────────────────
_log "Compile-checking factory Python modules..."
for pyfile in "$FACTORY_DIR"/*.py; do
  $PYTHON -m py_compile "$pyfile" && _ok "$(basename "$pyfile")" || _fail "Compile error: $pyfile"
done

# ── Print summary ──────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Vibe Coding Factory — Setup Complete"
echo "  Role     : $ROLE"
echo "  Lineage  : $LINEAGE_DIR"
echo "  Factory  : $FACTORY_DIR"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Next: mekong start"
echo ""
