# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Docs command - Generate, serve, and manage documentation"""

import os
from pathlib import Path
import re
import subprocess
import webbrowser

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import typer

from src.commands.docs_publish_helpers import (
    publish, publish_to_custom, publish_to_github_pages, publish_to_netlify,
)
from src.commands.docs_template_helpers import generate_simple_docs, template

app = typer.Typer()
console = Console()


@app.command()
def generate(
    format_type: str = typer.Option("html", "--format", "-f", help="Output format: html, pdf, epub, md"),
    source: str = typer.Option("./", "--source", "-s", help="Source directory containing docs"),
    output: str = typer.Option("./docs/_build", "--output", "-o", help="Output directory"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Generate documentation from source files"""
    console.print(f"[bold]📚 Generating {format_type.upper()} documentation...[/bold]")
    try:
        if Path("conf.py").exists() or Path("source/conf.py").exists():
            cmd = ["sphinx-build", "-b", format_type, source, output] + (["-v"] if verbose else [])
            console.print(f"[dim]Running: {' '.join(cmd)}[/dim]")
            result = subprocess.run(cmd, check=True, capture_output=not verbose, text=True)
            if result.returncode == 0:
                console.print(f"[green]✅ {format_type.upper()} documentation generated at {output}[/green]")
            else:
                console.print("[red]❌ Documentation generation failed[/red]")
                if result.stderr:
                    console.print(Panel(result.stderr, title="Error"))
        else:
            generate_simple_docs(format_type, source, output)
    except FileNotFoundError:
        console.print("[yellow]⚠️  Sphinx not found, generating simple documentation[/yellow]")
        generate_simple_docs(format_type, source, output)
    except subprocess.CalledProcessError as e:
        console.print("[red]❌ Documentation generation failed![/red]")
        if e.stderr:
            console.print(Panel(e.stderr, title="Error"))


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", "-H", help="Host to serve on"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to serve on"),
    open_browser: bool = typer.Option(True, "--open", "-o", help="Open browser automatically"),
):
    """Serve documentation locally"""
    docs_path = Path("./docs/_build/html") if Path("./docs/_build/html").exists() else Path("./docs")
    if not docs_path.exists():
        console.print("[red]❌ Documentation directory not found. Generate docs first.[/red]")
        return

    console.print(f"[bold]🌐 Serving documentation at http://{host}:{port}[/bold]")
    try:
        import http.server
        import socketserver

        os.chdir(docs_path)

        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=".", **kwargs)

        with socketserver.TCPServer((host, port), Handler) as httpd:
            console.print(f"[green]✅ Documentation server started at http://{host}:{port}[/green]")
            console.print("[dim]Press Ctrl+C to stop the server[/dim]")
            if open_browser:
                webbrowser.open(f"http://{host}:{port}")
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                console.print("\n[yellow]⚠️  Server stopped by user[/yellow]")
    except ImportError:
        console.print("[red]❌ Failed to start documentation server[/red]")
        console.print("[dim]Try installing a simple HTTP server: python -m http.server {port}[/dim]")


@app.command()
def check_links():
    """Check for broken links in documentation"""
    console.print("[bold]🔗 Checking for broken links in documentation...[/bold]")
    all_docs = [
        p for d in (Path("./docs"), Path("./doc"), Path("./documentation")) if d.exists()
        for ext in ("**/*.md", "**/*.html", "**/*.rst") for p in d.glob(ext)
    ]
    if not all_docs:
        console.print("[yellow]⚠️  No documentation files found[/yellow]")
        return

    broken_links, total_links = [], 0
    for doc_file in all_docs:
        content = doc_file.read_text(encoding="utf-8", errors="ignore")
        for pattern in (r"\[.*?\]\((.*?)\)", r'href="(.*?)"', r'src="(.*?)"'):
            for match in re.findall(pattern, content):
                total_links += 1
                if not match.startswith(("http://", "https://", "#")) and not (doc_file.parent / match).exists():
                    broken_links.append((doc_file.name, match))

    if broken_links:
        console.print(f"[red]❌ Found {len(broken_links)} broken links out of {total_links} total links[/red]")
        table = Table(title="Broken Links")
        table.add_column("Document", style="cyan")
        table.add_column("Link", style="red")
        for doc, link in broken_links[:10]:
            table.add_row(doc, link)
        console.print(table)
        if len(broken_links) > 10:
            console.print(f"[dim]... and {len(broken_links) - 10} more[/dim]")
    else:
        console.print(f"[green]✅ All {total_links} links are valid[/green]")


@app.command()
def validate():
    """Validate documentation structure and content"""
    console.print("[bold]🔍 Validating documentation...[/bold]")
    common_docs = ["README.md", "CONTRIBUTING.md", "LICENSE", "CHANGELOG.md", "docs/index.md", "docs/README.md", "doc/README.md"]
    validation_results = [(doc, "✅" if Path(doc).exists() else "❌", "Exists" if Path(doc).exists() else "Missing") for doc in common_docs]

    api_docs = list(Path(".").glob("**/api*.md")) + list(Path(".").glob("**/API*.md"))
    validation_results.append(("API Documentation", "✅" if api_docs else "⚠️ ", f"Found {len(api_docs)} API docs" if api_docs else "No API docs found"))
    tutorial_docs = list(Path(".").glob("**/tutorial*.md")) + list(Path(".").glob("**/guide*.md"))
    validation_results.append(("Tutorials/Guides", "✅" if tutorial_docs else "⚠️ ", f"Found {len(tutorial_docs)} tutorials/guides" if tutorial_docs else "No tutorials/guides found"))

    table = Table(title="Documentation Validation")
    for col, st in [("Component", "cyan"), ("Status", "magenta"), ("Info", "dim")]:
        table.add_column(col, style=st)
    for item, status, info in validation_results:
        table.add_row(item, status, info)
    console.print(table)


app.command()(publish)
app.command()(template)

__all__ = [
    "app", "check_links", "console", "generate", "generate_simple_docs",
    "publish", "publish_to_custom", "publish_to_github_pages",
    "publish_to_netlify", "serve", "template", "validate",
]
