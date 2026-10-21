# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Generation and template helpers for Docs command."""

import sys

import typer


def _facade():
    return sys.modules["src.commands.docs"]


SIMPLE_HTML_CONTENT = """
<!DOCTYPE html>
<html>
<head>
    <title>Project Documentation</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1, h2 { color: #2c3e50; }
        .toc { background-color: #f8f9fa; padding: 20px; margin: 20px 0; }
        .section { margin: 30px 0; }
    </style>
</head>
<body>
    <h1>Project Documentation</h1>
    <div class="toc">
        <h2>Table of Contents</h2>
        <ul>
            <li><a href="#intro">Introduction</a></li>
            <li><a href="#installation">Installation</a></li>
            <li><a href="#usage">Usage</a></li>
            <li><a href="#api">API Reference</a></li>
        </ul>
    </div>
    <div class="section"><h2 id="intro">Introduction</h2><p>Your project documentation goes here.</p></div>
    <div class="section"><h2 id="installation">Installation</h2><p>Instructions for installing your project.</p></div>
    <div class="section"><h2 id="usage">Usage</h2><p>Instructions for using your project.</p></div>
    <div class="section"><h2 id="api">API Reference</h2><p>API documentation for your project.</p></div>
</body>
</html>
"""

TEMPLATES = {
    "api": (
        "api-reference.md",
        "# API Reference\n\n## Base URL\n`https://api.yourapp.com/v1`\n\n"
        "## Authentication\nAll API requests require an API key in the `Authorization` header:\n\n"
        "```\nAuthorization: Bearer YOUR_API_KEY\n```\n\n"
        "## Endpoints\n\n### GET /endpoint\nDescription of the endpoint\n\n"
        "#### Parameters\n- param1 (required): Description\n- param2 (optional): Description\n\n"
        '#### Response\n```json\n{\n  "status": "success",\n  "data": {}\n}\n```\n',
    ),
    "tutorial": (
        "tutorial-template.md",
        "# Tutorial: [Tutorial Name]\n\n## Prerequisites\n- Prerequisite 1\n- Prerequisite 2\n\n"
        "## Step 1: [Step Title]\nDescription of the first step.\n\n"
        "```bash\n# Example command\ncommand here\n```\n\n"
        "## Step 2: [Step Title]\nDescription of the second step.\n\n"
        "## Conclusion\nSummary of what was covered.\n",
    ),
    "guide": (
        "guide-template.md",
        "# Guide: [Guide Topic]\n\n## Overview\nBrief overview of the guide topic.\n\n"
        "## When to Use This Guide\n- Situation 1\n- Situation 2\n\n"
        "## How to Use This Guide\nDetailed instructions.\n\n"
        "## Examples\nPractical examples.\n\n"
        "## Best Practices\n- Best practice 1\n- Best practice 2\n\n"
        "## Troubleshooting\nCommon issues and solutions.\n",
    ),
    "changelog": (
        "CHANGELOG-template.md",
        "# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n"
        "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),\n"
        "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).\n\n"
        "## [Unreleased]\n\n### Added\n- New features\n\n### Changed\n- Changes to existing functionality\n\n"
        "### Deprecated\n- Soon-to-be removed features\n\n### Removed\n- Removed features\n\n"
        "### Fixed\n- Bug fixes\n\n### Security\n- Security improvements\n",
    ),
}


def generate_simple_docs(format_type: str, source: str, output: str):
    """Generate simple documentation for different formats"""
    f = _facade()
    output_path = f.Path(output)
    output_path.mkdir(parents=True, exist_ok=True)

    if format_type == "html":
        with open(output_path / "index.html", "w") as fh:
            fh.write(SIMPLE_HTML_CONTENT)
        f.console.print(f"[green]✅ Simple HTML documentation generated at {output_path / 'index.html'}[/green]")
    elif format_type == "md":
        md_content = (
            "# Project Documentation\n\n## Introduction\n\nYour project introduction goes here.\n\n"
            "## Installation\n\nInstructions for installing your project.\n\n"
            "## Usage\n\nInstructions for using your project.\n\n"
            "## API Reference\n\nAPI documentation for your project.\n\n"
            "## Contributing\n\nGuidelines for contributing to your project.\n\n"
            "## License\n\nYour project license information.\n"
        )
        with open(output_path / "README.md", "w") as fh:
            fh.write(md_content)
        f.console.print(f"[green]✅ Markdown documentation generated at {output_path / 'README.md'}[/green]")
    else:
        f.console.print(f"[yellow]⚠️  Format {format_type} not supported in simple mode. Use Sphinx for advanced formats.[/yellow]")


def template(
    type_name: str = typer.Argument(..., help="Template type: api, tutorial, guide, changelog"),
    output: str = typer.Option("./docs", "--output", "-o", help="Output directory"),
):
    """Generate documentation templates"""
    f = _facade()
    f.console.print(f"[bold]📄 Generating {type_name} documentation template...[/bold]")

    output_path = f.Path(output)
    output_path.mkdir(parents=True, exist_ok=True)

    if type_name not in TEMPLATES:
        f.console.print(f"[red]❌ Unknown template type: {type_name}[/red]")
        f.console.print("[dim]Available types: api, tutorial, guide, changelog[/dim]")
        return

    filename, template_content = TEMPLATES[type_name]
    template_path = output_path / filename
    with open(template_path, "w") as fh:
        fh.write(template_content)

    f.console.print(f"[green]✅ {type_name.capitalize()} template created at {template_path}[/green]")
