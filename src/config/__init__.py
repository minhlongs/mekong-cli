"""Configuration package for Mekong CLI."""

from pathlib import Path

from src.config.logging_config import get_logger, setup_logging
from src.config.priority_stack import PriorityStack

PRIORITY_STACK = PriorityStack(project_root=str(Path(__file__).resolve().parent.parent))

__all__ = ["get_logger", "setup_logging", "PriorityStack", "PRIORITY_STACK"]
