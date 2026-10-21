# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - ZX-Inspired Shell Executor."""

from __future__ import annotations

import logging
import os
import shlex
import subprocess
import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ProcessOutput:
    """Enhanced execution result inspired by zx's ProcessOutput."""

    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    command: str = ""
    duration_ms: float = 0.0

    @property
    def ok(self) -> bool:
        return self.exit_code == 0

    @property
    def failed(self) -> bool:
        return self.exit_code != 0

    @property
    def lines(self) -> list[str]:
        text = self.stdout.rstrip("\n")
        return text.split("\n") if text else []

    def __str__(self) -> str:
        return self.stdout.strip()

    def __bool__(self) -> bool:
        return self.ok


def quote(arg: str) -> str:
    """Shell-safe quoting for a single argument."""
    return shlex.quote(arg)


@contextmanager
def cd(directory: str) -> Generator[str, None, None]:
    """Context manager that changes working directory and restores on exit."""
    target = Path(directory).resolve()
    if not target.is_dir():
        raise FileNotFoundError(f"Directory not found: {directory}")
    previous = os.getcwd()
    try:
        os.chdir(target)
        yield str(target)
    finally:
        os.chdir(previous)


@contextmanager
def within() -> Generator[None, None, None]:
    """Context manager preserving current directory across operations."""
    saved = os.getcwd()
    try:
        yield
    finally:
        os.chdir(saved)


def shell(
    command: str,
    cwd: str | None = None,
    timeout: int = 120,
    env: dict | None = None,
    quiet: bool = False,
    nothrow: bool = False,
) -> ProcessOutput:
    """Execute a shell command with enhanced safety and output handling."""
    merged_env = {**os.environ, **env} if env else None
    start = time.monotonic()
    try:
        proc = subprocess.run(
            shlex.split(command), cwd=cwd, capture_output=True, text=True, timeout=timeout, env=merged_env,
        )
        duration = (time.monotonic() - start) * 1000
        output = ProcessOutput(
            stdout=proc.stdout or "", stderr=proc.stderr or "",
            exit_code=proc.returncode, command=command, duration_ms=duration,
        )
        if output.failed and not nothrow:
            err_detail = "" if quiet else f": {output.stderr.strip()[:200]}"
            raise RuntimeError(f"Command failed (exit {output.exit_code}){err_detail}")
        return output
    except subprocess.TimeoutExpired:
        duration = (time.monotonic() - start) * 1000
        if nothrow:
            return ProcessOutput(
                stdout="", stderr=f"Timed out after {timeout}s",
                exit_code=124, command=command, duration_ms=duration,
            )
        raise


def retry(
    count: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    on_retry: Callable[[int, Exception], None] | None = None,
) -> Callable:
    """Decorator for retrying functions with exponential backoff."""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_error: Exception | None = None
            current_delay = delay
            for attempt in range(1, count + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < count:
                        if on_retry:
                            on_retry(attempt, e)
                        time.sleep(current_delay)
                        current_delay *= backoff
            raise last_error  # type: ignore[misc]
        return wrapper
    return decorator


def retry_shell(
    command: str, count: int = 3, delay: float = 1.0, backoff: float = 2.0, **shell_kwargs: Any,
) -> ProcessOutput:
    """Execute a shell command with automatic retry on failure."""
    current_delay = delay
    for attempt in range(1, count + 1):
        try:
            return shell(command, **shell_kwargs)
        except Exception as e:
            logger.debug("Shell retry attempt %d/%d failed for command '%s': %s", attempt, count, command, e)
            if attempt < count:
                time.sleep(current_delay)
                current_delay *= backoff
    return shell(command, nothrow=True, **shell_kwargs)


def pipe(*commands: str, cwd: str | None = None, timeout: int = 120) -> ProcessOutput:
    """Execute multiple commands piped together."""
    return shell(" | ".join(commands), cwd=cwd, timeout=timeout, nothrow=True)


__all__ = ["ProcessOutput", "cd", "pipe", "quote", "retry", "retry_shell", "shell", "within"]
