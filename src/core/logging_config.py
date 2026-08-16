# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Structured logging configuration for Mekong CLI.

Configures structlog for JSON output in production or pretty console
output in development, controlled via environment variables.

Usage:
    from src.core.logging_config import configure_logging
    configure_logging()
"""
from __future__ import annotations

import logging
import os
import structlog


def get_logger(name: str) -> logging.Logger:
    """Return a standard library logger for the given module name."""
    return logging.getLogger(name)


def configure_logging() -> None:
    """Configure structured JSON logging for production.

    Reads LOG_LEVEL (default INFO) and LOG_FORMAT (default json).

    json format: machine-readable JSON lines for log aggregators.
    console format: human-readable colored output for local dev.
    """
    log_level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_name, logging.INFO)
    log_format = os.getenv("LOG_FORMAT", "json").lower()

    # Configure stdlib root logger so uvicorn/fastapi logs go through structlog
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
    )

    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if log_format == "json":
        shared_processors.append(structlog.processors.JSONRenderer())
    else:
        shared_processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=shared_processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
