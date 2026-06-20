#!/usr/bin/env sh
# ci/helpers/run-gate.sh — Shared gate runner
# Usage: run-gate.sh <gate-name> <command>
# Wraps command with timing, exit-code capture, and labeled output.
set -euo pipefail

GATE_NAME="${1:?Usage: run-gate.sh <gate-name> <command>}"
shift
CMD="$*"

echo "==> [GATE: ${GATE_NAME}] start"
START=$(date +%s)

eval "${CMD}"
EXIT=$?

END=$(date +%s)
ELAPSED=$((END - START))

if [ "${EXIT}" -eq 0 ]; then
  echo "==> [GATE: ${GATE_NAME}] PASSED in ${ELAPSED}s"
else
  echo "==> [GATE: ${GATE_NAME}] FAILED (exit ${EXIT}) in ${ELAPSED}s"
  exit "${EXIT}"
fi
