#!/bin/bash
# Source from ~/.zshrc: source ~/mekong-cli/scripts/shell-init.sh
export MEKONG_ROOT="${MEKONG_ROOT:-$HOME/mekong-cli}"
export PATH="$MEKONG_ROOT/scripts:$MEKONG_ROOT/harness/bin:$PATH"

# Tool shortcuts
alias mekong='bash $MEKONG_ROOT/scripts/mekong-wrapper.sh'
alias mekong-claude='MEKONG_TOOL=claude bash $MEKONG_ROOT/scripts/mekong-wrapper.sh'
alias mekong-gemini='MEKONG_TOOL=gemini bash $MEKONG_ROOT/scripts/mekong-wrapper.sh'
alias mekong-opencode='MEKONG_TOOL=opencode bash $MEKONG_ROOT/scripts/mekong-wrapper.sh'
alias mekong-aider='MEKONG_TOOL=aider bash $MEKONG_ROOT/scripts/mekong-wrapper.sh'

# NEW: Dual CLI harness entry points (mk = Mekong persona, ak = Agent Kit persona)
alias mk='npx tsx $MEKONG_ROOT/harness/bin/mk.ts'
alias ak='npx tsx $MEKONG_ROOT/harness/bin/ak.ts'
alias mk-compiled='node $MEKONG_ROOT/harness/dist/bin/mk.js'
alias ak-compiled='node $MEKONG_ROOT/harness/dist/bin/ak.js'

# Model shortcuts (ZuneF API — claude-api.zunef.com/v1/ai)
alias mekong-opus='MEKONG_TOOL=claude MEKONG_MODEL=claude-opus-4-8 bash $MEKONG_ROOT/scripts/mekong-wrapper.sh'
alias mekong-sonnet='MEKONG_TOOL=claude MEKONG_MODEL=claude-sonnet-5-0 bash $MEKONG_ROOT/scripts/mekong-wrapper.sh'
alias mekong-fable='MEKONG_TOOL=claude MEKONG_MODEL=claude-fable-5 bash $MEKONG_ROOT/scripts/mekong-wrapper.sh'
alias mekong-haiku='MEKONG_TOOL=claude MEKONG_MODEL=claude-haiku-4-5 bash $MEKONG_ROOT/scripts/mekong-wrapper.sh'
alias mekong-deep='MEKONG_TOOL=claude MEKONG_MODEL=claude-opus-4-6[1m] bash $MEKONG_ROOT/scripts/mekong-wrapper.sh'

# Qwen shortcuts (DashScope Coding Plan — 90K req/mo)
alias mekong-qwen='MEKONG_TOOL=qwen bash $MEKONG_ROOT/scripts/mekong-wrapper.sh'
alias mekong-qwen-api='MEKONG_TOOL=claude MEKONG_MODEL=qwen3.5-plus bash $MEKONG_ROOT/scripts/mekong-wrapper.sh'

# Local LLM shortcut (M1 Max MLX — FREE, 24/7)
alias mekong-local='python3 $MEKONG_ROOT/src/daemon/agent_loop.py'

# RaaS Gateway bridge
alias mekong-raas='bash $MEKONG_ROOT/scripts/raas-bridge.sh'

# Quick
alias mek='mekong' mkc='mekong-claude' mkg='mekong-gemini' mkq='mekong-qwen'
alias mekong-cto='bash $MEKONG_ROOT/cto-daemon.sh'
alias mekong-health='bash $MEKONG_ROOT/scripts/cto-health-check.sh'

# Completion
_mekong_comp() {
  local cur="${COMP_WORDS[COMP_CWORD]}"
  local cmds=$(ls "$MEKONG_ROOT/.claude/commands/" 2>/dev/null | sed 's/\.md$//' | tr '\n' ' ')
  COMPREPLY=($(compgen -W "--tool --model --interactive --list-tools --status $cmds" -- "$cur"))
}
complete -F _mekong_comp mekong mekong-claude mekong-gemini mekong-opencode mekong-aider mek 2>/dev/null

echo "🏯 Mekong CLI loaded. $(source $MEKONG_ROOT/mekong/adapters/registry.sh 2>/dev/null && echo "Tools: $(list_available_tools)" || echo "")"
echo "   Dual CLI: 'mk' (Mekong) | 'ak' (Agent Kit) — both on shared harness"

# Mekong bootstrap init (CK init harness)
source "$MEKONG_ROOT/scripts/bootstrap-init.sh" --quiet 2>/dev/null || true

# project-idea alias: chạy /project-idea từ shell
project-idea() { echo "/project-idea $*" | mekong --print 2>/dev/null || echo "⚠️  Run 'mekong' first, then type: /project-idea $*"; }
