#!/usr/bin/env bash
# self-update.sh — Check GitHub releases and self-update mekong binary.
set -euo pipefail

REPO="mekong-cli/mekong-cli"
BIN_NAME="mekong"
TMP_DIR="$(mktemp -d)"
CURRENT_VERSION="$(mekong --version 2>/dev/null || echo unknown)"

cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

echo "Checking for updates (current: $CURRENT_VERSION)..."

LATEST_TAG=$(curl -fsSL "https://api.github.com/repos/${REPO}/releases/latest" | grep '"tag_name"' | head -1 | cut -d'"' -f4 || true)
if [[ -z "$LATEST_TAG" ]]; then
  echo "WARNING: Could not fetch latest release — staying on $CURRENT_VERSION"
  exit 0
fi

if [[ "$LATEST_TAG" == "v${CURRENT_VERSION}" ]]; then
  echo "Already up to date: $CURRENT_VERSION"
  exit 0
fi

echo "New version available: $LATEST_TAG (current: $CURRENT_VERSION)"
echo "Run: brew upgrade mekong"
echo "Or download DMG from: https://github.com/${REPO}/releases/latest"
