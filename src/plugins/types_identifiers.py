# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Plugin identifiers and basic types."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class PluginId(str):
    """Reverse-domain plugin id, e.g. ``com.example.my-plugin``."""

    _PATTERN = r"^[a-z0-9]+([.\-][a-z0-9]+)*\.[a-z0-9]+$"

    def __new__(cls, raw: str) -> PluginId:
        import re

        if not isinstance(raw, str) or not re.match(cls._PATTERN, raw):
            raise ValueError(
                f"Invalid plugin id '{raw}': expected reverse-domain (e.g. com.example.my-plugin)"
            )
        return super().__new__(cls, raw)


class HookId(str):
    """Identifier of a hook point registered inside a plugin."""

    def __new__(cls, raw: str) -> HookId:
        if not raw or not isinstance(raw, str):
            raise ValueError("HookId must be a non-empty string")
        return super().__new__(cls, raw)


class HookSpec(str, Enum):
    """Lifecycle hook points exposed by the plugin system."""

    BEFORE_COMMAND = "before_command"
    AFTER_COMMAND = "after_command"
    ON_ERROR = "on_error"
    ON_STARTUP = "on_startup"
    ON_SHUTDOWN = "on_shutdown"


class ResultStatus(str, Enum):
    OK = "ok"
    ERROR = "error"
    SKIPPED = "skipped"
    NOT_APPLICABLE = "not_applicable"


@dataclass
class Result:
    """Operation outcome from a plugin action."""

    status: ResultStatus
    value: Any = None
    error: Optional[str] = None
    meta: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def ok(value: Any = None, **meta: Any) -> Result:
        return Result(status=ResultStatus.OK, value=value, meta=meta)

    @staticmethod
    def err(error: str, **meta: Any) -> Result:
        return Result(status=ResultStatus.ERROR, error=error, meta=meta)

    @staticmethod
    def skip(reason: str = "skipped", **meta: Any) -> Result:
        return Result(status=ResultStatus.SKIPPED, error=reason, meta=meta)

    @staticmethod
    def na(**meta: Any) -> Result:
        return Result(status=ResultStatus.NOT_APPLICABLE, meta=meta)
