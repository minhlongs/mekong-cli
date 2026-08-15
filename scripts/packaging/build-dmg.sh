#!/usr/bin/env bash
# build-dmg.sh — Create signed + notarized DMG for macOS ARM64.
set -euo pipefail

APP_NAME="Mekong"
DMG_NAME="${APP_NAME}-6.0.0-arm64.dmg"
STAGING="dist/dmg-staging"

rm -rf "$STAGING" dist/Mekong-*.dmg
mkdir -p "$STAGING"

cp dist/mekong "$STAGING/"
ln -s /Applications "$STAGING/Applications"

hdiutil create -volname "$APP_NAME" -srcfolder "$STAGING" -format UDZO -ov -o "dist/${DMG_NAME}"

echo "DMG built: dist/${DMG_NAME}"
