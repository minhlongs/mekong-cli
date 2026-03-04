#!/usr/bin/env bash
# 🦞 Switch CC CLI → Claude Max 20x (Opus 4.6)
# Chạy 1 lần: ./switch-to-max.sh — CC CLI dùng Anthropic native
set -euo pipefail

SETTINGS="$HOME/.claude/settings.json"

echo "🔄 Switching to Claude Max 20x (Opus 4.6)..."

# Backup current
cp "$SETTINGS" "$SETTINGS.bak" 2>/dev/null || true

# Switch model + API
python3 -c "
import json
with open('$SETTINGS') as f: d = json.load(f)
d['model'] = 'claude-opus-4-6'
# Remove custom base URL — use Anthropic direct
d.pop('apiBaseUrl', None)
# Ensure ANTHROPIC_BASE_URL points to official (not proxy for Qwen)
env = d.get('env', {})
env['ANTHROPIC_BASE_URL'] = 'https://api.anthropic.com'
d['env'] = env
with open('$SETTINGS', 'w') as f: json.dump(d, f, indent=2)
"

echo "✅ Model: claude-opus-4-6"
echo "✅ API: Anthropic Direct (Max 20x native rotation)"
echo "✅ ĐIỀU 57: Inactive (Max handles subagent distribution)"
echo ""
echo "⚠️  Restart CC CLI sessions to apply:"
echo "    tmux send-keys -t tom_hum:0.0 '/model claude-opus-4-6' Enter"
echo "    tmux send-keys -t tom_hum:0.1 '/model claude-opus-4-6' Enter"
echo "    tmux send-keys -t tom_hum:0.2 '/model claude-opus-4-6' Enter"
