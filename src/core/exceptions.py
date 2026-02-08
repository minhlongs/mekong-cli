"""
Mekong CLI - Custom Exceptions

Structured error types for the Plan-Execute-Verify engine.
"""


class MekongError(Exception):
    """Base exception for all Mekong CLI errors."""


class PlanningError(MekongError):
    """Raised when task planning/decomposition fails."""


class ExecutionError(MekongError):
    """Raised when step execution fails."""

    def __init__(self, message: str, step_order: int = 0, exit_code: int = 1):
        self.step_order = step_order
        self.exit_code = exit_code
        super().__init__(message)


class VerificationError(MekongError):
    """Raised when verification criteria are not met."""

    def __init__(self, message: str, failed_checks: list = None):
        self.failed_checks = failed_checks or []
        super().__init__(message)


class RollbackError(MekongError):
    """Raised when rollback of a failed step fails."""

    def __init__(self, message: str, original_error: Exception = None):
        self.original_error = original_error
        super().__init__(message)


class LLMClientError(MekongError):
    """Raised when LLM client encounters an error."""


class RecipeParseError(MekongError):
    """Raised when recipe markdown parsing fails."""


class AgentError(MekongError):
    """Raised when an agent operation fails."""

    def __init__(self, message: str, agent_name: str = ""):
        self.agent_name = agent_name
        super().__init__(message)


__all__ = [
    "MekongError",
    "PlanningError",
    "ExecutionError",
    "VerificationError",
    "RollbackError",
    "LLMClientError",
    "RecipeParseError",
    "AgentError",
]
