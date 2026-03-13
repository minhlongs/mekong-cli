#!/bin/zsh
# ═══════════════════════════════════════════════════════════════
# 🦞 TÔM HÙM FACTORY v4 — Equal Grid Layout
# N agents → automatic NxN grid (2x2, 2x3, 3x3, etc.)
# ═══════════════════════════════════════════════════════════════

PROJECT="${1:-/Users/mac/mekong-cli}"
SESSION="tom_hum"
NUM_AGENTS="${2:-4}"  # Default 4, can pass more

# Homebrew PATH
eval "$(/opt/homebrew/bin/brew shellenv)" 2>/dev/null || true
export PATH="$HOME/bin:$PATH"

echo "🦞 TÔM HÙM FACTORY v4 — $NUM_AGENTS Agents"
echo "📁 $PROJECT"

# Kill old session
tmux kill-session -t $SESSION 2>/dev/null || true
sleep 1

# Agent configs: name, config_dir
AGENT_NAMES=("CTO" "BUILDER" "TESTER" "DESIGNER" "PLANNER" "REVIEWER" "FIXER" "SCOUT")
AGENT_ICONS=("🧠" "⚡" "🔍" "🎨" "📋" "📝" "🔧" "🔭")
AGENT_CONFIGS=(
    "$HOME/.claude-planner"
    "$HOME/.claude-developer"
    "$HOME/.claude-tester"
    "$HOME/.claude-planner"
    "$HOME/.claude-planner"
    "$HOME/.claude-tester"
    "$HOME/.claude-developer"
    "$HOME/.claude-tester"
)

# ═══ Create session with P0 ═══
tmux new-session -d -s $SESSION -x 220 -y 55 -c "$PROJECT" \
  "echo '${AGENT_ICONS[1]} [P0: ${AGENT_NAMES[1]}] — bypass on'; CLAUDE_CONFIG_DIR=${AGENT_CONFIGS[1]} claude --dangerously-skip-permissions; zsh"

# ═══ Create remaining panes ═══
for ((i=1; i<NUM_AGENTS; i++)); do
    local_name="${AGENT_NAMES[$((i+1))]:-WORKER$i}"
    local_icon="${AGENT_ICONS[$((i+1))]:-🤖}"
    local_config="${AGENT_CONFIGS[$((i+1))]:-$HOME/.claude-planner}"

    tmux split-window -t $SESSION -c "$PROJECT" \
      "echo '${local_icon} [P${i}: ${local_name}] — bypass on'; CLAUDE_CONFIG_DIR=${local_config} claude --dangerously-skip-permissions; zsh"

    # After each split, re-tile to keep equal
    tmux select-layout -t $SESSION tiled 2>/dev/null || true
done

# ═══ Final equal layout ═══
tmux select-layout -t $SESSION tiled

# ─── Status Bar (Mekong style) ───
tmux set -t $SESSION status-style "bg=#0a0a1a,fg=#00ff88"
tmux set -t $SESSION status-left "#[fg=#e94560,bold] 🦞 TÔM HÙM #[fg=#00ff88]│"
tmux set -t $SESSION status-left-length 30
tmux set -t $SESSION status-right "#[fg=#888]qwen3.5-plus#[fg=#00ff88] │ %H:%M │ $NUM_AGENTS Agents "
tmux set -t $SESSION status-right-length 50
tmux set -t $SESSION pane-border-style "fg=#16213e"
tmux set -t $SESSION pane-active-border-style "fg=#e94560,bold"
tmux set -t $SESSION window-status-current-format "#[fg=#e94560]● #W"

# Pane titles
for ((i=0; i<NUM_AGENTS; i++)); do
    local_name="${AGENT_NAMES[$((i+1))]:-WORKER$i}"
    local_icon="${AGENT_ICONS[$((i+1))]:-🤖}"
    tmux select-pane -t $SESSION:0.$i -T "${local_icon} P${i}:${local_name}" 2>/dev/null || true
done
tmux set -t $SESSION pane-border-format " #{pane_title} " 2>/dev/null || true
tmux set -t $SESSION pane-border-status top 2>/dev/null || true

# Focus P0
tmux select-pane -t $SESSION:0.0

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  🦞 TÔM HÙM FACTORY v4 — ${NUM_AGENTS} Agents Equal Grid        ║"
echo "╠═══════════════════════════════════════════════════════════╣"
for ((i=0; i<NUM_AGENTS; i++)); do
    local_name="${AGENT_NAMES[$((i+1))]:-WORKER$i}"
    local_icon="${AGENT_ICONS[$((i+1))]:-🤖}"
    printf "║  P%d: %-10s │ %s                                  ║\n" $i "$local_name" "$local_icon"
done
echo "╠═══════════════════════════════════════════════════════════╣"
echo "║  Ctrl-B + ←↑↓→  Navigate panes                         ║"
echo "║  Ctrl-B + Z      Zoom pane                              ║"
echo "║  Ctrl-B + D      Detach (session keeps running)         ║"
echo "╚═══════════════════════════════════════════════════════════╝"

tmux attach -t $SESSION
