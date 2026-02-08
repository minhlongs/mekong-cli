"""Configuration loader for Mekong CLI environment variables."""

import os

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_API_TOKEN: str = os.getenv("TELEGRAM_API_TOKEN", "")

if not TELEGRAM_API_TOKEN:
    raise ValueError(
        "TELEGRAM_API_TOKEN is not set. "
        "Please add it to your .env file. See .env.example for reference."
    )
