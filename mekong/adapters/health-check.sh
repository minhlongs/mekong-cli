#!/usr/bin/env bash
# ==============================================================================
# health-check.sh — sovereign AI OS health monitor
# Checks: Ollama, model availability, disk space, memory pressure, thermal
# Outputs: JSON with pass/fail/warn per check
# Logs: ~/.system/logs/health-check.log
# Exit: 0=all pass, 1=any fail, 2=any warn
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${HOME}/.system/logs"
LOG_FILE="${LOG_DIR}/health-check.log"
TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
mkdir -p "${LOG_DIR}"

RESULTS_FILE="$(mktemp)"
echo '[]' > "${RESULTS_FILE}"

PASS=0
FAIL=0
WARN=0

add_result() {
    local check="$1"
    local status="$2"
    local message="$3"
    python3 -c "
import json,sys
with open('${RESULTS_FILE}') as f:
    r = json.load(f)
r.append({'check': ${check}, 'status': ${status}, 'message': json.loads('''${message}'''), 'timestamp': '${TIMESTAMP}'})
with open('${RESULTS_FILE}','w') as f:
    json.dump(r, f)
"
    case "${status}" in
        pass) ((PASS++)) ;;
        fail) ((FAIL++)) ;;
        warn) ((WARN++)) ;;
    esac
}

jesc() {
    python3 -c "import json,sys; print(json.dumps(sys.argv[1]))" "$1"
}

add_r() {
    local check="$1" status="$2" msg="$3"
    add_result "$(jesc "${check}")" "$(jesc "${status}")" "$(jesc "${msg}")"
}

# --- Check 1: Ollama API ---
check_ollama() {
    local resp
    if resp=$(curl -s --max-time 5 http://localhost:11434/api/tags 2>&1); then
        if echo "${resp}" | python3 -c "import json,sys; json.load(sys.stdin); print('ok')" 2>/dev/null | grep -q ok; then
            add_r "ollama_api" "pass" "Ollama API responding with valid JSON"
        else
            add_r "ollama_api" "fail" "Ollama API response is not valid JSON"
        fi
    else
        add_r "ollama_api" "fail" "Ollama API unreachable: ${resp}"
    fi
}

# --- Check 2: Model availability ---
check_models() {
    local models
    if models=$(ollama list 2>&1); then
        if echo "${models}" | grep -q "qwen3.6\|qwen3:6b\|qwen"; then
            add_r "model_qwen3.6" "pass" "Required model qwen3.6 available"
        else
            add_r "model_qwen3.6" "warn" "Model qwen3.6 not found in ollama list"
        fi
    else
        add_r "model_qwen3.6" "fail" "Cannot list ollama models: ${models}"
    fi
}

# --- Check 3: Disk space ---
check_disk() {
    local free_kb free_gb
    free_kb=$(df -k / | tail -1 | awk '{print $4}')
    free_gb=$((free_kb / 1024 / 1024))
    if [ "${free_gb}" -lt 10 ]; then
        add_r "disk_space" "fail" "Low disk space: ${free_gb}GB free (threshold: 10GB)"
    elif [ "${free_gb}" -lt 20 ]; then
        add_r "disk_space" "warn" "Disk space warning: ${free_gb}GB free (threshold: 10GB)"
    else
        add_r "disk_space" "pass" "Disk space OK: ${free_gb}GB free"
    fi
}

# --- Check 4: Memory pressure ---
check_memory() {
    local pressure
    if pressure=$(memory_pressure 2>&1); then
        local pct=$(echo "${pressure}" | grep -o '[0-9]\+\.[0-9]*%' | tr -d '%' | head -1)
        if echo "${pressure}" | grep -qi "critical"; then
            add_r "memory_pressure" "warn" "Memory pressure critical"
        elif [ -n "${pct}" ] && [ "${pct%.*}" -gt 80 ]; then
            add_r "memory_pressure" "warn" "Memory pressure high: ${pct}%"
        else
            add_r "memory_pressure" "pass" "Memory pressure normal${pct:+: ${pct}%}"
        fi
    else
        add_r "memory_pressure" "warn" "Cannot check memory pressure"
    fi
}

# --- Check 5: Thermal status ---
check_thermal() {
    local therm level cpu_speed throttled
    if therm=$(pmset -g therm 2>&1); then
        level=$(echo "${therm}" | grep -o 'CPU_Scheduler_Limit[[:space:]]*=[[:space:]]*[0-9]*' | grep -o '[0-9]*$' || echo "100")
        throttled=$((100 - level))
        if [ "${throttled}" -gt 80 ]; then
            add_r "thermal_status" "warn" "Thermal throttling critical: ${throttled}% (limit: >80%)"
        elif [ "${throttled}" -gt 50 ]; then
            add_r "thermal_status" "warn" "Thermal throttling elevated: ${throttled}%"
        else
            add_r "thermal_status" "pass" "Thermal status OK: throttled ${throttled}%"
        fi
    else
        add_r "thermal_status" "warn" "Cannot check thermal status"
    fi
}

# Run all checks
check_ollama
check_models
check_disk
check_memory
check_thermal

# Build final output
FINAL_JSON=$(python3 -c "
import json
with open('${RESULTS_FILE}') as f:
    checks = json.load(f)
output = {
    'timestamp': '${TIMESTAMP}',
    'summary': {'pass': ${PASS}, 'fail': ${FAIL}, 'warn': ${WARN}},
    'checks': checks
}
print(json.dumps(output, indent=2))
")

rm -f "${RESULTS_FILE}"

echo "${FINAL_JSON}" >> "${LOG_FILE}"
echo "${FINAL_JSON}"

if [ "${FAIL}" -gt 0 ]; then
    exit 1
elif [ "${WARN}" -gt 0 ]; then
    exit 2
else
    exit 0
fi
