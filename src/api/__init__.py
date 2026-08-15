"""API package for Mekong CLI."""

# Expose route submodules so dotted patch targets resolve from the package,
# e.g. ``src.api.tier_config_routes.router`` and
# ``src.api.quota_status_endpoints.quota_router``.
from src.api import tier_config_routes  # noqa: E402
from src.api import quota_status_endpoints  # noqa: E402
from src.api import raas_router  # noqa: E402

from src.api.webhooks.router import router as webhooks_router

__all__ = [
    "webhooks_router",
    "tier_config_routes",
    "quota_status_endpoints",
    "raas_router",
]
