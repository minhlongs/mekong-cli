# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Versioned cross-system contracts for Mekong CLI autonomous runtime."""

from .sophia_integration_v1 import (
    CONTRACT_VERSION,
    SOPHIA_CONTRACT_OPERATIONS,
    SophiaContractValidationError,
    SophiaExecutionContractV1,
    SophiaOutcomeEnvelope,
    SophiaTaskSubmissionRequest,
    SophiaTicketAssignment,
    validate_sophia_handoff_fixture,
)

__all__ = [
    "CONTRACT_VERSION",
    "SOPHIA_CONTRACT_OPERATIONS",
    "SophiaContractValidationError",
    "SophiaExecutionContractV1",
    "SophiaOutcomeEnvelope",
    "SophiaTaskSubmissionRequest",
    "SophiaTicketAssignment",
    "validate_sophia_handoff_fixture",
]
