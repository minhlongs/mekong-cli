#!/usr/bin/env bash
set -euo pipefail

# build-dmg.sh - Package Mekong CLI into signed + unsigned DMGs.
# Usage: bash scripts/packaging/build-dmg.sh <app-bundle> [output-dir]

APP_BUNDLE="${1:?Usage: $0 <path-to.app> [output-dir]}"
OUT_DIR="${2:-./out}"
VOL_NAME="${VOL_NAME:-MekongCLI}"
DMG_UNSIGNED="${OUT_DIR}/${VOL_NAME}-unsigned.dmg"
DMG_SIGNED="${OUT_DIR}/${VOL_NAME}-signed.dmg"
TEMP_DMG="${OUT_DIR}/${VOL_NAME}.tmp.dmg"
SIGN_IDENTITY="${SIGN_IDENTITY:-Developer ID Application:}"
NOTARY_PROFILE="${NOTARY_PROFILE:-mekong-notary}"

command -v hdiutil >/dev/null 2>&1 || { echo "ERROR: hdiutil not found"; exit 1; }
[[ -d "$APP_BUNDLE" ]] || { echo "ERROR: app bundle not found"; exit 1; }
mkdir -p "$OUT_DIR"

# Check signing identity
IDENTITY_LINE=$(security find-identity -v 2>/dev/null \
  | grep -E "Developer ID Application|Apple Distribution" \
  | head -n1 || true)
HAS_IDENTITY=false
if [[ -n "$IDENTITY_LINE" ]]; then
  echo "Developer identity found: $IDENTITY_LINE"
  SIGN_IDENTITY=$(echo "$IDENTITY_LINE" | awk '{print $3}')
  HAS_IDENTITY=true
else
  echo "No developer signing identity available."
fi

# Stage the app
STAGING=$(mktemp -d "${TMPDIR:-/tmp}/mekong-dmg-XXXXXX")
trap 'rm -rf "$STAGING"' EXIT
cp -R "$APP_BUNDLE" "$STAGING/"

echo "[1/4] Creating base DMG ..."
hdiutil create -quiet -srcfolder "$STAGING" -volname "$VOL_NAME" -fs HFS+ -format UDRW -ov -o "$DMG_UNSIGNED"

echo "[2/4] Compressing to read-only ..."
hdiutil convert -quiet "$DMG_UNSIGNED" -format UDZO -o "$TEMP_DMG"
mv "$TEMP_DMG" "$DMG_UNSIGNED"
echo "  -> Unsigned: $DMG_UNSIGNED"

# Sign if identity is available
if [[ "$HAS_IDENTITY" == true ]]; then
  echo "[3/4] Signing with identity: $SIGN_IDENTITY ..."
  hdiutil sign -quiet -sign "$SIGN_IDENTITY" -timestamp -o "$DMG_SIGNED" "$DMG_UNSIGNED"
  echo "  -> Signed (pre-notarization): $DMG_SIGNED"

  echo "[4/4] Notarizing ..."
  if xcrun notarytool submit "$DMG_SIGNED" --profile "$NOTARY_PROFILE" --wait 2>/dev/null; then
    echo "  Stapling notarization ticket ..."
    xcrun stapler staple "$DMG_SIGNED"
    echo "  -> Signed + notarized: $DMG_SIGNED"
  else
    echo "  WARN: notarytool failed; DMG is signed but not notarized."
  fi
else
  echo "[3/4] Skipping signing (no identity)."
  echo "[4/4] Skipping notarization."
fi

echo ""
echo "Done. Artifacts in $OUT_DIR/:"
[[ -f "$DMG_UNSIGNED" ]] && echo "  unsigned : $DMG_UNSIGNED"
[[ -f "$DMG_SIGNED" ]] && echo "  signed   : $DMG_SIGNED"
