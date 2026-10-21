# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - Command Sanitizer."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class SanitizationResult:
    is_safe: bool = True
    sanitized_command: str = ""
    blocked_patterns: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    blocked_reason: str = ""


class CommandSanitizer:
    """Sanitizes shell commands to prevent injection attacks."""

    DANGEROUS_PATTERNS = [
        (r";\s*\S+", "command_separator"), (r"\|\|", "pipe_or"), (r"\|\s*\S+", "pipe_injection"),
        (r"&&\s*\S+", "command_chain"), (r"`[^`]+`", "backtick_execution"),
        (r"\$\(.*\)", "dollar_paren_execution"), (r"\$\{.*\}", "dollar_brace_execution"),
        (r"rm\s+(-[rf]+\s+)?/", "rm_root"), (r"rm\s+(-[rf]+\s+)?\*", "rm_glob"),
        (r">\s*/", "redirect_to_root"), (r"curl\s+.*\|\s*(ba)?sh", "curl_pipe_shell"),
        (r"wget\s+.*\|\s*(ba)?sh", "wget_pipe_shell"), (r"(curl|wget)\s+.*-o\s+~", "download_to_home"),
        (r"sudo\s+", "sudo_execution"), (r"su\s+", "su_execution"),
        (r"chmod\s+[0-7]{3,4}\s+", "chmod_execution"), (r"chown\s+", "chown_execution"),
        (r"nohup\s+", "nohup_execution"), (r"(?<![a-z])at\s+", "at_scheduling"),
        (r"cron", "cron_manipulation"), (r"export\s+[A-Z_]+=", "export_env"), (r"unset\s+", "unset_env"),
    ]

    SUSPICIOUS_PATTERNS = [
        (r"eval\s+", "eval_usage"), (r"exec\s+", "exec_usage"), (r"python.*-c\s+", "python_exec"),
        (r"node.*-e\s+", "node_exec"), (r"/dev/(tcp|udp)", "dev_tcp"), (r"nc\s+", "netcat_usage"),
        (r"base64\s+-d", "base64_decode"), (r">\s*\.", "dot_redirect"), (r"\.\./", "parent_dir_access"),
    ]

    STRICT_MODE_COMMANDS = ["rm", "mv", "cp", "dd", "mkfs", "fdisk", "parted"]

    def __init__(
        self, strict_mode: bool = False, allow_patterns: list[str] | None = None, deny_patterns: list[str] | None = None,
    ) -> None:
        self.strict_mode = strict_mode
        self.allow_patterns = allow_patterns or []
        self.deny_patterns = deny_patterns or []
        self._dangerous_regex = [(re.compile(p, re.IGNORECASE), n) for p, n in self.DANGEROUS_PATTERNS]
        self._suspicious_regex = [(re.compile(p, re.IGNORECASE), n) for p, n in self.SUSPICIOUS_PATTERNS]

    def sanitize(self, command: str) -> SanitizationResult:
        result = SanitizationResult(is_safe=True, sanitized_command=strip_invisible_chars(command.strip()))
        command = strip_invisible_chars(command)
        if not command or not command.strip():
            result.is_safe, result.blocked_reason = False, "Empty command"
            return result

        if _has_command_chaining(command):
            result.is_safe = False
            result.blocked_patterns.append("command_chaining")
            result.blocked_reason = "Command chaining characters (; && || | newline) detected"

        for pattern_str in self.deny_patterns:
            try:
                if re.search(pattern_str, command, re.IGNORECASE):
                    result.is_safe = False
                    result.blocked_patterns.append(f"custom_deny:{pattern_str}")
                    result.blocked_reason = f"Matches custom deny pattern: {pattern_str}"
            except re.error:
                pass

        for regex, name in self._dangerous_regex:
            if regex.search(command):
                result.is_safe = False
                result.blocked_patterns.append(name)
                result.warnings.append(f"Dangerous pattern detected: {name}")

        if result.is_safe:
            for pattern_str in self.allow_patterns:
                try:
                    if re.search(pattern_str, command, re.IGNORECASE):
                        result.warnings.append(f"Command matches allow pattern: {pattern_str}")
                except re.error:
                    pass

        if not result.is_safe:
            result.blocked_reason = f"Dangerous patterns detected: {', '.join(result.blocked_patterns)}"
            return result

        for regex, name in self._suspicious_regex:
            if regex.search(command):
                result.warnings.append(f"Suspicious pattern: {name}")
                if self.strict_mode:
                    result.is_safe = False
                    result.blocked_patterns.append(name)

        if self.strict_mode:
            self._apply_strict_mode_checks(command, result)
        return result

    def _apply_strict_mode_checks(self, command: str, result: SanitizationResult) -> None:
        cmd_parts = command.split()
        if cmd_parts and cmd_parts[0] in self.STRICT_MODE_COMMANDS:
            result.warnings.append(f"Strict mode: '{cmd_parts[0]}' command requires review")
        command_separators = len(re.findall(r"[;&|]", command))
        if command_separators > 1:
            result.warnings.append(f"Multiple command separators detected: {command_separators}")
        if len(command) > 500:
            result.warnings.append(f"Command unusually long ({len(command)} chars) - potential obfuscation")

    def is_safe_command(self, command: str) -> bool:
        return self.sanitize(command).is_safe

    def get_blocked_reason(self, command: str) -> str:
        return self.sanitize(command).blocked_reason or "Command is safe"

    _sanitizer: CommandSanitizer | None = None


_sanitizer: CommandSanitizer | None = None


def get_sanitizer(strict_mode: bool = False) -> CommandSanitizer:
    global _sanitizer
    if _sanitizer is None:
        _sanitizer = CommandSanitizer(strict_mode=strict_mode)
    return _sanitizer


_INVISIBLE_CHARS_RE = re.compile("[​‌‍﻿‎‏‪‮]")
_CHAINING_RE = re.compile(r"[;&|]|\n")


def _has_command_chaining(command: str) -> bool:
    return bool(_CHAINING_RE.search(command))


def strip_invisible_chars(command: str) -> str:
    return _INVISIBLE_CHARS_RE.sub("", command)


__all__ = ["CommandSanitizer", "SanitizationResult", "get_sanitizer"]
