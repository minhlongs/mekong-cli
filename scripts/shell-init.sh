#!/bin/bash
# Source from ~/.zshrc: source ~/mekong-cli/scripts/shell-init.sh
export MEKONG_ROOT="${MEKONG_ROOT:-$HOME/mekong-cli}"
export PATH="$MEKONG_ROOT/scripts:$PATH"

# Tool shortcuts
alias mekong='bash $MEKONG_ROOT/scripts/mekong-wrapper.sh'
alias mekong-claude='MEKONG_TOOL=claude bash $MEKONG_ROOT/scripts/mekong-wrapper.sh'
alias mekong-gemini='MEKONG_TOOL=gemini bash $MEKONG_ROOT/scripts/mekong-wrapper.sh'
alias mekong-opencode='MEKONG_TOOL=opencode bash $MEKONG_ROOT/scripts/mekong-wrapper.sh'
alias mekong-aider='MEKONG_TOOL=aider bash $MEKONG_ROOT/scripts/mekong-wrapper.sh'

# Model shortcuts
alias mekong-opus='MEKONG_TOOL=claude MEKONG_MODEL=claude-opus-4-6-20250901 bash $MEKONG_ROOT/scripts/mekong-wrapper.sh'
alias mekong-sonnet='MEKONG_TOOL=claude MEKONG_MODEL=claude-sonnet-4-6-20250514 bash $MEKONG_ROOT/scripts/mekong-wrapper.sh'
alias mekong-qwen='MEKONG_TOOL=claude MEKONG_MODEL=qwen3-coder-plus bash $MEKONG_ROOT/scripts/mekong-wrapper.sh'

# Quick
alias mek='mekong' mkc='mekong-claude' mkg='mekong-gemini'
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
