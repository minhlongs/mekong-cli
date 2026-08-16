# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - Social Daemon helpers.

Front-matter parser and CLI entry-point for social_daemon.py.
Kept separate to keep social_daemon.py under 200 lines.
"""

from __future__ import annotations

import argparse
from typing import Any


def parse_frontmatter(raw: str) -> tuple[str, list[str], str, dict[str, Any]]:
    """Extract YAML-ish front-matter from a markdown string.

    Supported keys inside ``---`` block:
        title:  Article title
        tags:   Comma-separated tag list
        gh_repo:        owner/repo for GitHub Discussions
        gh_category_id: GraphQL node ID of discussion category

    Example::

        ---
        title: My Post
        tags: python, ai
        gh_repo: owner/repo
        gh_category_id: DIC_kwXXXX
        ---
        Body content here...

    Returns:
        (title, tags, body, meta) — meta holds all remaining front-matter keys.
    """
    title = "Mekong CLI Update"
    tags: list[str] = []
    meta: dict[str, Any] = {}
    body = raw

    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            fm_block = parts[1].strip()
            body = parts[2].strip()
            for line in fm_block.splitlines():
                if ":" in line:
                    key, _, val = line.partition(":")
                    key = key.strip()
                    val = val.strip()
                    if key == "title":
                        title = val
                    elif key == "tags":
                        tags = [t.strip().strip("[]") for t in val.split(",") if t.strip()]
                    else:
                        meta[key] = val

    return title, tags, body, meta


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser for the social daemon."""
    parser = argparse.ArgumentParser(description="Mekong CLI Social Daemon")
    parser.add_argument(
        "--interval", type=int, default=60, help="Poll interval in minutes (default 60)"
    )
    parser.add_argument(
        "--publish", type=str, default="", help="Path to markdown file to publish now"
    )
    parser.add_argument(
        "--platforms",
        nargs="+",
        default=["devto", "github"],
        help="Platforms to publish to: discord devto github",
    )
    return parser


__all__ = ["parse_frontmatter", "build_arg_parser"]
