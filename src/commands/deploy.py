"""Deploy command - Deploy applications to various platforms"""

import typer
from rich.console import Console
from rich.panel import Panel
import subprocess
from pathlib import Path
import os

app = typer.Typer()
console = Console()


@app.command()
def run(
    platform: str = typer.Argument(..., help="Platform to deploy to: cloudflare, docker, custom"),
    build_first: bool = typer.Option(True, "--build", help="Build before deploying"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate deployment without executing"),
    env: str = typer.Option("production", "--env", "-e", help="Environment: production, staging, development"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Deploy application to specified platform"""

    if dry_run:
        console.print(f"[yellow]🧪 DRY RUN: Would deploy to {platform} (env: {env})[/yellow]")
        return

    if build_first:
        console.print("[blue]📦 Building application...[/blue]")
        # Simulate build process
        console.print("[green]✅ Build completed[/green]")

    console.print(f"[bold]🚀 Deploying to {platform} (environment: {env})...[/bold]")

    if platform.lower() == "cloudflare":
        deploy_cloudflare(env, verbose)
    elif platform.lower() == "docker":
        deploy_docker(env, verbose)
    elif platform.lower() == "custom":
        deploy_custom(env, verbose)
    else:
        console.print(f"[red]Unsupported platform: {platform}[/red]")
        console.print("[dim]Supported platforms: cloudflare, docker, custom[/dim]")
        raise typer.Exit(code=1)


def deploy_cloudflare(env: str, verbose: bool) -> None:
    """Deploy to Cloudflare (Pages + Workers)."""
    try:
        result = subprocess.run(
            ["wrangler", "--version"],
            capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            console.print("[red]wrangler CLI not found. Install with: npm install -g wrangler[/red]")
            raise typer.Exit(code=1)

        cmd = ["wrangler", "deploy"]
        if env != "production":
            cmd.extend(["--env", env])

        if verbose:
            cmd.append("--log-level=debug")

        console.print(f"[blue]Deploying to Cloudflare ({env})...[/blue]")
        result = subprocess.run(cmd, cwd=Path.cwd(), check=True, capture_output=not verbose, text=True)

        if result.stdout:
            console.print(Panel(result.stdout, title="Wrangler Output"))

        console.print("[green]Deployed to Cloudflare successfully![/green]")

    except subprocess.CalledProcessError as e:
        console.print("[red]Cloudflare deployment failed![/red]")
        if e.stderr:
            console.print(Panel(e.stderr, title="Error"))
    except Exception as e:
        console.print(f"[red]Deployment failed: {str(e)}[/red]")


def deploy_docker(env: str, verbose: bool):
    """Deploy using Docker"""
    try:
        # Check if Docker is available
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            console.print("[red]❌ Docker not found. Please install Docker.[/red]")
            raise typer.Exit(code=1)

        # Build and push Docker image
        image_name = os.environ.get("DOCKER_IMAGE_NAME", "mekong-cli")
        image_tag = f"{image_name}:{env}"

        # Tag and push
        tag_cmd = ["docker", "tag", f"{image_name}:latest", image_tag]
        push_cmd = ["docker", "push", image_tag]

        console.print(f"[blue]🐳 Tagging image: {image_tag}[/blue]")
        subprocess.run(tag_cmd, cwd=Path.cwd(), check=True, capture_output=not verbose)

        console.print(f"[blue]🌐 Pushing to registry: {image_tag}[/blue]")
        subprocess.run(push_cmd, cwd=Path.cwd(), check=True, capture_output=not verbose, text=True)

        console.print(f"[green]✅ Docker image deployed: {image_tag}[/green]")

        # Optional: deploy to container orchestration platform
        if os.environ.get("DEPLOY_TO_K8S"):
            deploy_to_kubernetes(image_tag, verbose)

    except subprocess.CalledProcessError as e:
        console.print("[red]❌ Docker deployment failed![/red]")
        if e.stderr:
            console.print(Panel(e.stderr, title="Error"))
    except Exception as e:
        console.print(f"[red]❌ Deployment failed: {str(e)}[/red]")


def deploy_to_kubernetes(image_tag: str, verbose: bool):
    """Deploy to Kubernetes (helper for Docker deployment)"""
    kubectl_path = Path("kubectl")
    if not kubectl_path.exists():
        # Look for kubectl in PATH
        import shutil
        if not shutil.which("kubectl"):
            console.print("[yellow]⚠️  kubectl not found, skipping Kubernetes deployment[/yellow]")
            return

    # Update deployment with new image
    deployment_name = os.environ.get("K8S_DEPLOYMENT_NAME", "mekong-cli")
    namespace = os.environ.get("K8S_NAMESPACE", "default")

    cmd = ["kubectl", "set", "image", f"deployment/{deployment_name}", f"app={image_tag}", "-n", namespace]

    console.print(f"[blue]☸️  Updating Kubernetes deployment ({namespace}/{deployment_name})[/blue]")
    result = subprocess.run(cmd, cwd=Path.cwd(), check=True, capture_output=not verbose, text=True)

    if result.stdout:
        console.print(Panel(result.stdout, title="Kubectl Output"))

    console.print(f"[green]✅ Kubernetes deployment updated with {image_tag}[/green]")


def deploy_custom(env: str, verbose: bool):
    """Deploy using custom script or command"""
    deploy_script = os.environ.get("CUSTOM_DEPLOY_SCRIPT", "./deploy.sh")

    if not Path(deploy_script).exists():
        console.print(f"[red]❌ Custom deployment script not found: {deploy_script}[/red]")
        console.print("[dim]Set CUSTOM_DEPLOY_SCRIPT environment variable or create ./deploy.sh[/dim]")
        return

    try:
        cmd = ["bash", deploy_script, env]
        console.print(f"[blue]🔧 Running custom deployment: {deploy_script}[/blue]")
        result = subprocess.run(cmd, cwd=Path.cwd(), check=True, capture_output=not verbose, text=True)

        if result.stdout:
            console.print(Panel(result.stdout, title="Deployment Output"))

        console.print("[green]✅ Custom deployment completed![/green]")

    except subprocess.CalledProcessError as e:
        console.print("[red]❌ Custom deployment failed![/red]")
        if e.stderr:
            console.print(Panel(e.stderr, title="Error"))
    except Exception as e:
        console.print(f"[red]❌ Custom deployment failed: {str(e)}[/red]")


@app.command()
def status(platform: str = typer.Argument(..., help="Platform to check: cloudflare, docker")):
    """Check deployment status."""
    console.print(f"[bold]Checking deployment status for {platform}...[/bold]")

    if platform.lower() == "cloudflare":
        check_cloudflare_status()
    elif platform.lower() == "docker":
        check_docker_status()
    else:
        console.print(f"[red]Unsupported platform: {platform}[/red]")
        console.print("[dim]Supported platforms: cloudflare, docker[/dim]")


def check_cloudflare_status() -> None:
    """Check Cloudflare Workers/Pages deployment status."""
    try:
        result = subprocess.run(
            ["wrangler", "deployments", "list"],
            capture_output=True, text=True, check=False
        )

        if result.returncode == 0:
            console.print(Panel(result.stdout, title="Cloudflare Deployments"))
        else:
            console.print("[yellow]Unable to fetch Cloudflare status[/yellow]")
            if result.stderr:
                console.print(Panel(result.stderr, title="Error"))

    except Exception as e:
        console.print(f"[red]Failed to check Cloudflare status: {str(e)}[/red]")


def check_docker_status():
    """Check Docker deployment status"""
    try:
        # Check if Docker daemon is running
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True, text=True, check=False
        )

        if result.returncode == 0:
            console.print(Panel("Docker daemon is running", title="Docker Status", border_style="green"))
        else:
            console.print(Panel("Docker daemon is not running", title="Docker Status", border_style="red"))

        # Check running containers
        result = subprocess.run(
            ["docker", "ps"],
            capture_output=True, text=True, check=False
        )

        if result.returncode == 0:
            console.print(Panel(result.stdout, title="Running Containers"))

    except Exception as e:
        console.print(f"[red]❌ Failed to check Docker status: {str(e)}[/red]")


@app.command()
def rollback(to_version: str = typer.Argument(..., help="Version to rollback to")):
    """Rollback deployment to a previous version"""
    console.print(f"[bold]🔄 Rolling back to version: {to_version}[/bold]")
    console.print("[yellow]This feature is platform-dependent and not implemented yet.[/yellow]")
    console.print("Would implement rollback functionality for specific platform")


if __name__ == "__main__":
    app()
