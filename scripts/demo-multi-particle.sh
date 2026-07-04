#!/bin/bash
# Demo: Multi-Particle Economic Forest
#
# End-to-end walkthrough of the ZenOS multi-particle network:
# 1. Create two particles (alpha, beta)
# 2. Connect them in the behavior graph
# 3. Inspect network status
# 4. Run AI Cells (strategist, compliance, guardian)
# 5. Run cross-particle strategist with trust-network context
#
# Requires:
#   - Python 3.10+ with the mekong-cli package installed
#   - ZENOS.md and cells/strategist.yaml inside each particle
#   - $OPENROUTER_API_KEY or $ANTHROPIC_API_KEY (for LLM steps)
#
# Usage:
#   bash scripts/demo-multi-particle.sh
#   # Skip LLM-dependent cells (offline mode):
#   bash scripts/demo-multi-particle.sh --offline

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MEKONG_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON="${PYTHON:-python3}"

OFFLINE=false
if [[ "${1:-}" == "--offline" ]]; then
    OFFLINE=true
fi

# ---------------------------------------------------------------------------
# Colours / helpers
# ---------------------------------------------------------------------------
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

step()  { echo -e "\n${CYAN}==>${NC} ${BOLD}$1${NC}"; }
ok()    { echo -e "  ${GREEN}[OK]${NC} $1"; }
warn()  { echo -e "  ${YELLOW}[WARN]${NC} $1"; }
info()  { echo -e "  ${BOLD}   $1${NC}"; }
fail()  { echo -e "  ${RED}[FAIL]${NC} $1"; exit 1; }

# ---------------------------------------------------------------------------
# Setup: temporary particle directories
# ---------------------------------------------------------------------------
WORKDIR=$(mktemp -d)
trap 'rm -rf "$WORKDIR"' EXIT

step "Creating particle directories"

ALPHA_DIR="$WORKDIR/alpha"
BETA_DIR="$WORKDIR/beta"

mkdir -p "$ALPHA_DIR/cells" "$BETA_DIR/cells"

# --- alpha ZENOS.md ---
cat > "$ALPHA_DIR/ZENOS.md" << 'EOFA'
# ZENOS.md — Alpha Particle

## Article 1: Mission Integrity

The particle exists to generate AI video content for Southeast Asian markets.
All operations shall serve this mission.

## Article 2: Governance

Decisions are made by consensus among constituent cells. Each cell has one vote.

## Article 3: AI Cell Boundaries

Cells operate within defined privilege limits. No cell may escalate its own
privileges without constitutional review.

## Article 4: Economics

Value is distributed proportionally to contribution. Transparency is required.

## Article 5: Right to Exit

Any participant may exit at any time. No exit penalty shall be imposed.

## Article 6: Behavioral Integrity

The particle shall resist anti-concentration patterns. No single actor may
consolidate decision-making authority.

## Article 7: Evolution

This constitution may be amended by super-majority consensus.

## Article 8: Anti-Capture

The particle shall resist capture by any single agent or faction.
EOFA

# --- beta ZENOS.md ---
cat > "$BETA_DIR/ZENOS.md" << 'EOFB'
# ZENOS.md — Beta Particle

## Article 1: Mission Integrity

The particle exists to generate AI audio content for Southeast Asian markets.

## Article 2: Governance

Decisions are made by consensus among constituent cells.

## Article 3: AI Cell Boundaries

Cells operate within defined privilege limits. No cell may act without approval
for high-impact decisions.

## Article 4: Economics

Value is distributed proportionally to contribution. Transparency is required.

## Article 5: Right to Exit

Any participant may exit at any time, taking their data. No exit penalty.

## Article 6: Behavioral Integrity

The particle shall resist anti-concentration patterns. Checks and balances
shall be maintained.

## Article 7: Evolution

This constitution may be amended by super-majority consensus.

## Article 8: Anti-Capture

The particle shall resist capture by any single agent or faction.
EOFB

ok "Particle directories created at $WORKDIR/alpha and $WORKDIR/beta"

# --- strategist cell configs ---
for dir in "$ALPHA_DIR" "$BETA_DIR"; do
    cat > "$dir/cells/strategist.yaml" << 'EOFCFG'
role: strategist
model: anthropic/claude-sonnet-4
capabilities:
  - analysis
  - recommendation
privileges:
  max_budget: 100.0
  requires_approval: false
