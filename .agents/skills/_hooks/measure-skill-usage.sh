#!/bin/bash
# Log skill usage for analysis
# Called via PreToolUse hook when any skill is invoked

SKILL_NAME="${1:-unknown}"
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
LOG_FILE="${CLAUDE_PLUGIN_DATA:-.claude/skills/_data}/skill-usage.jsonl"

mkdir -p "$(dirname "$LOG_FILE")"

echo "{\"skill\":\"$SKILL_NAME\",\"timestamp\":\"$TIMESTAMP\",\"session\":\"$CLAUDE_SESSION_ID\"}" >> "$LOG_FILE"
