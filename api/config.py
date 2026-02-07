import os
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application Settings
    """
    # Application
    APP_ENV: str = "development"
    DEBUG: bool = True

    # Supabase / Database
    SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
    SUPABASE_KEY: Optional[str] = os.getenv("SUPABASE_KEY")

    # Stripe
    STRIPE_SECRET_KEY: Optional[str] = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET: Optional[str] = os.getenv("STRIPE_WEBHOOK_SECRET")

    # Gumroad
    GUMROAD_ACCESS_TOKEN: Optional[str] = os.getenv("GUMROAD_ACCESS_TOKEN")
    GUMROAD_WEBHOOK_SECRET: Optional[str] = os.getenv("GUMROAD_WEBHOOK_SECRET")

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings():
    return Settings()
