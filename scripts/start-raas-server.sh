#!/bin/bash
set -euo pipefail
echo "═══ Mekong RaaS Server — :${RAAS_PORT:-9090} ═══"
npx tsx packages/openclaw-engine/src/raas/raas-server.ts
