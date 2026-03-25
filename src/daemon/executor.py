"""
Mekong Daemon - Mission Executor

Runs missions via subprocess (shell) or LLM client.
Abstract enough to swap execution backends.
"""

import json
import logging
import shlex
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Optional

from .llm_config import ModelConfig

logger = logging.getLogger(__name__)


@dataclass
class MissionResult:
    """Result of a mission execution."""
    success: bool
    output: str = ""
    error: str = ""
    duration: float = 0.0
    exit_code: int = -1


class MissionExecutor:
    """
    Executes missions as shell commands or LLM prompts.

    Args:
        working_dir: Default working directory for shell commands
        timeout: Default timeout in seconds
    """

    def __init__(self, working_dir: str = ".", timeout: int = 1800) -> None:
        self._cwd = working_dir
        self._timeout = timeout

    def run_shell(self, command: str, timeout: Optional[int] = None) -> MissionResult:
        """Execute a shell command and return result."""
        t = timeout or self._timeout
        start = time.time()
        try:
            proc = subprocess.run(
                shlex.split(command), capture_output=True, text=True,
                cwd=self._cwd, timeout=t,
            )
            return MissionResult(
                success=proc.returncode == 0,
                output=proc.stdout[-2000:] if proc.stdout else "",
                error=proc.stderr[-1000:] if proc.stderr else "",
                duration=round(time.time() - start, 2),
                exit_code=proc.returncode,
            )
        except subprocess.TimeoutExpired:
            return MissionResult(
                success=False, error=f"Timeout after {t}s",
                duration=round(time.time() - start, 2),
            )
        except Exception as e:
            return MissionResult(
                success=False, error=str(e),
                duration=round(time.time() - start, 2),
            )

    def run_mission_file(self, filepath: str, timeout: Optional[int] = None) -> MissionResult:
        """Read mission file content and execute as shell command."""
        try:
            with open(filepath, "r") as f:
                content = f.read().strip()
            if not content:
                return MissionResult(success=False, error="Empty mission file")
            return self.run_shell(content, timeout)
        except Exception as e:
            return MissionResult(success=False, error=f"Failed to read mission: {e}")

    def run_llm(self, prompt: str, model_config: ModelConfig) -> MissionResult:
        """
        Send a prompt to an OpenAI-compatible LLM endpoint and return the result.

        Uses stdlib urllib — no external dependencies required.

        Args:
            prompt: User message to send to the model
            model_config: ModelConfig with endpoint URL, model ID, auth, and timeouts

        Returns:
            MissionResult with LLM response in output, token usage appended,
            and success=False on any HTTP or parse error.
        """
        start = time.time()
        payload = json.dumps({
            "model": model_config.model_id,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": model_config.max_tokens,
            "temperature": model_config.temperature,
        }).encode("utf-8")

        req = urllib.request.Request(
            model_config.chat_url,
            data=payload,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {model_config.api_key}",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=model_config.timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))

            choices = body.get("choices", [])
            if not choices:
                return MissionResult(
                    success=False,
                    error="LLM returned no choices",
                    duration=round(time.time() - start, 2),
                )

            content = choices[0].get("message", {}).get("content", "")

            # Append token usage to output when available
            usage = body.get("usage", {})
            usage_note = ""
            if usage:
                usage_note = (
                    f"\n\n[tokens: prompt={usage.get('prompt_tokens', '?')} "
                    f"completion={usage.get('completion_tokens', '?')} "
                    f"total={usage.get('total_tokens', '?')}]"
                )

            return MissionResult(
                success=True,
                output=content + usage_note,
                duration=round(time.time() - start, 2),
                exit_code=0,
            )

        except urllib.error.HTTPError as exc:
            error_body = ""
            try:
                error_body = exc.read().decode("utf-8")[:500]
            except Exception:
                pass
            return MissionResult(
                success=False,
                error=f"HTTP {exc.code}: {exc.reason} — {error_body}",
                duration=round(time.time() - start, 2),
            )
        except urllib.error.URLError as exc:
            return MissionResult(
                success=False,
                error=f"Connection error: {exc.reason}",
                duration=round(time.time() - start, 2),
            )
        except (json.JSONDecodeError, KeyError) as exc:
            return MissionResult(
                success=False,
                error=f"Failed to parse LLM response: {exc}",
                duration=round(time.time() - start, 2),
            )
        except Exception as exc:
            return MissionResult(
                success=False,
                error=f"Unexpected error: {exc}",
                duration=round(time.time() - start, 2),
            )


__all__ = ["MissionExecutor", "MissionResult"]
