# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Health check and log monitoring helpers for Monitor command."""

import shutil
import subprocess
import sys
from typing import Optional
import urllib.error
import urllib.request

from rich.panel import Panel
import typer


def _facade():
    return sys.modules["src.commands.monitor"]


def check_web_health(base_url: str, port: int, timeout: int) -> tuple[str, str]:
    """Check if web server is responding"""
    f = _facade()
    try:
        url = f"{base_url}:{port}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mekong CLI Monitor"})
        start_time = f.time.time()
        response = urllib.request.urlopen(req, timeout=timeout)
        response_time = f.time.time() - start_time

        if response.getcode() < 400:
            return ("✅ Healthy", f"Response: {response.getcode()}, Time: {response_time:.2f}s")
        else:
            return ("❌ Unhealthy", f"Response: {response.getcode()}")
    except Exception as e:
        return ("❌ Unhealthy", f"Error: {str(e)}")


def check_endpoint(url: str, timeout: int) -> tuple[str, str]:
    """Check a specific endpoint"""
    f = _facade()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mekong CLI Monitor"})
        start_time = f.time.time()
        response = urllib.request.urlopen(req, timeout=timeout)
        response_time = f.time.time() - start_time

        if response.getcode() < 400:
            return ("✅ Healthy", f"Response: {response.getcode()}, Time: {response_time:.2f}s")
        else:
            return ("❌ Unhealthy", f"Response: {response.getcode()}")
    except Exception as e:
        return ("❌ Unhealthy", f"Error: {str(e)}")


def is_command_available(command: str) -> bool:
    """Check if a command is available in PATH"""
    return shutil.which(command) is not None


def tail_log(log_file: str, lines: int, follow: bool, filter_pattern: Optional[str] = None) -> None:
    """Display log file contents"""
    f = _facade()
    try:
        cmd = ["tail", "-n", str(lines)]
        if follow:
            cmd.append("-f")
        cmd.append(log_file)

        if filter_pattern:
            tail_process = f.subprocess.Popen(cmd[:-1], stdout=subprocess.PIPE, text=True)
            grep_cmd = ["grep", filter_pattern]
            if follow:
                grep_cmd.append("--line-buffered")

            result = f.subprocess.run(grep_cmd, stdin=tail_process.stdout, capture_output=True, text=True)
            output = result.stdout
        else:
            result = f.subprocess.run(cmd, capture_output=True, text=True)
            output = result.stdout

        if output:
            panel_title = f"Log: {log_file}"
            if filter_pattern:
                panel_title += f" (filtered: {filter_pattern})"
            if follow:
                panel_title += " - LIVE"

            f.console.print(Panel(output, title=panel_title))
        else:
            f.console.print(f"[dim]No recent log entries in {log_file}[/dim]")

    except subprocess.CalledProcessError as e:
        f.console.print(f"[red]❌ Error reading log: {e}[/red]")
    except FileNotFoundError:
        f.console.print("[red]❌ 'tail' command not found. Please install coreutils.[/red]")


def logs(
    service: str = typer.Argument(..., help="Service to monitor: app, nginx, apache, docker, custom"),
    lines: int = typer.Option(50, "--lines", "-n", help="Number of lines to show"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
    filter_pattern: str = typer.Option(None, "--filter", "-F", help="Filter logs by pattern"),
):
    """Monitor application logs"""
    f = _facade()
    f.console.print(f"[bold]📝 Monitoring logs for {service} (last {lines} lines)...[/bold]")

    if service == "app":
        log_locations = ["logs/app.log", "log/app.log", "/var/log/app.log", "app.log", "main.log"]
        log_file = next((loc for loc in log_locations if f.Path(loc).exists()), None)

        if not log_file:
            f.console.print("[yellow]⚠️  App log file not found in common locations[/yellow]")
            f.console.print("[dim]Expected locations: logs/app.log, log/app.log, /var/log/app.log, app.log[/dim]")
            return

        f.tail_log(log_file, lines, follow, filter_pattern)

    elif service == "nginx":
        log_file = "/var/log/nginx/access.log" if f.Path("/var/log/nginx/access.log").exists() else "/var/log/nginx/error.log"
        if f.Path(log_file).exists():
            f.tail_log(log_file, lines, follow, filter_pattern)
        else:
            f.console.print(f"[red]❌ Nginx log file not found: {log_file}[/red]")

    elif service == "apache":
        log_file = "/var/log/apache2/access.log" if f.Path("/var/log/apache2/access.log").exists() else "/var/log/apache2/error.log"
        if f.Path(log_file).exists():
            f.tail_log(log_file, lines, follow, filter_pattern)
        else:
            f.console.print(f"[red]❌ Apache log file not found: {log_file}[/red]")

    elif service == "docker":
        if not f.is_command_available("docker"):
            f.console.print("[red]❌ Docker not found[/red]")
            return

        container_name = f.os.environ.get("DOCKER_CONTAINER_NAME", "current")
        cmd = ["docker", "logs", "--tail", str(lines)]
        if follow:
            cmd.append("-f")
        cmd.append(container_name)

        try:
            result = f.subprocess.run(cmd, capture_output=True, text=True, check=True)
            f.console.print(Panel(result.stdout, title=f"Docker Logs ({container_name})"))
        except subprocess.CalledProcessError as e:
            f.console.print(f"[red]❌ Error getting Docker logs: {e.stderr}[/red]")

    elif service == "custom":
        custom_log_path = f.os.environ.get("CUSTOM_LOG_PATH", "./custom.log")
        if f.Path(custom_log_path).exists():
            f.tail_log(custom_log_path, lines, follow, filter_pattern)
        else:
            f.console.print(f"[red]❌ Custom log file not found: {custom_log_path}[/red]")
            f.console.print("[dim]Set CUSTOM_LOG_PATH environment variable to specify log location[/dim]")
    else:
        f.console.print(f"[red]❌ Unknown service: {service}[/red]")
        f.console.print("[dim]Supported services: app, nginx, apache, docker, custom[/dim]")
