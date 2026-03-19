#!/bin/bash
# api-switch.sh — Toggle CC CLI between DashScope Coding Plan and Claude Max 20x
# Usage: ./api-switch.sh dashscope|max20x

set -euo pipefail

SETTINGS="$HOME/.claude/settings.json"

# Define colors for output
YELLOW='\033[1;33m'
GREEN='\033[1;32m'
NC='\033[0m' # No Color

case "${1:-}" in
  dashscope|ds|qwen)
    echo -e "${YELLOW}Switching to DashScope API...${NC}"
    read -p "Enter DashScope API key (sk-...): " DASHSCOPE_API_KEY
    
    # Use a temporary file for cross-platform sed, or python for more robust JSON manipulation
    # For simplicity and to match the instruction's intent for sed, we'll use sed.
    # Note: 'sed -i' behavior differs between GNU sed (Linux) and BSD sed (macOS).
    # The '' after -i is for BSD sed. For GNU sed, it's just -i.
    # We'll use a Python script for robust JSON manipulation as it's already in use.
    python3 -c "
import json
with open('$SETTINGS') as f: d = json.load(f)
d['env']['ANTHROPIC_BASE_URL'] = 'https://coding-intl.dashscope.aliyuncs.com/apps/anthropic'
d['env']['ANTHROPIC_AUTH_TOKEN'] = '$DASHSCOPE_API_KEY'
d['env']['ANTHROPIC_MODEL'] = 'qwen3.5-plus[1m]'
d['model'] = 'qwen3.5-plus[1m]'
d['smallModelId'] = 'qwen3.5-plus[1m]'
d['largeModelId'] = 'qwen3.5-plus[1m]'
with open('$SETTINGS', 'w') as f: json.dump(d, f, indent=2)
print('  BASE_URL: https://coding-intl.dashscope.aliyuncs.com/apps/anthropic')
print('  MODEL:    qwen3.5-plus[1m] (1M context explicit)')
print('  SUBAGENT: qwen3.5-plus[1m] (all)')
print('  KEY:      $DASHSCOPE_API_KEY[:10]...')
"
    echo -e "${GREEN}✅ DashScope mode active. Restart CC CLI to apply.${NC}"
    ;;
    
  max20x|claude|anthropic)
    echo "🚀 Switching to Claude Max 20x..."
    read -p "Enter Anthropic API key (sk-ant-...): " API_KEY
    read -p "Enter model (default: claude-sonnet-4-20250514): " MODEL
    MODEL=${MODEL:-claude-sonnet-4-20250514}
    python3 -c "
import json
with open('$SETTINGS') as f: d = json.load(f)
d['env']['ANTHROPIC_BASE_URL'] = 'https://api.anthropic.com'
d['env']['ANTHROPIC_AUTH_TOKEN'] = '$API_KEY'
d['env']['ANTHROPIC_MODEL'] = '$MODEL'
d['model'] = '$MODEL'
# Remove DashScope-specific model overrides
d.pop('smallModelId', None)
d.pop('largeModelId', None)
with open('$SETTINGS', 'w') as f: json.dump(d, f, indent=2)
print('  BASE_URL: api.anthropic.com')
print('  MODEL:    $MODEL')
print('  SUBAGENT: Haiku/Sonnet (auto by CC CLI)')
print('  KEY:      $API_KEY[:10]...')
"
    echo "✅ Max 20x mode active. Restart CC CLI to apply."
    ;;
    
  status|check)
    python3 -c "
import json
with open('$SETTINGS') as f: d = json.load(f)
url = d.get('env',{}).get('ANTHROPIC_BASE_URL','?')
model = d.get('model','?')
small = d.get('smallModelId','(default)')
large = d.get('largeModelId','(default)')
mode = 'DashScope' if 'dashscope' in url else 'Max 20x' if 'anthropic.com' in url else 'Proxy'
print(f'Mode:     {mode}')
print(f'URL:      {url}')
print(f'Model:    {model}')
print(f'Small:    {small}')
print(f'Large:    {large}')
"
    ;;
    
  *)
    echo "Usage: api-switch.sh <dashscope|max20x|status>"
    echo ""
    echo "Commands:"
    echo "  dashscope (ds, qwen)     — DashScope Coding Plan (\$50/mo)"
    echo "  max20x (claude, anthropic) — Claude Max 20x (Anthropic direct)"
    echo "  status (check)           — Show current API mode"
    ;;
esac
