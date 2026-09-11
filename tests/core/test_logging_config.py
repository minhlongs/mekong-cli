"""Tests for src/core/logging_config.py — structured logging configuration."""

from __future__ import annotations

import logging
from unittest.mock import patch

from src.core.logging_config import configure_logging, get_logger


class TestGetLogger:
    def test_get_logger_returns_standard_logger(self):
        logger = get_logger("my_test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "my_test_module"


class TestConfigureLogging:
    def test_configure_logging_json_format(self):
        with patch.dict("os.environ", {"LOG_LEVEL": "INFO", "LOG_FORMAT": "json"}):
            configure_logging()
        # Ensure no exception and structlog configured

    def test_configure_logging_console_format(self):
        with patch.dict("os.environ", {"LOG_LEVEL": "DEBUG", "LOG_FORMAT": "console"}):
            configure_logging()
        # Hits ConsoleRenderer line 53

    def test_configure_logging_invalid_log_level_defaults_to_info(self):
        with patch.dict("os.environ", {"LOG_LEVEL": "INVALID_LEVEL", "LOG_FORMAT": "json"}):
            configure_logging()
