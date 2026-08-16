# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Customer Interview Program - Main Entry Point

Registers customer interview commands with the Mekong CLI.
"""

from .commands import app

# Command metadata for Mekong CLI discovery
COMMAND_METADATA = {
    "name": "customer-interview",
    "description": "Customer interview management for PMF validation",
    "category": "business",
    "layer": "Business",
    "tags": ["customer", "interview", "pmf", "research"],
    "mcu_cost": {
        "plan": 1,
        "recruit": 2,
        "schedule": 1,
        "conduct": 2,
        "transcribe": 3,
        "analyze": 3,
        "report": 2,
        "list": 0,
        "show": 0,
        "stats": 0,
        "export": 1,
    },
    "examples": [
        "mekong customer-interview plan 'PMF Study' 'Understand onboarding pain'",
        "mekong customer-interview list",
        "mekong customer-interview conduct <id> --guided",
        "mekong customer-interview analyze <id>",
    ]
}

def get_app():
    """Return the Typer app for registration."""
    return app

if __name__ == "__main__":
    app()
