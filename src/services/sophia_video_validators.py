# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Sophia video input validation — identifiers, job ids, and script text."""

from __future__ import annotations

import re

SAFE_IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,63}$")
SAFE_JOB_ID_PATTERN = re.compile(r"^sophia-[a-zA-Z0-9_-]{8,64}$")
FORBIDDEN_SCRIPT_CHARS = {";", "`", "$", "\0"}


def validate_identifier(name: str, label: str = "identifier") -> str:
    cleaned = name.strip()
    if not cleaned or cleaned.startswith("-") or not SAFE_IDENTIFIER_PATTERN.match(cleaned):
        raise ValueError(f"Invalid {label}: '{name}'. Must be alphanumeric and may contain '.', '_', or '-'.")
    return cleaned


def validate_job_id(job_id: str) -> str:
    cleaned = job_id.strip()
    if not cleaned or not SAFE_JOB_ID_PATTERN.match(cleaned):
        raise ValueError(f"Invalid job ID: '{job_id}'. Must match pattern 'sophia-[id]'.")
    return cleaned


def sanitize_script(script: str) -> str:
    cleaned = script.strip()
    if len(cleaned) < 10:
        raise ValueError("Script text too short. Minimum 10 characters required.")
    if len(cleaned) > 10000:
        raise ValueError(f"Script text too long ({len(cleaned)} chars). Maximum 10,000 characters allowed.")
    for ch in FORBIDDEN_SCRIPT_CHARS:
        if ch in cleaned:
            raise ValueError(f"Forbidden character '{ch}' detected in script text.")
    return cleaned
