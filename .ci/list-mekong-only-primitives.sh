#!/usr/bin/env bash
# .ci/list-mekong-only-primitives.sh
#
# Print mekong-cli primitives (skills, commands, agents) that have NO
# counterpart in ~/.claude/ — i.e. candidates worth upstreaming into the
# global ClaudeKit so the broader community can use them.
#
# Output is ranked by file size desc (heuristic: bigger spec = more
# investment = higher upstream value). Each row is tab-separated:
#
#   <bytes>\t<lines>\t<relative-path>
#
# Usage:
#   bash .ci/list-mekong-only-primitives.sh                  # all 3 kinds
#   bash .ci/list-mekong-only-primitives.sh skills           # filter
#   bash .ci/list-mekong-only-primitives.sh skills commands  # multiple
#   bash .ci/list-mekong-only-primitives.sh --top 50         # top 50 only

set -euo pipefail

GLOBAL_CK="${GLOBAL_CLAUDEKIT:-$HOME/.claude}"
MEKONG_CK="${MEKONG_CLAUDEKIT:-$(cd "$(dirname "$0")/.." && pwd)/.claude}"

KINDS=()
TOP=""

while [ $# -gt 0 ]; do
  case "$1" in
    --top) TOP="$2"; shift 2 ;;
    skills|commands|agents) KINDS+=("$1"); shift ;;
    *) echo "unknown arg: $1" >&2; exit 1 ;;
  esac
done

if [ ${#KINDS[@]} -eq 0 ]; then
  KINDS=(skills commands agents)
fi

scan_kind() {
  local kind="$1"
  local mekong_dir="$MEKONG_CK/$kind"
  local global_dir="$GLOBAL_CK/$kind"
  [ -d "$mekong_dir" ] || return 0

  case "$kind" in
    skills)
      # Compare by skill directory name (each skill = one dir)
      while IFS= read -r -d '' m_path; do
        name=$(basename "$m_path")
        if [ ! -d "$global_dir/$name" ]; then
          local skill_md="$m_path/SKILL.md"
          [ -f "$skill_md" ] || continue
          local bytes lines
          bytes=$(wc -c < "$skill_md" | tr -d ' ')
          lines=$(wc -l < "$skill_md" | tr -d ' ')
          printf '%s\t%s\t.claude/skills/%s/SKILL.md\n' "$bytes" "$lines" "$name"
        fi
      done < <(find "$mekong_dir" -mindepth 1 -maxdepth 1 -type d -print0)
      ;;
    commands|agents)
      # Compare by markdown file name
      while IFS= read -r -d '' m_path; do
        name=$(basename "$m_path")
        # Skip private drafts + .local.md
        case "$name" in
          *.local.md) continue ;;
        esac
        case "$m_path" in
          */private/*) continue ;;
        esac
        if [ ! -f "$global_dir/$name" ]; then
          local bytes lines
          bytes=$(wc -c < "$m_path" | tr -d ' ')
          lines=$(wc -l < "$m_path" | tr -d ' ')
          printf '%s\t%s\t.claude/%s/%s\n' "$bytes" "$lines" "$kind" "$name"
        fi
      done < <(find "$mekong_dir" -name '*.md' -type f -print0)
      ;;
  esac
}

{
  for k in "${KINDS[@]}"; do
    scan_kind "$k"
  done
} | sort -rn -k1,1 | { [ -n "$TOP" ] && head -n "$TOP" || cat; }
