# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.
"""Mekong CLI - CC CLI Spawner (Tôm Hùm Executor)."""

from __future__ import annotations
import asyncio
import os
import re
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class SessionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class CCSession:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    goal: str = ""
    cwd: str = ""
    agent_role: str = ""
    status: SessionStatus = SessionStatus.PENDING
    pid: int | None = None
    output_buffer: list[str] = field(default_factory=list)
    start_time: float = 0.0
    end_time: float = 0.0
    exit_code: int | None = None
    error: str = ""

    @property
    def duration(self) -> float:
        return (self.end_time or time.time()) - self.start_time if self.start_time else 0.0

    @property
    def output(self) -> str:
        return "\n".join(self.output_buffer)

    @property
    def last_output(self) -> str:
        return "\n".join(self.output_buffer[-10:])

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "goal": self.goal[:60], "agent_role": self.agent_role, "status": self.status.value,
            "pid": self.pid, "duration": round(self.duration, 1), "exit_code": self.exit_code, "output_lines": len(self.output_buffer),
        }


class CCSpawner:
    DEFAULT_CWD = str(Path.home() / "mekong-cli")
    DEFAULT_TIMEOUT = 600

    def __init__(self, cwd: str | None = None, timeout: int = DEFAULT_TIMEOUT) -> None:
        self.cwd, self.timeout, self._sessions = cwd or self.DEFAULT_CWD, timeout, {}

    @property
    def active_sessions(self) -> list[CCSession]:
        return [s for s in self._sessions.values() if s.status == SessionStatus.RUNNING]

    @property
    def all_sessions(self) -> list[CCSession]:
        return list(self._sessions.values())

    async def spawn(
        self, goal: str, cwd: str | None = None, timeout: int | None = None,
        project: str | None = None, agent_role: str | None = None,
    ) -> CCSession:
        session = CCSession(goal=goal, cwd=cwd or self.cwd, agent_role=agent_role or "", start_time=time.time())
        if project:
            base_dir = os.path.realpath(self.cwd)
            project_dir = os.path.realpath(os.path.join(base_dir, "apps", project))
            apps_dir = os.path.realpath(os.path.join(base_dir, "apps"))
            if not project_dir.startswith(apps_dir + os.sep) and project_dir != apps_dir:
                session.status, session.error = SessionStatus.FAILED, f"Invalid project path: {project}"
            elif os.path.isdir(project_dir):
                session.cwd = project_dir
            else:
                session.status, session.error = SessionStatus.FAILED, f"Project directory not found: {project_dir}"
            self._sessions[session.id] = session
            return session
        self._sessions[session.id] = session
        asyncio.create_task(self._run_session(session, timeout or self.timeout))
        return session

    async def _run_session(self, session: CCSession, timeout: int) -> None:
        session.status = SessionStatus.RUNNING
        cmd = ["claude", "--dangerously-skip-permissions", "--print"]
        if session.agent_role:
            from src.core.agent_dispatcher import load_agent_prompt
            prompt = load_agent_prompt(session.agent_role)
            cmd.append(
                f"[SYSTEM CONTEXT]\nYou are the {session.agent_role.upper()} agent.\n{prompt[:1500]}\n\n"
                f"[STATUS PROTOCOL]\nWhen done, end with: <status>DONE|DONE_WITH_CONCERNS|BLOCKED|NEEDS_CONTEXT</status>\n\n[TASK]\n{session.goal}"
            )
        else:
            cmd.append(session.goal)
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT, cwd=session.cwd, limit=1024 * 1024,
            )
            session.pid = process.pid

            async def read_output() -> None:
                while process.stdout and (line := await process.stdout.readline()):
                    session.output_buffer.append(line.decode("utf-8", errors="replace").rstrip())
                    if len(session.output_buffer) > 500:
                        session.output_buffer = session.output_buffer[-300:]

            try:
                await asyncio.wait_for(read_output(), timeout=timeout)
            except TimeoutError:
                session.status, session.error, session.exit_code = SessionStatus.TIMEOUT, f"Timed out after {timeout}s", -1
                try:
                    process.kill()
                    await process.wait()
                except ProcessLookupError:
                    pass
                session.end_time = time.time()
                return
            await process.wait()
            session.exit_code = process.returncode
            if process.returncode == 0:
                session.status, _out = SessionStatus.COMPLETED, session.output
                if "<status>BLOCKED</status>" in _out:
                    session.status, session.error = SessionStatus.FAILED, "subagent_blocked"
                elif "<status>NEEDS_CONTEXT</status>" in _out:
                    session.status, session.error = SessionStatus.FAILED, "subagent_needs_context"
                elif "<status>DONE_WITH_CONCERNS</status>" in _out:
                    if m := re.search(r"<status>DONE_WITH_CONCERNS</status>\s*(.*)", _out, re.DOTALL):
                        session.error = f"concerns: {m.group(1)[:200]}"
            else:
                session.status, session.error = SessionStatus.FAILED, f"Exit code: {process.returncode}"
        except FileNotFoundError:
            session.status, session.error = SessionStatus.FAILED, "claude CLI not found. Install: npm i -g @anthropic-ai/claude-code"
        except Exception as e:
            session.status, session.error = SessionStatus.FAILED, str(e)
        session.end_time = time.time()

    def get_session(self, session_id: str) -> CCSession | None:
        return self._sessions.get(session_id)

    def clear_completed(self) -> int:
        done = (SessionStatus.COMPLETED, SessionStatus.FAILED, SessionStatus.TIMEOUT)
        to_remove = [sid for sid, s in self._sessions.items() if s.status in done]
        for sid in to_remove:
            del self._sessions[sid]
        return len(to_remove)


_spawner: CCSpawner | None = None


def get_spawner() -> CCSpawner:
    global _spawner
    if _spawner is None:
        _spawner = CCSpawner()
    return _spawner


__all__ = ["CCSession", "CCSpawner", "SessionStatus", "get_spawner"]
