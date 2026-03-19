#!/bin/bash
# ═══════════════════════════════════════════════════════════
# MEKONG-CLI Shell Init — source this in .zshrc / .bashrc
# Usage: source ~/mekong-cli/scripts/shell-init.sh
# ═══════════════════════════════════════════════════════════

export MEKONG_ROOT="${MEKONG_ROOT:-$HOME/mekong-cli}"
export PATH="$MEKONG_ROOT/scripts:$PATH"

# ═══ Core Aliases ═══
alias mekong='bash $MEKONG_ROOT/scripts/mekong-wrapper.sh'
alias mekong-opus='MEKONG_PROVIDER=opus bash $MEKONG_ROOT/scripts/mekong-wrapper.sh'
alias mekong-sonnet='MEKONG_PROVIDER=sonnet bash $MEKONG_ROOT/scripts/mekong-wrapper.sh'
alias mekong-qwen='MEKONG_PROVIDER=qwen bash $MEKONG_ROOT/scripts/mekong-wrapper.sh'
alias mekong-gemini='MEKONG_PROVIDER=gemini bash $MEKONG_ROOT/scripts/mekong-wrapper.sh'
alias mekong-opencode='MEKONG_PROVIDER=opencode bash $MEKONG_ROOT/scripts/mekong-wrapper.sh'
alias mekong-cto='MEKONG_PROVIDER=claude MEKONG_MODE=cto bash $MEKONG_ROOT/scripts/mekong-wrapper.sh'
alias mekong-continue='bash $MEKONG_ROOT/scripts/mekong-wrapper.sh --continue'
alias mekong-status='bash $MEKONG_ROOT/scripts/mekong-wrapper.sh --quiet --print "echo status" 2>/dev/null; echo "Provider: ${MEKONG_PROVIDER:-claude}"; echo "Root: $MEKONG_ROOT"; echo "Commands: $(find $MEKONG_ROOT/.claude/commands -name "*.md" 2>/dev/null | wc -l | tr -d " ")"; echo "Skills: $(find $MEKONG_ROOT/.claude/skills -name "SKILL.md" 2>/dev/null | wc -l | tr -d " ")"'

# ═══ Print mode (non-interactive) ═══
mekong-print() {
  bash "$MEKONG_ROOT/scripts/mekong-wrapper.sh" --print "$*"
}

# ═══ Quick dispatch ═══
mekong-cook() {
  bash "$MEKONG_ROOT/scripts/mekong-wrapper.sh" --print "/cook \"$*\""
}

# ═══ Override bare `claude` to always run from mekong root ═══
unalias claude 2>/dev/null
alias claude='cd $MEKONG_ROOT && command claude --dangerously-skip-permissions'

# ═══ Completion hint ═══
if [[ -n "${ZSH_VERSION:-}" ]]; then
  # Zsh completion
  _mekong_complete() {
    local commands=($(find "$MEKONG_ROOT/.claude/commands" -name "*.md" -exec basename {} .md \; 2>/dev/null | sort))
    compadd -- "${commands[@]}"
  }
  compdef _mekong_complete mekong mekong-opus mekong-sonnet mekong-qwen
fi

echo "🌊 MEKONG CLI loaded | $(find $MEKONG_ROOT/.claude/commands -name '*.md' 2>/dev/null | wc -l | tr -d ' ') commands | $(find $MEKONG_ROOT/.claude/skills -name 'SKILL.md' 2>/dev/null | wc -l | tr -d ' ') skills"
