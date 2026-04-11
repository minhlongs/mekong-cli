#!/bin/bash
# Build all frontends into 1 output directory for mekongmind CF Pages project.
# Output: dist/site/
#   /           → landing hub (from landing/dist)
#   /use-cases/ → 13 tenant pages
#   /ide/       → IDE app (from apps/mekong-ide/out)
#   /dashboard/ → Dashboard (from apps/agencyos-web/out)
#   /reports/   → report renderer (SPA stub)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$REPO_ROOT/dist/site"

echo "=== Mekong Unified Site Builder ==="
echo "Output: $OUT"

# ── Clean output ─────────────────────────────────────────────────────────────
rm -rf "$OUT"
mkdir -p "$OUT"

# Set SKIP_BUILDS=1 in CI when builds are pre-run in separate steps
SKIP_BUILDS="${SKIP_BUILDS:-0}"

if [ "$SKIP_BUILDS" != "1" ]; then
  # ── Step 1: Build IDE (Next.js static export) ──────────────────────────────
  echo ""
  echo "[1/4] Building IDE..."
  cd "$REPO_ROOT/apps/mekong-ide"
  npm install --silent
  npx next build
  cd "$REPO_ROOT"
  echo "      IDE built → apps/mekong-ide/out/"

  # ── Step 2: Build landing pages (Python/Jinja2) ────────────────────────────
  echo ""
  echo "[2/4] Building landing pages..."
  pip install --quiet jinja2 markupsafe
  python3 "$REPO_ROOT/landing/build.py"
  echo "      Landing built → landing/dist/"

  # ── Step 3: Build dashboard (Next.js static export) ───────────────────────
  echo ""
  echo "[3/4] Building dashboard..."
  cd "$REPO_ROOT/apps/agencyos-web"
  npm install --silent
  npx next build
  cd "$REPO_ROOT"
  echo "      Dashboard built → apps/agencyos-web/out/"
else
  echo ""
  echo "[1-3/4] Skipping builds (SKIP_BUILDS=1, using pre-built artifacts)"
fi

# ── Step 4: Merge into unified output ────────────────────────────────────────
echo ""
echo "[4/4] Merging into $OUT ..."

# Landing at root (hub index + static/)
cp -r "$REPO_ROOT/landing/dist/." "$OUT/"

# Tenant pages under /use-cases/
mkdir -p "$OUT/use-cases"
for slug_dir in "$REPO_ROOT/landing/dist"/*/; do
  slug="$(basename "$slug_dir")"
  # Skip non-tenant dirs (static, _* files)
  [[ "$slug" == static ]] && continue
  [[ "$slug" == _* ]] && continue
  cp -r "$slug_dir" "$OUT/use-cases/$slug"
done
# Copy hub index
cp "$REPO_ROOT/landing/dist/index.html" "$OUT/use-cases/index.html" 2>/dev/null
cp -r "$REPO_ROOT/landing/dist/static" "$OUT/use-cases/static" 2>/dev/null
echo "      Tenant pages + hub → $OUT/use-cases/"

# IDE under /ide/  — next export puts files at top-level, wrap in subdir
mkdir -p "$OUT/ide"
cp -r "$REPO_ROOT/apps/mekong-ide/out/." "$OUT/ide/"
echo "      IDE → $OUT/ide/"

# Dashboard under /dashboard/
mkdir -p "$OUT/dashboard"
cp -r "$REPO_ROOT/apps/agencyos-web/out/." "$OUT/dashboard/"
echo "      Dashboard → $OUT/dashboard/"

# ── Generate _redirects ───────────────────────────────────────────────────────
cat > "$OUT/_redirects" <<'REDIRECTS'
# Tenant use-case clean URLs
/use-cases/:slug /use-cases/:slug/index.html 200

# IDE — SPA catch-all
/ide/* /ide/index.html 200

# Reports — SPA catch-all (renderer served from /ide/reports)
/reports /ide/reports.html 200
/reports/* /ide/reports.html 200

# Dashboard — SPA catch-all
/dashboard /dashboard/index.html 200
/dashboard/* /dashboard/index.html 200
REDIRECTS

# ── Generate _headers ─────────────────────────────────────────────────────────
cat > "$OUT/_headers" <<'HEADERS'
/*
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  Strict-Transport-Security: max-age=31536000; includeSubDomains
  Referrer-Policy: strict-origin-when-cross-origin
  Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self' http://localhost:* https://*.mekongmind.com https://api.cashclaw.cc https://polar.sh; font-src 'self'
HEADERS

echo ""
echo "=== Build complete ==="
echo "Output size: $(du -sh "$OUT" | cut -f1)"
echo "Files: $(find "$OUT" -type f | wc -l | tr -d ' ')"
echo ""
echo "To deploy:"
echo "  wrangler pages deploy dist/site --project-name mekongmind"
