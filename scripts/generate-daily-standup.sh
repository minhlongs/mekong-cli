#!/usr/bin/env bash
# generate-daily-standup.sh — Generate daily standup report from heartbeat logs
#
# Usage:
#   bash scripts/generate-daily-standup.sh              # Generate and print
#   bash scripts/generate-daily-standup.sh --save       # Save to .mekong/logs/
#
# Reads today's heartbeat log and produces a markdown standup report.
# Designed to run via cron at 09:00 UTC daily.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="${PROJECT_ROOT}/.mekong/logs"
TODAY=$(date +%Y%m%d)
LOG_FILE="${LOG_DIR}/heartbeat-${TODAY}.log"
REPORT_FILE="${LOG_DIR}/standup-${TODAY}.md"
KPI_FILE="${LOG_DIR}/kpi-snapshot.json"

mkdir -p "$LOG_DIR"

# Count loop executions from today's log
TOTAL_RUNS=0
FAILED_RUNS=0
LOOPS_OK=0

if [ -f "$LOG_FILE" ]; then
    TOTAL_RUNS=$(grep -c "Executing:" "$LOG_FILE" 2>/dev/null || echo 0)
    FAILED_RUNS=$(grep -c "❌\|FAIL\|timeout" "$LOG_FILE" 2>/dev/null || echo 0)
    LOOPS_OK=$((TOTAL_RUNS - FAILED_RUNS))
fi

# Check LLM health
NEMOTRON="DOWN"
DEEPSEEK="DOWN"
GATEWAY="DOWN"

curl -sf http://192.168.11.111:11436/v1/models >/dev/null 2>&1 && NEMOTRON="HEALTHY"
curl -sf http://192.168.11.111:11435/v1/models >/dev/null 2>&1 && DEEPSEEK="HEALTHY"
curl -sf https://api.agencyos.network/health >/dev/null 2>&1 && GATEWAY="HEALTHY"

# Calculate uptime
if [ "$TOTAL_RUNS" -gt 0 ]; then
    UPTIME_PCT=$(echo "scale=1; ($LOOPS_OK * 100) / $TOTAL_RUNS" | bc 2>/dev/null || echo "N/A")
else
    UPTIME_PCT="N/A"
fi

# Generate report
REPORT="# Daily Standup — $(date +%Y-%m-%d)

## System Health
- Nemotron (11436): **${NEMOTRON}**
- DeepSeek R1 (11435): **${DEEPSEEK}**
- RaaS Gateway: **${GATEWAY}**

## Loop Execution
- Total runs today: **${TOTAL_RUNS}**
- Successful: **${LOOPS_OK}**
- Failed: **${FAILED_RUNS}**
- Uptime: **${UPTIME_PCT}%**

## Generated
- Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)
- Log file: heartbeat-${TODAY}.log
"

# Write KPI snapshot for stats server
cat > "$KPI_FILE" << ENDJSON
{
  "date": "$(date +%Y-%m-%d)",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "system": {
    "nemotron": "${NEMOTRON}",
    "deepseek": "${DEEPSEEK}",
    "gateway": "${GATEWAY}"
  },
  "loops": {
    "total_runs": ${TOTAL_RUNS},
    "successful": ${LOOPS_OK},
    "failed": ${FAILED_RUNS},
    "uptime_pct": "${UPTIME_PCT}"
  }
}
ENDJSON

if [ "${1:-}" = "--save" ]; then
    echo "$REPORT" > "$REPORT_FILE"
    echo "Standup saved to: $REPORT_FILE"
    echo "KPI snapshot saved to: $KPI_FILE"
else
    echo "$REPORT"
fi
