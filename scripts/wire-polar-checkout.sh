#!/bin/bash
# Wire real Polar.sh product IDs into codebase
# Run after: python3 scripts/create-polar-products.py
#
# Usage:
#   export STARTER_ID=prod_xxx
#   export GROWTH_ID=prod_xxx
#   export PRO_ID=prod_xxx
#   bash scripts/wire-polar-checkout.sh

set -e

if [ -z "$STARTER_ID" ] || [ -z "$GROWTH_ID" ] || [ -z "$PRO_ID" ]; then
    echo "Set product IDs first:"
    echo "  export STARTER_ID=prod_xxx"
    echo "  export GROWTH_ID=prod_xxx"
    echo "  export PRO_ID=prod_xxx"
    echo ""
    echo "Get IDs from: python3 scripts/create-polar-products.py"
    exit 1
fi

POLAR_ORG="${POLAR_ORG:-longtho638-jpg}"
CHECKOUT_BASE="https://polar.sh/$POLAR_ORG/checkout"

echo "═══ Wiring Polar checkout ═══"
echo "  Starter: $STARTER_ID"
echo "  Growth:  $GROWTH_ID"
echo "  Pro:     $PRO_ID"
echo ""

# 1. Revenue router — replace placeholder price IDs
echo "1. revenue_router.py"
sed -i '' "s/\"price_starter\"/\"$STARTER_ID\"/g" src/raas/revenue_router.py 2>/dev/null || \
sed -i "s/\"price_starter\"/\"$STARTER_ID\"/g" src/raas/revenue_router.py
sed -i '' "s/\"price_growth\"/\"$GROWTH_ID\"/g" src/raas/revenue_router.py 2>/dev/null || \
sed -i "s/\"price_growth\"/\"$GROWTH_ID\"/g" src/raas/revenue_router.py
sed -i '' "s/\"price_pro\"/\"$PRO_ID\"/g" src/raas/revenue_router.py 2>/dev/null || \
sed -i "s/\"price_pro\"/\"$PRO_ID\"/g" src/raas/revenue_router.py
echo "  ✅ Price IDs replaced"

# 2. Pricing page — wire checkout links
echo "2. pricing/index.html"
STARTER_URL="$CHECKOUT_BASE?products=$STARTER_ID"
GROWTH_URL="$CHECKOUT_BASE?products=$GROWTH_ID"
PRO_URL="$CHECKOUT_BASE?products=$PRO_ID"

# Replace placeholder hrefs
python3 -c "
with open('apps/landing/pricing/index.html') as f: h = f.read()
links = h.split('href=\"https://polar.sh/longtho638-jpg\"')
if len(links) >= 4:
    h = links[0] + 'href=\"$STARTER_URL\"' + links[1] + 'href=\"$GROWTH_URL\"' + links[2] + 'href=\"$PRO_URL\"' + links[3]
    with open('apps/landing/pricing/index.html','w') as f: f.write(h)
    print('  ✅ Checkout URLs wired')
else:
    print('  ⚠️  Manual update needed — placeholder format changed')
"

# 3. MekongMind landing
echo "3. mekonmind landing"
if [ -f apps/mekonmind-landing/index.html ]; then
    sed -i '' "s|https://github.com/longtho638-jpg/mekong-cli|$GROWTH_URL|g" apps/mekonmind-landing/index.html 2>/dev/null || \
    sed -i "s|https://github.com/longtho638-jpg/mekong-cli|$GROWTH_URL|g" apps/mekonmind-landing/index.html
    echo "  ✅ MekongMind links → Polar checkout"
fi

echo ""
echo "═══ Done. Verify: ═══"
grep "$STARTER_ID" src/raas/revenue_router.py | head -1
echo ""
echo "Commit:"
echo "  git add -A && git commit -m 'feat: wire Polar checkout — real product IDs'"
echo "  git push origin main"
