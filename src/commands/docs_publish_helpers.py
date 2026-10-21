# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Publishing helpers for Docs command."""

import shutil
import subprocess
import sys

from rich.panel import Panel
import typer


def _facade():
    return sys.modules["src.commands.docs"]


def publish(
    platform: str = typer.Argument(..., help="Platform to publish to: github-pages, netlify, custom"),
    source: str = typer.Option("./docs/_build/html", "--source", "-s", help="Source directory to publish"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Publish documentation to various platforms"""
    f = _facade()
    f.console.print(f"[bold]🚀 Publishing documentation to {platform}...[/bold]")

    if platform == "github-pages":
        f.publish_to_github_pages(source, verbose)
    elif platform == "netlify":
        f.publish_to_netlify(source, verbose)
    elif platform == "custom":
        f.publish_to_custom(source, verbose)
    else:
        f.console.print(f"[red]❌ Unsupported platform: {platform}[/red]")
        f.console.print("[dim]Supported platforms: github-pages, netlify, custom[/dim]")


def publish_to_github_pages(source: str, verbose: bool):
    """Publish documentation to GitHub Pages"""
    f = _facade()
    if not f.Path(".git").exists():
        f.console.print("[red]❌ Not in a git repository[/red]")
        return

    try:
        f.subprocess.run(["git", "checkout", "gh-pages"], check=False, capture_output=not verbose)

        result = f.subprocess.run(
            ["git", "show-ref", "--verify", "--quiet", "refs/heads/gh-pages"],
            capture_output=True,
        )
        if result.returncode != 0:
            f.subprocess.run(
                ["git", "checkout", "--orphan", "gh-pages"],
                check=True,
                capture_output=not verbose,
            )

        for item in f.Path(".").iterdir():
            if item.name != ".git":
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()

        source_path = f.Path(source)
        if source_path.exists():
            for item in source_path.rglob("*"):
                if item.is_file():
                    dest_path = f.Path(".") / item.relative_to(source_path)
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, dest_path)

        f.subprocess.run(["git", "add", "."], check=True, capture_output=not verbose)
        f.subprocess.run(["git", "commit", "-m", "Update documentation"], check=True, capture_output=not verbose)
        f.subprocess.run(["git", "push", "origin", "gh-pages"], check=True, capture_output=not verbose)

        f.console.print("[green]✅ Documentation published to GitHub Pages![/green]")
        f.console.print("[dim]Visit: https://<username>.github.io/<repository>[/dim]")

        f.subprocess.run(["git", "checkout", "-"], check=False, capture_output=not verbose)

    except subprocess.CalledProcessError as e:
        f.console.print("[red]❌ GitHub Pages publishing failed![/red]")
        if e.stderr:
            f.console.print(Panel(e.stderr, title="Error"))
    except Exception as e:
        f.console.print(f"[red]❌ Error during GitHub Pages publishing: {str(e)}[/red]")


def publish_to_netlify(source: str, verbose: bool):
    """Publish documentation to Netlify"""
    f = _facade()
    try:
        result = f.subprocess.run(["netlify", "--version"], capture_output=True, text=True, check=False)
        if result.returncode != 0:
            f.console.print("[red]❌ Netlify CLI not found. Install with: npm install -g netlify-cli[/red]")
            return

        cmd = ["netlify", "deploy", "--dir", source]
        if verbose:
            cmd.append("--verbose")

        result = f.subprocess.run(cmd, check=True, capture_output=not verbose, text=True)

        f.console.print("[green]✅ Documentation published to Netlify![/green]")
        if result.stdout:
            f.console.print(Panel(result.stdout, title="Netlify Response"))

    except subprocess.CalledProcessError as e:
        f.console.print("[red]❌ Netlify publishing failed![/red]")
        if e.stderr:
            f.console.print(Panel(e.stderr, title="Error"))
    except Exception as e:
        f.console.print(f"[red]❌ Error during Netlify publishing: {str(e)}[/red]")


def publish_to_custom(source: str, verbose: bool):
    """Publish documentation using custom method"""
    f = _facade()
    custom_publish_script = f.os.environ.get("CUSTOM_DOCS_PUBLISH_SCRIPT", "./publish-docs.sh")

    if not f.Path(custom_publish_script).exists():
        f.console.print(f"[red]❌ Custom publish script not found: {custom_publish_script}[/red]")
        f.console.print("[dim]Set CUSTOM_DOCS_PUBLISH_SCRIPT env var or create ./publish-docs.sh[/dim]")
        return

    try:
        cmd = ["bash", custom_publish_script, source]
        result = f.subprocess.run(cmd, check=True, capture_output=not verbose, text=True)

        f.console.print("[green]✅ Documentation published using custom method![/green]")
        if result.stdout:
            f.console.print(Panel(result.stdout, title="Publish Script Output"))

    except subprocess.CalledProcessError as e:
        f.console.print("[red]❌ Custom publishing failed![/red]")
        if e.stderr:
            f.console.print(Panel(e.stderr, title="Error"))
    except Exception as e:
        f.console.print(f"[red]❌ Error during custom publishing: {str(e)}[/red]")
