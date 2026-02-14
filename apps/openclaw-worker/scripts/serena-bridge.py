#!/usr/bin/env python3
"""
🦞 Serena Bridge for OpenClaw (The Semantic Eye)
Wraps Serena's LSP tools into a simple CLI for the OpenClaw Bridge Server.

Usage:
  python3 scripts/serena-bridge.py <tool_name> --args '<json_args>'
  python3 scripts/serena-bridge.py find_symbol --name "Order" --file "src/types.ts"

Tools Supported:
- get_overview
- find_symbol
- find_refs
- replace_body
- insert_after
- insert_before
- rename
"""

import sys
import json
import argparse
import os
from pathlib import Path
from typing import Any, Dict

# Ensure we can import serena
# Implementation Note: We assume this script runs in an environment where 'serena' is installed.
try:
    from serena.agent import SerenaAgent, SerenaConfig
    from serena.tools import (
        GetSymbolsOverviewTool,
        FindSymbolTool,
        FindReferencingSymbolsTool,
        ReplaceSymbolBodyTool,
        InsertAfterSymbolTool,
        InsertBeforeSymbolTool,
        RenameSymbolTool
    )
except ImportError as e:
    print(json.dumps({"error": f"Failed to import serena: {str(e)}", "guidance": "Run `uv pip install -e external/serena` first."}))
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Serena Bridge for OpenClaw")
    parser.add_argument("tool", help="Tool to execute (find_symbol, get_overview, etc.)")
    parser.add_argument("--args", help="JSON string of arguments for the tool", default="{}")
    parser.add_argument("--project", help="Path to project root (default: current dir)", default=".")
    
    # Specific args for ease of use (overrides JSON args if provided)
    parser.add_argument("--name", help="Symbol name/path")
    parser.add_argument("--file", help="Relative file path")
    parser.add_argument("--body", help="Content body for edits")
    
    args = parser.parse_args()

    # 1. Initialize Serena Agent
    # We use a minimal config suitable for CLI usage
    # Enable logging to stderr for debugging
    import logging
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    try:
        project_path = Path(args.project).resolve()
        config = SerenaConfig(
            log_level=20, # INFO
            web_dashboard=False,
            gui_log_window=False
        )
        agent = SerenaAgent(project=str(project_path), serena_config=config)
        
        # Sync: Wait for async initialization to complete
        # Serena's TaskExecutor runs sequentially, so scheduling a sync task waits for pending ones.
        logging.info("Waiting for Serena Agent initialization...")
        agent.execute_task(lambda: None, name="WaitForInit")
        logging.info("Agent initialized.")
    except Exception as e:
        print(json.dumps({"error": f"Failed to initialize SerenaAgent: {str(e)}"}))
        sys.exit(1)

    # 2. Prepare Tool Arguments
    tool_args: Dict[str, Any] = {}
    if args.args:
        try:
            tool_args = json.loads(args.args)
        except json.JSONDecodeError:
            print(json.dumps({"error": "Invalid JSON in --args"}))
            sys.exit(1)

    # Merge explicit flags
    if args.name:
        # Map generic 'name' to tool-specific arg (usually 'name_path_pattern' or 'name_path')
        if args.tool == "find_symbol":
            tool_args["name_path_pattern"] = args.name
        elif args.tool in ["find_refs", "replace_body", "insert_after", "insert_before", "rename"]:
            tool_args["name_path"] = args.name
            
    if args.file:
        tool_args["relative_path"] = args.file
        
    if args.body:
        tool_args["body"] = args.body

    # 3. Execute Tool
    result = None
    try:
        if args.tool == "get_overview":
            tool_inst = agent.get_tool(GetSymbolsOverviewTool)
            # Default Depth=1 if not set
            if "depth" not in tool_args:
                tool_args["depth"] = 1
            result = tool_inst.apply(**tool_args)

        elif args.tool == "find_symbol":
            tool_inst = agent.get_tool(FindSymbolTool)
            result = tool_inst.apply(**tool_args)

        elif args.tool == "find_refs":
            tool_inst = agent.get_tool(FindReferencingSymbolsTool)
            result = tool_inst.apply(**tool_args)

        elif args.tool == "replace_body":
            tool_inst = agent.get_tool(ReplaceSymbolBodyTool)
            result = tool_inst.apply(**tool_args)

        elif args.tool == "insert_after":
            tool_inst = agent.get_tool(InsertAfterSymbolTool)
            result = tool_inst.apply(**tool_args)

        elif args.tool == "insert_before":
            tool_inst = agent.get_tool(InsertBeforeSymbolTool)
            result = tool_inst.apply(**tool_args)
            
        elif args.tool == "rename":
            tool_inst = agent.get_tool(RenameSymbolTool)
            # Add 'new_name' handling? For now assume it's in --args JSON
            result = tool_inst.apply(**tool_args)

        else:
            print(json.dumps({"error": f"Unknown tool: {args.tool}"}))
            sys.exit(1)

        # 4. Output Result
        # API returns a string (often JSON string), we output it directly (or sanitized)
        # Check if result is already JSON string
        try:
            # Try parsing to ensure it's valid JSON, if so, dump it again to be sure
            parsed = json.loads(result)
            print(json.dumps({"status": "success", "data": parsed}))
        except:
            # If prompt/string, wrap it
            print(json.dumps({"status": "success", "data": result}))

    except Exception as e:
        print(json.dumps({"error": str(e), "type": type(e).__name__}))
        sys.exit(1)

if __name__ == "__main__":
    main()
