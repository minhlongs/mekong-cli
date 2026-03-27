#!/bin/bash
set -e

CLAUDE_HOME="/home/claude"
SOURCE_DIR="/usr/local/share/mekong"
PUID="${PUID:-1000}"
PGID="${PGID:-1000}"

echo "[bootstrap] Mekong CLI first-boot initialization..."

mkdir -p "$CLAUDE_HOME/.claude"

# Copy Mekong settings.json (with PEV notification hooks)
cp "$SOURCE_DIR/settings.json" "$CLAUDE_HOME/.claude/settings.json"
echo "[bootstrap] Copied settings.json"

# Copy Mekong-specific CLAUDE.md memory
cp "$SOURCE_DIR/claude-memory.md" "$CLAUDE_HOME/.claude/CLAUDE.md"
echo "[bootstrap] Copied CLAUDE.md (Mekong memory)"

# Pre-create claude.json
cat > "$CLAUDE_HOME/.claude.json" <<'EOF'
{"hasCompletedOnboarding":true,"installMethod":"native"}
EOF

# Git configuration
GIT_USER_NAME="${GIT_USER_NAME:-Mekong CLI}"
GIT_USER_EMAIL="${GIT_USER_EMAIL:-noreply@binhphap.io}"
runuser -u claude -- git config --global safe.directory /workspace
runuser -u claude -- git config --global user.name "$GIT_USER_NAME"
runuser -u claude -- git config --global user.email "$GIT_USER_EMAIL"
echo "[bootstrap] Git configured as '$GIT_USER_NAME <$GIT_USER_EMAIL>'"

# Initialize Mekong workspace structure
mkdir -p /workspace/recipes/auto /workspace/plans /workspace/docs
echo "[bootstrap] Workspace directories created"

# Fix ownership
chown -R "$PUID:$PGID" "$CLAUDE_HOME/.claude"
chown "$PUID:$PGID" "$CLAUDE_HOME/.claude.json"

# Sentinel
touch "$CLAUDE_HOME/.claude/.mekong-bootstrapped"
chown "$PUID:$PGID" "$CLAUDE_HOME/.claude/.mekong-bootstrapped"

echo "[bootstrap] Mekong CLI initialization complete."
