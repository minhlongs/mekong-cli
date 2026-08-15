#!/bin/bash
# Migration Rollback Script
# Provides instant rollback from plugin mode to legacy mode

set -e

echo "🔄 Command Migration Rollback"
echo "=============================="

ROLLBACK_MODE=${1:-"full"}  # full, layer, or plugin

case "$ROLLBACK_MODE" in
  full)
    echo "Mode: FULL SYSTEM ROLLBACK"
    echo "  - Disabling plugin system"
    echo "  - Switching all layers to legacy"
    echo ""

    # Method 1: Environment variable (immediate, temporary)
    export MEKONG_FEATURE_PLUGIN_SYSTEM_ENABLED=false
    export MEKONG_LEGACY_MODE=true

    # Method 2: Update settings.json (persistent)
    if [ -f "$HOME/.mekong/settings.json" ]; then
      echo "Updating ~/.mekong/settings.json..."
      tmp=$(mktemp)
      jq '.plugin_system.enabled = false | .feature_flags.plugin_founder = "legacy" | .feature_flags.plugin_business = "legacy" | .feature_flags.plugin_product = "legacy" | .feature_flags.plugin_engineering = "legacy" | .feature_flags.plugin_ops = "legacy" | .feature_flags.plugin_studio = "legacy"' "$HOME/.mekong/settings.json" > "$tmp" && mv "$tmp" "$HOME/.mekong/settings.json"
    fi

    echo ""
    echo "✅ Full rollback complete"
    echo "   All commands will use legacy implementation"
    echo ""
    echo "To re-enable plugins:"
    echo "  unset MEKONG_FEATURE_PLUGIN_SYSTEM_ENABLED MEKONG_LEGACY_MODE"
    echo "  # or set settings.json plugin_system.enabled = true"
    ;;

  layer)
    LAYER=${2:?Layer name required (founder|business|product|engineering|ops|studio)}
    echo "Mode: LAYER ROLLBACK"
    echo "  Layer: $LAYER"
    echo "  Switching to legacy implementation"
    echo ""

    # Disable specific layer plugin
    export MEKONG_FEATURE_PLUGIN_${LAYER^^}=legacy

    if [ -f "$HOME/.mekong/settings.json" ]; then
      tmp=$(mktemp)
      jq --arg layer "$LAYER" '.feature_flags["plugin_" + $layer] = "legacy"' "$HOME/.mekong/settings.json" > "$tmp" && mv "$tmp" "$HOME/.mekong/settings.json"
    fi

    echo ""
    echo "✅ Layer $LAYER rolled back to legacy"
    echo ""
    echo "To re-enable plugin for this layer:"
    echo "  export MEKONG_FEATURE_PLUGIN_${LAYER^^}=plugin"
    ;;

  plugin)
    PLUGIN_ID=${2:?Plugin ID required}
    echo "Mode: PLUGIN DISABLE"
    echo "  Plugin: $PLUGIN_ID"
    echo ""

    if mekong admin plugin disable "$PLUGIN_ID"; then
      echo ""
      echo "✅ Plugin $PLUGIN_ID disabled"
      echo ""
      echo "To re-enable:"
      echo "  mekong admin plugin enable $PLUGIN_ID"
    else
      echo "❌ Failed to disable plugin"
      exit 1
    fi
    ;;

  *)
    echo "Usage: $0 [full|layer <layer>|plugin <plugin-id>]"
    echo ""
    echo "Modes:"
    echo "  full              - Rollback entire plugin system to legacy"
    echo "  layer <layer>     - Rollback specific layer (founder, business, etc.)"
    echo "  plugin <plugin>   - Disable specific plugin"
    echo ""
    echo "Examples:"
    echo "  $0 full                    # Emergency full rollback"
    echo "  $0 layer founder           # Rollback founder layer only"
    echo "  $0 plugin mekong-core-founder  # Disable specific plugin"
    exit 1
    ;;
esac
