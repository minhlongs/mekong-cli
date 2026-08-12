#!/usr/bin/env python3
"""Migrate command modules to plugin format.

This script automates the migration of legacy command modules from src/commands/
to plugin format in plugins/mekong-core-{layer}/

Usage:
    python3 scripts/migrate-commands-to-plugins.py [--dry-run] [--output OUTPUT]

Options:
    --dry-run        Show what would be created without doing it
    --output OUTPUT  Output directory (default: plugins/)
    --layer LAYER   Only migrate specific layer (founder|business|product|engineering|ops|studio)
    --force         Overwrite existing plugins
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.plugins.command_plugin_factory import CommandPluginFactory  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Migrate legacy command modules to plugin format"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without doing it",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("plugins"),
        help="Output directory (default: plugins/)",
    )
    parser.add_argument(
        "--layer",
        type=str,
        help="Only migrate specific layer (founder|business|product|engineering|ops|studio)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing plugins",
    )

    args = parser.parse_args()

    try:
        factory = CommandPluginFactory()

        # Scan modules
        logger.info("Scanning command modules...")
        modules = factory.scan_command_modules()

        if not modules:
            logger.warning("No command modules found!")
            return 1

        # Group by layer
        by_layer: dict[str, list] = {}
        for module in modules:
            by_layer.setdefault(module.layer, []).append(module)

        logger.info("Found %d layers: %s", len(by_layer), ", ".join(sorted(by_layer.keys())))

        # Filter by layer if specified
        if args.layer:
            if args.layer not in by_layer:
                logger.error("Layer '%s' not found. Available: %s", args.layer, ", ".join(by_layer.keys()))
                return 1
            by_layer = {args.layer: by_layer[args.layer]}

        # Show what would be done
        total_commands = sum(len(mod.commands) for mods in by_layer.values() for mod in mods)
        logger.info("Total: %d modules, %d commands", sum(len(mods) for mods in by_layer.values()), total_commands)

        if args.dry_run:
            logger.info("=== DRY RUN ===")
            for layer, mods in sorted(by_layer.items()):
                print(f"\nLayer: {layer}")
                for mod in mods:
                    plugin_dir = args.output / f"mekong-core-{layer}"
                    print(f"  Would create: {plugin_dir}/")
                    print(f"    From: {mod.path}")
                    print(f"    Commands: {', '.join(mod.commands)}")
            return 0

        # Create plugins
        created_dirs = []
        for layer, mods in sorted(by_layer.items()):
            logger.info("Migrating layer: %s (%d modules)", layer, len(mods))

            for mod in mods:
                plugin_dir = args.output / f"mekong-core-{layer}"

                # Check if exists
                if plugin_dir.exists() and not args.force:
                    logger.warning("Plugin already exists: %s (use --force to overwrite)", plugin_dir)
                    continue

                try:
                    created = factory.create_plugin(mod, output_dir=plugin_dir)
                    created_dirs.append(created)
                except Exception as e:
                    logger.error("Failed to create plugin for %s: %s", mod.path, e)
                    import traceback
                    traceback.print_exc()

        # Summary
        print("\n" + "=" * 60)
        logger.info("Migration complete!")
        logger.info("Created %d plugin directories", len(created_dirs))
        for d in created_dirs[:10]:  # Show first 10
            print(f"  - {d}")
        if len(created_dirs) > 10:
            print(f"  ... and {len(created_dirs) - 10} more")

        # Next steps
        print("\nNext steps:")
        print("1. Review generated plugins in plugins/mekong-core-*/")
        print("2. Implement actual handler logic (handlers/*.py)")
        print("3. Update plugin.json with accurate command descriptions and arguments")
        print("4. Test: MEKONG_FEATURE_PLUGIN_SYSTEM_ENABLED=true mekong admin plugin scan")
        print("5. Enable plugins layer by layer via feature flags")
        print("\nSee docs/command-migration-timeline.md for full rollout plan")

        return 0

    except Exception as e:
        logger.error("Fatal error: %s", e)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
