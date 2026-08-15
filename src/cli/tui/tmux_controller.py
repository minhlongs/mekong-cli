"""tmux controller — spawn/attach interactive agent sessions on M1 Pro via ssh.

Uses subprocess ssh (no new deps). One tmux socket per controller; one session
per agent. The TUI polls capture-pane and sends keys.
"""

from __future__ import annotations

import shlex
import subprocess

SSH_HOST = "m1pro-home"
SSH_PORT = "2222"
SOCKET = "/tmp/mk-tui-tmux/mk.sock"
BASE_ENV = "export PATH=/opt/homebrew/bin:$PATH; export SOCK={sock}; mkdir -p /tmp/mk-tui-tmux".format(
    sock=SOCKET
)
# proxy socks5 in .zshrc breaks claude/opencode/wrangler — unset in agent shells
UNSET_PROXY = (
    "unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy; "
)

AGENTS: dict[str, dict[str, str]] = {
    "claude": {"session": "mk-claude", "binary": "claude", "desc": "Claude Code"},
    "opencode": {"session": "mk-opencode", "binary": "opencode", "desc": "opencode"},
}

AgentStatus = dict[str, str]


def _ssh(cmd: str, timeout: int = 20) -> tuple[str, str]:
    prefix = "export PATH=/opt/homebrew/bin:/usr/local/bin:$PATH; "
    full = f"ssh -p {SSH_PORT} {SSH_HOST} -- {prefix}{cmd}"
    proc = subprocess.run(
        full, shell=True, capture_output=True, text=True, timeout=timeout
    )
    return proc.stdout, proc.stderr


def list_agents() -> list[AgentStatus]:
    out: list[AgentStatus] = []
    for key, cfg in AGENTS.items():
        session = cfg["session"]
        stdout, _ = _ssh(f"tmux -S {SOCKET} has-session -t {session} 2>/dev/null && echo RUNNING || echo STOPPED")
        running = "RUNNING" in stdout
        out.append(
            {
                "id": key,
                "name": cfg["desc"],
                "binary": cfg["binary"],
                "status": "running" if running else "stopped",
            }
        )
    return out


def spawn(agent_id: str, workdir: str | None = None) -> tuple[bool, str]:
    cfg = AGENTS.get(agent_id)
    if not cfg:
        return False, f"unknown agent: {agent_id}"
    session = cfg["session"]
    binary = cfg["binary"]
    cwd = f"cd {shlex.quote(workdir)}; " if workdir else ""
    cmd = (
        f"{BASE_ENV}; tmux -S {SOCKET} kill-session -t {session} 2>/dev/null; "
        f"tmux -S {SOCKET} new -d -s {session}; "
        f"tmux -S {SOCKET} send-keys -t {session} "
        f"{shlex.quote(cwd + UNSET_PROXY + binary)} Enter"
    )
    stdout, stderr = _ssh(cmd)
    if stderr and "error" in stderr.lower():
        return False, stderr.strip()[:200]
    return True, f"spawned {binary} in session {session}"


def stop(agent_id: str) -> tuple[bool, str]:
    cfg = AGENTS.get(agent_id)
    if not cfg:
        return False, f"unknown agent: {agent_id}"
    stdout, _ = _ssh(
        f"tmux -S {SOCKET} kill-session -t {cfg['session']} 2>/dev/null && echo KILLED"
    )
    return True, "stopped" if "KILLED" in stdout else "not running"


def capture(agent_id: str, lines: int = 40) -> str:
    cfg = AGENTS.get(agent_id)
    if not cfg:
        return ""
    stdout, _ = _ssh(
        f"tmux -S {SOCKET} capture-pane -p -J -t {cfg['session']} -S -{lines}"
    )
    return stdout


def send_key(agent_id: str, text: str) -> None:
    cfg = AGENTS.get(agent_id)
    if not cfg:
        return
    _ssh(
        f"tmux -S {SOCKET} send-keys -t {cfg['session']} -l {shlex.quote(text)}"
    )


def send_enter(agent_id: str) -> None:
    cfg = AGENTS.get(agent_id)
    if not cfg:
        return
    _ssh(f"tmux -S {SOCKET} send-keys -t {cfg['session']} Enter")
