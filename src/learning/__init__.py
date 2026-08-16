# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - Learning Loop (C4).

Execution-outcome recorder, retry-loop hooks, pattern warnings,
threshold auto-tuning, and `mekong learn` CLI.

Sub-modules:
  outcome_recorder  — ExecutionOutcome dataclass + OutcomeRecorder
  retry_hooks       — attach_learning_hooks, record_outcome, get_pattern_warnings
  learn_cli         — `mekong learn` Typer sub-command
"""
