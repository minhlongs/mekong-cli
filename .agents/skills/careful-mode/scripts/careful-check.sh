#!/bin/bash
# Careful mode — block destructive commands
# Used as PreToolUse hook for Bash tool
# Exit 0 = allow, Exit 2 = block with message

# Read the command from stdin (Claude Code hook protocol)
CMD=$(cat)

# Destructive patterns to block
BLOCKED_PATTERNS=(
    "rm -rf"
    "rm -r /"
    "DROP TABLE"
    "DROP DATABASE"
    "TRUNCATE"
    "git push --force"
    "git push -f "
    "docker rm"
    "docker rmi"
    "docker system prune"
    "kubectl delete"
    "CASHCLAW_MODE=LIVE"
    "wrangler delete"
    "wrangler d1 delete"
)

for pattern in "${BLOCKED_PATTERNS[@]}"; do
    if echo "$CMD" | grep -qi "$pattern"; then
        echo "[CAREFUL] BLOCKED: Command matches destructive pattern '$pattern'" >&2
        echo "[CAREFUL] Disable careful mode with /careful-off to proceed" >&2
        exit 2
    fi
done

# Allow /tmp operations even with rm -r
if echo "$CMD" | grep -q "rm.*\/tmp"; then
    exit 0
fi

exit 0
