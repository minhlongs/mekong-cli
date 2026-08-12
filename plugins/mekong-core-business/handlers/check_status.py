"""Handler for check-status command."""

from __future__ import annotations

import logging
import subprocess
import sys
from typing import Any

logger = logging.getLogger(__name__)


def handle_check_status(ctx: Any, **kwargs: Any) -> dict[str, Any]:
    """Handle check-status command by invoking legacy implementation.

    Args:
        ctx: Plugin context (unused)
        **kwargs: Command arguments

    Returns:
        Dictionary with command result
    """
    logger.info("Executing check-status via legacy module debug_rate_limits")

    # Build CLI arguments from kwargs
    args_list = []
    for key, value in kwargs.items():
        key = key.replace("_", "-")
        if isinstance(value, bool):
            if value:
                args_list.append(f"--{key}")
        elif value is not None:
            args_list.extend([f"--{key}", str(value)])

    # Construct command: python -m src.commands.debug_rate_limits check-status [args]
    cmd_parts = [sys.executable, "-m", "src.commands.debug_rate_limits", "check-status"] + args_list
    cmd_str = " ".join(cmd_parts)

    try:
        logger.debug("Running: %s", cmd_str)
        result = subprocess.run(
            cmd_parts,
            capture_output=True,
            text=True,
            timeout=300,
        )
        return {
            "command": "check-status",
            "status": "success" if result.returncode == 0 else "error",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "execution_info": {"module": "debug_rate_limits", "args": kwargs},
        }
    except subprocess.TimeoutExpired as exc:
        logger.error("Command timed out after %s seconds: %s", exc.timeout, cmd_str)
        return {
            "command": "check-status",
            "status": "timeout",
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or f"Timed out after {exc.timeout} seconds",
            "returncode": -1,
            "execution_info": {"module": "debug_rate_limits", "args": kwargs},
        }
    except Exception as exc:
        logger.exception("Unexpected error executing command")
        return {
            "command": "check-status",
            "status": "exception",
            "stdout": "",
            "stderr": str(exc),
            "returncode": -1,
            "execution_info": {"module": "debug_rate_limits", "args": kwargs},
        }

