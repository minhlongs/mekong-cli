#!/usr/bin/env bash
# check-prohibited.sh — Scan Polar-visible surfaces for forbidden keywords
# Usage: bash polar-copy/check-prohibited.sh
# Not wired to pre-commit; run manually before Polar dashboard updates

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PATTERN='\b(AI|A\.I\.|artificial intelligence|machine learning|smart assistant|wellness|health|healthcare|medical|therapy|therapeutic|clinical|patient|prescription|BAA|HIPAA|diagnosis|treatment|trading|crypto|token|investment|gambling)\b'

echo "=== Polar Prohibited Word Scanner ==="
echo "Repo: $REPO_ROOT"
echo ""

TOTAL_VIOLATIONS=0

scan_file() {
  local file="$1"
  local label="$2"
  local hits
  hits=$(grep -niE "$PATTERN" "$file" 2>/dev/null || true)
  local count
  count=$(echo "$hits" | grep -c . 2>/dev/null || echo 0)
  # Subtract exempt lines (URLs in code blocks, CLI command names)
  echo "--- $label ---"
  if [ -z "$hits" ]; then
    echo "  CLEAN (0 hits)"
  else
    echo "$hits" | while IFS= read -r line; do
      echo "  HIT: $line"
    done
    echo "  Raw hits: $count (review each — URLs/code blocks are exempt)"
  fi
  echo ""
}

scan_file "$REPO_ROOT/README.md" "README.md (primary Polar-visible surface)"

# Scan polar-copy product descriptions (actual Polar dashboard copy)
for f in "$REPO_ROOT/polar-copy/product-"*.md; do
  [ -f "$f" ] || continue
  scan_file "$f" "$(basename "$f")"
done

echo "=== Prose-only check (excludes code blocks) ==="
echo "Checking README.md lines NOT inside code fences..."
# Extract prose lines (not inside ``` blocks) and scan
awk '/^```/{in_code=!in_code; next} !in_code{print NR": "$0}' "$REPO_ROOT/README.md" \
  | grep -iE "$PATTERN" || echo "  CLEAN — zero prose violations"

echo ""
echo "=== Checkout URL Status ==="
URLS=(
  "Starter:https://buy.polar.sh/polar_cl_apvIt00Pf7vw2GGX0PW7tWfNjSiwaTRUl0YzO3YqVhA"
  "Growth:https://buy.polar.sh/polar_cl_TDhelBvQfsZq3Rayqf9to4tl0UD6D04OBFqXm1zJDVC"
  "Pro:https://buy.polar.sh/polar_cl_zi7LHdaPk93V0xbNVQZgqum96gWCFDTVzpDNR2kfN3j"
)
for entry in "${URLS[@]}"; do
  tier="${entry%%:*}"
  url="${entry#*:}"
  status=$(curl -sI "$url" 2>/dev/null | head -1 | awk '{print $2}')
  location=$(curl -sI "$url" 2>/dev/null | grep -i "^location:" | awk '{print $2}' || echo "")
  if [ "$status" = "200" ]; then
    echo "  $tier: HTTP $status — ACTIVE"
  else
    echo "  $tier: HTTP $status → $location — INACTIVE (Stripe onboarding required)"
  fi
done

echo ""
echo "=== Summary ==="
echo "Run complete. Review HIT lines above."
echo "Exempt: URLs in code blocks, CLI command names (/health etc), vendor names in URLs."
echo "Any prose violation = FIX BEFORE submitting to Polar dashboard."
