"""
Registry API - Command resolution and lookup functions (Facade).
"""
from .mcp_catalog import mcp_catalog
from .metadata import list_subcommands, list_suites, get_agent_for_command, get_command_metadata
from .store import COMMAND_REGISTRY, SHORTCUTS


def print_command_map():
    """Visualizes the command hierarchy for the user."""
    print("\n" + "=" * 60)
    print("|" + "AGENCY OS - COMMAND REGISTRY".center(58) + "|")
    print("=" * 60)

    for suite_id in list_suites():
        s = COMMAND_REGISTRY[suite_id]
        print(f"\n  [{s['emoji']}] {suite_id.upper()} - {s['description']}")
        for sub in list_subcommands(suite_id):
            meta = s["subcommands"][sub]
            agent_tag = f"[{meta.get('agent', 'system')}]"
            print(f"     - {sub:<15} {agent_tag}")

    # Show MCP Tools if any
    if mcp_catalog.tools:
        print("\n  [🔌] MCP TOOLS - Dynamically loaded from servers")
        for server, tools in mcp_catalog.tools.items():
            print(f"     - Server: {server}")
            for tool in tools[:5]: # Show first 5
                print(f"       * {tool['name']}")
            if len(tools) > 5:
                print(f"       * ... and {len(tools)-5} more")

    print("\n" + "-" * 60)
    print("  Try using shortcuts: " + ", ".join(list(SHORTCUTS.keys())[:8]) + "...")
    print("=" * 60 + "\n")
