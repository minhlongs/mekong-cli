#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# MEKONG SHELL INIT — Add to ~/.zshrc or ~/.bashrc:
#   source ~/mekong-cli/scripts/shell-init.sh
# ═══════════════════════════════════════════════════════════════

export MEKONG_ROOT="${MEKONG_ROOT:-$HOME/mekong-cli}"
export PATH="$MEKONG_ROOT/scripts:$PATH"

# ─── ALIASES: Tool-specific shortcuts ───
alias mekong='bash $MEKONG_ROOT/scripts/mekong-wrapper.sh'
alias mekong-claude='MEKONG_TOOL=claude bash $MEKONG_ROOT/scripts/mekong-wrapper.sh'
alias mekong-gemini='MEKONG_TOOL=gemini bash $MEKONG_ROOT/scripts/mekong-wrapper.sh'
alias mekong-opencode='MEKONG_TOOL=opencode bash $MEKONG_ROOT/scripts/mekong-wrapper.sh'
alias mekong-aider='MEKONG_TOOL=aider bash $MEKONG_ROOT/scripts/mekong-wrapper.sh'

# ─── ALIASES: Model-specific shortcuts ───
alias mekong-opus='MEKONG_TOOL=claude MEKONG_MODEL=claude-opus-4-0520 bash $MEKONG_ROOT/scripts/mekong-wrapper.sh'
alias mekong-sonnet='MEKONG_TOOL=claude MEKONG_MODEL=claude-sonnet-4-20250514 bash $MEKONG_ROOT/scripts/mekong-wrapper.sh'
alias mekong-qwen='MEKONG_TOOL=claude MEKONG_MODEL=qwen3.5-plus bash $MEKONG_ROOT/scripts/mekong-wrapper.sh'

# ─── ALIASES: CTO daemon ───
alias mekong-cto='MEKONG_TOOL=claude MEKONG_MODE=cto bash $MEKONG_ROOT/scripts/mekong-wrapper.sh --cto'
alias mekong-status='bash $MEKONG_ROOT/scripts/mekong-wrapper.sh --status'
alias mekong-continue='bash $MEKONG_ROOT/scripts/mekong-wrapper.sh --continue'

# ─── ALIASES: Quick commands ───
alias mek='mekong'
alias mkc='mekong-claude'
alias mkg='mekong-gemini'

# ─── Override bare `claude` ───
unalias claude 2>/dev/null
alias claude='cd $MEKONG_ROOT && command claude --dangerously-skip-permissions'

# ─── Quick dispatch ───
mekong-print() {
  bash "$MEKONG_ROOT/scripts/mekong-wrapper.sh" --tool "${MEKONG_TOOL:-auto}" -p "$*"
}

mekong-cook() {
  bash "$MEKONG_ROOT/scripts/mekong-wrapper.sh" --tool "${MEKONG_TOOL:-auto}" -p "/cook \"$*\""
}

echo "🏯 Mekong CLI loaded | $(find $MEKONG_ROOT/.claude/commands -name '*.md' 2>/dev/null | wc -l | tr -d ' ') commands | $(find $MEKONG_ROOT/.claude/skills -name 'SKILL.md' 2>/dev/null | wc -l | tr -d ' ') skills"
