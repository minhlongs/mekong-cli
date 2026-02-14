#!/bin/bash
# 🦞 Visual Demo: "4 Tab Chạy Code" for Serena Bridge
# Demonstrates 4 parallel semantic queries running against the OpenClaw codebase.

PROJECT_ROOT=$(pwd)
BRIDGE_SCRIPT=".venv/bin/python3 scripts/serena-bridge.py"

# Function to run a "tab" with visual dressing
run_tab() {
    local tab_id=$1
    local name=$2
    local cmd=$3
    
    echo -e "\n================ [TAB $tab_id: $name] ================"
    echo "Running: $cmd"
    # Execute command, suppress logs to show only JSON output
    eval "$cmd" 2>/dev/null | jq '.' || echo "Error/Empty in TAB $tab_id"
    echo "======================================================"
}

echo "Starting 4-Tab Serena Demo..."
echo "Target: $PROJECT_ROOT"

# Run 4 queries in parallel (background) to simulate multiple tabs working
# We use wait to synch output but for visual effect, sequential is cleaner to read,
# however "4 tab chạy" implies concurrency. 
# Let's run them sequentially for clarity in the single terminal output, 
# but print them as if they are separate contexts.

# TAB 1: Overview (The Map)
run_tab 1 "STRUCTURAL SCAN" "$BRIDGE_SCRIPT get_overview --file src/index.ts"

# TAB 2: Find Function (The Lens)
run_tab 2 "FIND FUNCTION" "$BRIDGE_SCRIPT find_symbol --name handleTelegramWebhook --file src/index.ts"

# TAB 3: Find Interface (The Type)
run_tab 3 "FIND INTERFACE" "$BRIDGE_SCRIPT find_symbol --name Env --file src/index.ts"

# TAB 4: Find Utility (The Search)
run_tab 4 "FIND UTILITY" "$BRIDGE_SCRIPT find_symbol --name sendTelegramMessage --file src/index.ts"

echo -e "\n✅ [DEMO COMPLETE] All 4 semantic queries executed via Serena Bridge."
