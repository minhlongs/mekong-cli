"""Mekong CLI 7 — Gate registry + protocol.

Gates are hard stops before dangerous actions. When a node hits a gate and
no operator decision is provided, the CLI exits with code 42 so the host
agent can ask the operator, then resume with --decision.
"""

from __future__ import annotations

from dataclasses import dataclass

GATE_EXIT_CODE = 42

# Default gates: keyword -> (gate key, message). Never overridable.
DEFAULT_GATES: dict[str, tuple[str, str]] = {
    "deploy": ("deploy", "deploying to production"),
    "rm": ("rm", "deleting files/directories"),
    "git push --force": ("force_push", "force-pushing to git"),
    "chi-tien": ("spend_money", "spending money"),
    "xoa-data": ("delete_data", "deleting data"),
}

# Hard gates from registry.yaml hard_gates — enforced but message-driven.
HARD_GATES = {
    "code_review_required": "code review is required before merge",
    "ci_checks_pass": "CI checks must pass before merge",
    "no_force_push_main": "force-push to main is forbidden",
}

# Tools that may run without a gate.
SAFE_TOOLS = {
    "read",
    "write",
    "cat",
    "bash-test",
    "bash",
    "grep",
    "glob",
    "edit",
    "apply-patch",
    "apply_patch",
    "webfetch",
    "question",
    "lsp",
}


class GateNotAllowed(RuntimeError):
    pass


@dataclass
class GateDecision:
    blocked: bool
    gate_key: str = ""
    message: str = ""
    exit_code: int = 0
    hard: bool = False


class GateRegistry:
    def __init__(self, extra_gates: dict[str, tuple[str, str]] | None = None):
        self.gates: dict[str, tuple[str, str]] = dict(DEFAULT_GATES)
        if extra_gates:
            self.gates.update(extra_gates)
        # hard gates always present
        for key, msg in HARD_GATES.items():
            self.gates.setdefault(key, (key, msg))

    def evaluate(self, node_task: str, tool: str = "", hard_flags: list[str] | None = None) -> GateDecision:
        """Return the first matching gate for a node task / tool, or not blocked."""
        hard_flags = hard_flags or []
        for flag in hard_flags:
            if flag in HARD_GATES:
                return GateDecision(
                    blocked=True,
                    gate_key=flag,
                    message=HARD_GATES[flag],
                    exit_code=GATE_EXIT_CODE,
                    hard=True,
                )
        for keyword, (key, msg) in self.gates.items():
            normalized_keyword = keyword.lower().replace("-", " ").replace("_", " ")
            if normalized_keyword in node_task.lower() or normalized_keyword in tool.lower():
                return GateDecision(
                    blocked=True,
                    gate_key=key,
                    message=msg,
                    exit_code=GATE_EXIT_CODE,
                    hard=key in HARD_GATES,
                )
        return GateDecision(blocked=False)

    def ensure_tool_allowed(self, tool: str) -> None:
        """Raise GateNotAllowed for tools outside the whitelist."""
        base = tool.split(" ")[0].lower()
        if base not in SAFE_TOOLS:
            raise GateNotAllowed(f"tool '{base}' is not in whitelist {sorted(SAFE_TOOLS)}")


# ─────────────────────────────────────────────────────────────────────────────
# Per-agent permissions (port of opencode AgentConfig.permission)
# ─────────────────────────────────────────────────────────────────────────────

PERMISSION_MODES = ("allow", "ask", "deny")

# Defaults for built-in roles (safe by default).
DEFAULT_AGENT_PERMISSIONS: dict[str, dict[str, str]] = {
    "eng": {"edit": "allow", "bash": "allow", "read": "allow", "grep": "allow", "glob": "allow", "webfetch": "deny"},
    "pm": {"edit": "allow", "bash": "deny", "read": "allow", "grep": "allow", "glob": "allow", "webfetch": "allow"},
    "ops": {"edit": "deny", "bash": "allow", "read": "allow", "grep": "allow", "glob": "allow", "webfetch": "allow"},
    "ae": {"edit": "allow", "bash": "deny", "read": "allow", "grep": "deny", "glob": "deny", "webfetch": "allow"},
    "ceo": {"edit": "allow", "bash": "allow", "read": "allow", "grep": "allow", "glob": "allow", "webfetch": "allow"},
    "sun-tzu": {"edit": "deny", "bash": "deny", "read": "allow", "grep": "allow", "glob": "allow", "webfetch": "allow"},
}


class PermissionDenied(RuntimeError):
    pass


class AgentPermissionResolver:
    """Resolve allow/ask/deny for a tool per agent, with bash glob patterns.

    Mirrors opencode: last matching rule wins; bash accepts a dict of
    command-glob -> mode.
    """

    def __init__(self, overrides: dict[str, dict[str, Any]] | None = None):
        self.permissions: dict[str, dict[str, Any]] = {}
        for agent, perms in DEFAULT_AGENT_PERMISSIONS.items():
            self.permissions[agent] = dict(perms)
        if overrides:
            for agent, perms in overrides.items():
                base = self.permissions.setdefault(agent, {})
                base.update(perms)

    def mode_for(self, agent: str, tool: str, command: str = "") -> str:
        perms = self.permissions.get(agent, {})
        raw = perms.get(tool, "allow")
        base_mode = raw if isinstance(raw, str) else "allow"

        if tool in ("bash", "bash-test") and command:
            rule = perms.get("bash")
            if isinstance(rule, dict):
                matched = "ask"
                for pattern, mode in rule.items():
                    if pattern == "*" or _glob_match(pattern, command):
                        matched = mode
                return matched
            if isinstance(rule, str):
                return rule
        return base_mode if base_mode in PERMISSION_MODES else "allow"

    def check(self, agent: str, tool: str, command: str = "") -> None:
        """Raise PermissionDenied when the agent may not run the tool."""
        mode = self.mode_for(agent, tool, command)
        if mode == "deny":
            raise PermissionDenied(f"agent '{agent}' is denied tool '{tool}'" + (f": {command[:60]}" if command else ""))
        if mode == "ask":
            # 'ask' surfaces as a gate in the harness (exit 42 protocol).
            raise PermissionDenied(f"agent '{agent}' needs approval for {tool}" + (f": {command[:60]}" if command else ""))


def _glob_match(pattern: str, text: str) -> bool:
    """Minimal glob matching (* and ?), case-insensitive, on command text."""
    import fnmatch

    p = pattern.lower()
    t = text.lower()
    if "*" in p or "?" in p:
        return fnmatch.fnmatch(t, p) or any(fnmatch.fnmatch(word, p) for word in t.split())
    return p in t
