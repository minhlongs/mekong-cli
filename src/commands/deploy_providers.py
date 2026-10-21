# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Platform deployment and status check providers for Deploy command."""

import shutil
import subprocess
import sys

from rich.panel import Panel
import typer


def _facade():
    return sys.modules["src.commands.deploy"]


def deploy_cloudflare(env: str, verbose: bool) -> None:
    """Deploy to Cloudflare (Pages + Workers)."""
    f = _facade()
    env = f.validate_env(env)
    try:
        result = f.run_sanitized_process(
            ["wrangler", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            f.console.print("[red]wrangler CLI not found. Install with: npm install -g wrangler[/red]")
            raise typer.Exit(code=1)

        cmd = ["wrangler", "deploy"]
        if env != "production":
            cmd.extend(["--env", env])
        if verbose:
            cmd.append("--log-level=debug")

        f.console.print(f"[blue]Deploying to Cloudflare ({env})...[/blue]")
        result = f.run_sanitized_process(
            cmd,
            cwd=f.Path.cwd(),
            check=True,
            capture_output=not verbose,
            text=True,
        )

        if result.stdout:
            f.console.print(Panel(result.stdout, title="Wrangler Output"))
        f.console.print("[green]Deployed to Cloudflare successfully![/green]")

    except FileNotFoundError:
        f.console.print("[red]wrangler CLI not found. Install with: npm install -g wrangler[/red]")
        raise typer.Exit(code=1)
    except subprocess.CalledProcessError as e:
        f.console.print("[red]Cloudflare deployment failed![/red]")
        if e.stderr:
            f.console.print(Panel(e.stderr, title="Error"))
        raise typer.Exit(code=1)
    except typer.Exit:
        raise
    except Exception as e:
        f.console.print(f"[red]Deployment failed: {str(e)}[/red]")
        raise typer.Exit(code=1)


def deploy_docker(env: str, verbose: bool):
    """Deploy using Docker"""
    f = _facade()
    env = f.validate_env(env)
    try:
        result = f.run_sanitized_process(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            f.console.print("[red]❌ Docker not found. Please install Docker.[/red]")
            raise typer.Exit(code=1)

        raw_image_name = f.os.environ.get("DOCKER_IMAGE_NAME", "mekong-cli")
        image_name = f.validate_identifier(raw_image_name, "Docker image name")
        image_tag = f"{image_name}:{env}"

        tag_cmd = ["docker", "tag", f"{image_name}:latest", image_tag]
        push_cmd = ["docker", "push", image_tag]

        f.console.print(f"[blue]🐳 Tagging image: {image_tag}[/blue]")
        f.run_sanitized_process(tag_cmd, cwd=f.Path.cwd(), check=True, capture_output=not verbose)

        f.console.print(f"[blue]🌐 Pushing to registry: {image_tag}[/blue]")
        f.run_sanitized_process(push_cmd, cwd=f.Path.cwd(), check=True, capture_output=not verbose, text=True)

        f.console.print(f"[green]✅ Docker image deployed: {image_tag}[/green]")

        if f.os.environ.get("DEPLOY_TO_K8S"):
            f.deploy_to_kubernetes(image_tag, verbose)

    except FileNotFoundError:
        f.console.print("[red]❌ Docker not found. Please install Docker.[/red]")
        raise typer.Exit(code=1)
    except subprocess.CalledProcessError as e:
        f.console.print("[red]❌ Docker deployment failed![/red]")
        if e.stderr:
            f.console.print(Panel(e.stderr, title="Error"))
        raise typer.Exit(code=1)
    except typer.Exit:
        raise
    except Exception as e:
        f.console.print(f"[red]❌ Deployment failed: {str(e)}[/red]")
        raise typer.Exit(code=1)


def deploy_to_kubernetes(image_tag: str, verbose: bool):
    """Deploy to Kubernetes (helper for Docker deployment)"""
    f = _facade()
    kubectl_path = f.Path("kubectl")
    if not kubectl_path.exists() and not shutil.which("kubectl"):
        f.console.print("[yellow]⚠️  kubectl not found, skipping Kubernetes deployment[/yellow]")
        return

    raw_deployment = f.os.environ.get("K8S_DEPLOYMENT_NAME", "mekong-cli")
    raw_namespace = f.os.environ.get("K8S_NAMESPACE", "default")
    deployment_name = f.validate_identifier(raw_deployment, "Kubernetes deployment name")
    namespace = f.validate_identifier(raw_namespace, "Kubernetes namespace")

    cmd = ["kubectl", "set", "image", f"deployment/{deployment_name}", f"app={image_tag}", "-n", namespace]

    f.console.print(f"[blue]☸️  Updating Kubernetes deployment ({namespace}/{deployment_name})[/blue]")
    result = f.run_sanitized_process(cmd, cwd=f.Path.cwd(), check=True, capture_output=not verbose, text=True)

    if result.stdout:
        f.console.print(Panel(result.stdout, title="Kubectl Output"))
    f.console.print(f"[green]✅ Kubernetes deployment updated with {image_tag}[/green]")


def deploy_custom(env: str, verbose: bool):
    """Deploy using custom script or command"""
    f = _facade()
    env = f.validate_env(env)
    raw_script = f.os.environ.get("CUSTOM_DEPLOY_SCRIPT", "./deploy.sh")
    script_path = f.validate_script_path(raw_script)

    try:
        cmd = ["bash", "--", str(script_path), env]
        f.console.print(f"[blue]🔧 Running custom deployment: {script_path}[/blue]")
        result = f.run_sanitized_process(cmd, cwd=f.Path.cwd(), check=True, capture_output=not verbose, text=True)

        if result.stdout:
            f.console.print(Panel(result.stdout, title="Deployment Output"))
        f.console.print("[green]✅ Custom deployment completed![/green]")

    except subprocess.CalledProcessError as e:
        f.console.print("[red]❌ Custom deployment failed![/red]")
        if e.stderr:
            f.console.print(Panel(e.stderr, title="Error"))
        raise typer.Exit(code=1)
    except typer.Exit:
        raise
    except Exception as e:
        f.console.print(f"[red]❌ Custom deployment failed: {str(e)}[/red]")
        raise typer.Exit(code=1)
