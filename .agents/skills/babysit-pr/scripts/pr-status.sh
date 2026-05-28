#!/bin/bash
# One-line PR health summary
# Usage: ./pr-status.sh <pr_number>

PR="${1:?Usage: $0 <pr_number>}"

gh pr view "$PR" --json state,mergeable,title,statusCheckRollup \
  --jq '"PR #\(.number // "?") [\(.state)] mergeable=\(.mergeable // "unknown") checks=\((.statusCheckRollup // [] | map(select(.conclusion == "failure")) | length)) failed — \(.title)"'