boundaries:
  read:
    - particle/*
  write:
    - particle/reports/*
EOFCFG
done
ok "Strategist cell configs created"

# --- compliance cell config ---
for dir in "$ALPHA_DIR" "$BETA_DIR"; do
    cat > "$dir/cells/compliance.yaml" << 'EOFCFG'
role: compliance
model: anthropic/claude-haiku-4-5
capabilities:
  - constitutional_review
  - violation_detection
privileges:
  max_budget: 50.0
  requires_approval: false
boundaries:
  read:
    - particle/*
  write: []
EOFCFG
done
ok "Compliance cell configs created"

# --- guardian cell config ---
for dir in "$ALPHA_DIR" "$BETA_DIR"; do
    cat > "$dir/cells/guardian.yaml" << 'EOFCFG'
role: guardian
model: anthropic/claude-haiku-4-5
capabilities:
  - health_monitoring
  - anomaly_detection
privileges:
  max_budget: 30.0
  requires_approval: false
boundaries:
  read:
    - particle/*
  write: []
EOFCFG
done
ok "Guardian cell configs created"

# ---------------------------------------------------------------------------
# Helper Python script
# ---------------------------------------------------------------------------
step "Connecting particles in behavior graph"

PYCODE=$(cat << 'PYEOF'
import json, os, sys
from pathlib import Path

workdir = sys.argv[1]
db_path = os.path.join(workdir, "graph.db")

alpha = os.path.join(workdir, "alpha")
beta  = os.path.join(workdir, "beta")

sys.path.insert(0, r"/Users/macbook/mekong-cli")
os.chdir(workdir)

# 2. Connect particles
from src.mekong.graph.network import connect_particles, particle_network_status, cross_particle_strategist

result = connect_particles(alpha, beta, db_path=db_path)
print(json.dumps(result, indent=2))
PYEOF
)

if ! CONNECT_OUTPUT=$("$PYTHON" -c "$PYCODE" "$WORKDIR" 2>&1); then
    echo "$CONNECT_OUTPUT"
    fail "Failed to connect particles"
fi

# Extract JSON from last line of output
echo "$CONNECT_OUTPUT" | grep '^{' | head -1 | "$PYTHON" -c "import sys,json; d=json.load(sys.stdin); print(f'  Trust: alpha->beta = {d[\"trust\"][\"alpha_to_beta\"]}/100'); print(f'  Trust: beta->alpha = {d[\"trust\"][\"beta_to_alpha\"]}/100')" 2>/dev/null || echo "$CONNECT_OUTPUT" | tail -1
ok "Particles connected"

# ---------------------------------------------------------------------------
# Step 3: Check network status
# ---------------------------------------------------------------------------
step "Checking particle network status"

PYCODE=$(cat << 'PYEOF'
import json, os, sys
from pathlib import Path

workdir = sys.argv[1]
db_path = os.path.join(workdir, "graph.db")
alpha = os.path.join(workdir, "alpha")
beta  = os.path.join(workdir, "beta")

sys.path.insert(0, r"/Users/macbook/mekong-cli")
os.chdir(workdir)

from src.mekong.graph.network import particle_network_status

status_a = particle_network_status(alpha, db_path=db_path)
status_b = particle_network_status(beta, db_path=db_path)

print("=== Alpha Status ===")
print(json.dumps(status_a, indent=2))
print("\n=== Beta Status ===")
print(json.dumps(status_b, indent=2))
PYEOF
)

STATUS_OUTPUT=$("$PYTHON" -c "$PYCODE" "$WORKDIR" 2>&1)
echo "$STATUS_OUTPUT"

# Verify counterparties exist
if echo "$STATUS_OUTPUT" | grep -q "particle:beta\|beta_to_alpha\|alpha_to_beta"; then
    ok "Network status shows counterparties"
else
    warn "Counterparty info not visible in status output (expected if trust scores are neutral)"
fi

# ---------------------------------------------------------------------------
# Step 4: Run strategist + compliance on each particle
# ---------------------------------------------------------------------------
if [ "$OFFLINE" = true ]; then
    warn "Skipping AI Cell execution (--offline mode)"
else
    step "Running strategist cell on alpha"
    PYCODE=$(cat << 'PYEOF'
import json, os, sys
workdir = sys.argv[1]
db_path = os.path.join(workdir, "graph.db")
alpha = os.path.join(workdir, "alpha")

sys.path.insert(0, r"/Users/macbook/mekong-cli")
os.chdir(workdir)

from src.mekong.cells.config import load_cell_config
from src.mekong.cells.runner import run_strategist

config = load_cell_config(os.path.join(alpha, "cells", "strategist.yaml"))
result = run_strategist(config, alpha, "What market should we target?", db_path=db_path)
print(json.dumps({
    "recommendation": result.recommendation,
    "confidence": result.confidence,
    "rationale": result.rationale,
    "risk_factors": result.risk_factors,
    "estimated_impact": result.estimated_impact,
}, indent=2))
PYEOF
    )

    if STRAT_OUTPUT=$("$PYTHON" -c "$PYCODE" "$WORKDIR" 2>&1); then
        echo "$STRAT_OUTPUT"
        ok "Strategist cell ran on alpha"
    else
        warn "Strategist cell failed (API key may be missing):"
        echo "  $STRAT_OUTPUT" | head -3
    fi

    # --- Compliance check ---
    step "Running compliance cell on alpha"
    PYCODE=$(cat << 'PYEOF'
import json, os, sys
workdir = sys.argv[1]
db_path = os.path.join(workdir, "graph.db")
alpha = os.path.join(workdir, "alpha")
rec_path = os.path.join(workdir, "last_rec.json")

sys.path.insert(0, r"/Users/macbook/mekong-cli")
os.chdir(workdir)

from src.mekong.cells.config import load_cell_config
from src.mekong.cells.runner import run_compliance
from src.mekong.cells.types import CellRecommendation

config = load_cell_config(os.path.join(alpha, "cells", "compliance.yaml"))
# Use a reasonable recommendation for compliance check
rec = CellRecommendation(
    recommendation="Expand into the Vietnamese market with localized AI video content",
    confidence=0.85,
    rationale="Strong market demand and cultural alignment",
    risk_factors=["Competition", "Regulatory compliance"],
    estimated_impact="high",
)
result = run_compliance(config, alpha, rec, db_path=db_path)
print(json.dumps({
    "verdict": result.verdict,
    "checked_articles": result.checked_articles,
    "violations": result.violations,
    "warnings": result.warnings,
}, indent=2))
PYEOF
    )

    if COMP_OUTPUT=$("$PYTHON" -c "$PYCODE" "$WORKDIR" 2>&1); then
        echo "$COMP_OUTPUT"
        ok "Compliance cell ran on alpha"
    else
        warn "Compliance cell failed (API key may be missing):"
        echo "  $COMP_OUTPUT" | head -3
    fi

    # ---------------------------------------------------------------------------
    # Step 5: Cross-particle strategist
    # ---------------------------------------------------------------------------
    step "Running cross-particle strategist (alpha consults beta)"
    PYCODE=$(cat << 'PYEOF'
import json, os, sys
workdir = sys.argv[1]
db_path = os.path.join(workdir, "graph.db")
alpha = os.path.join(workdir, "alpha")

sys.path.insert(0, r"/Users/macbook/mekong-cli")
os.chdir(workdir)

from src.mekong.graph.network import cross_particle_strategist

result = cross_particle_strategist(
    particle_id=alpha,
    question="Should we partner with beta?",
    network_size=5,
    db_path=db_path,
)
print(json.dumps(result, indent=2))
PYEOF
    )

    if CROSS_OUTPUT=$("$PYTHON" -c "$PYCODE" "$WORKDIR" 2>&1); then
        echo "$CROSS_OUTPUT"
        ok "Cross-particle strategist completed"
    else
        warn "Cross-particle strategist failed (API key may be missing):"
        echo "  $CROSS_OUTPUT" | head -3
    fi
fi  # end OFFLINE check

# ---------------------------------------------------------------------------
# Step 6: Guardian review
# ---------------------------------------------------------------------------
step "Running guardian health review"

PYCODE=$(cat << 'PYEOF'
import json, os, sys
workdir = sys.argv[1]
db_path = os.path.join(workdir, "graph.db")

sys.path.insert(0, r"/Users/macbook/mekong-cli")
os.chdir(workdir)

from src.mekong.cells.guardian import run_guardian_review

report_a = run_guardian_review("particle:alpha", graph_db=db_path)
report_b = run_guardian_review("particle:beta", graph_db=db_path)

print("=== Alpha Guardian Report ===")
print(json.dumps({
    "status": report_a.status,
    "total_behaviors": report_a.total_behaviors,
    "violations": report_a.violations,
    "collusion_flags": report_a.collusion_flags,
    "trust_trend": report_a.trust_trend,
    "alerts": [{"severity": a.severity, "source": a.source, "message": a.message} for a in report_a.alerts],
}, indent=2))

print("\n=== Beta Guardian Report ===")
print(json.dumps({
    "status": report_b.status,
    "total_behaviors": report_b.total_behaviors,
    "violations": report_b.violations,
    "collusion_flags": report_b.collusion_flags,
    "trust_trend": report_b.trust_trend,
    "alerts": [{"severity": a.severity, "source": a.source, "message": a.message} for a in report_b.alerts],
}, indent=2))
PYEOF
)

GUARDIAN_OUTPUT=$("$PYTHON" -c "$PYCODE" "$WORKDIR" 2>&1)
echo "$GUARDIAN_OUTPUT"
ok "Guardian review complete"

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  Multi-Particle Demo Complete${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
info "Network DB: $WORKDIR/graph.db"
info "Particle alpha: $ALPHA_DIR"
info "Particle beta:  $BETA_DIR"
if [ "$OFFLINE" = true ]; then
    info "Mode: OFFLINE (LLM cells skipped)"
else
    info "Mode: ONLINE (all cells executed)"
fi
echo ""
echo -e "Run ${CYAN}sqlite3 $WORKDIR/graph.db \"SELECT * FROM trust_scores;\"${NC}"
echo -e "    to inspect the trust scores."
echo ""
