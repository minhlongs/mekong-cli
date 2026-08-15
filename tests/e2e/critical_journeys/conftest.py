"""Shared fixtures for E2E critical journey tests.

Provides:
- Isolated database fixtures (SQLite in tmp_path)
- FastAPI app factory with dependency injection
- Mock external services (Stripe, LLM, email, etc.)
- Authentication helpers
- Test data factories
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Import core modules
from src.raas.credits import CreditStore
from src.raas.tenant import TenantStore
from src.raas.missions import MissionService, mission_router
from src.raas.mission_store import MissionStore
from src.raas.auth import TenantContext, get_tenant_context
from src.auth.session_manager import SessionManager
from src.auth.rbac import Role, UserInfo
from src.core.plugin_loader import PluginLoader
from src.core.rate_limit import RateLimiter


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    """Isolated SQLite DB file per test."""
    return tmp_path / "test_e2e.db"


@pytest.fixture()
def tenant_store(db_path: Path) -> TenantStore:
    """TenantStore with isolated DB."""
    return TenantStore(db_path=db_path)


@pytest.fixture()
def credit_store(db_path: Path) -> CreditStore:
    """CreditStore with isolated DB."""
    return CreditStore(db_path=db_path)


@pytest.fixture()
def mission_store(db_path: Path) -> MissionStore:
    """MissionStore with isolated DB."""
    return MissionStore(db_path=db_path)


@pytest.fixture()
def tasks_dir(tmp_path: Path) -> Path:
    """Isolated tasks directory."""
    d = tmp_path / "tasks"
    d.mkdir()
    return d


# ============================================================================
# Tenant & User Fixtures
# ============================================================================

@pytest.fixture()
def tenant(tenant_store: TenantStore):
    """Create a default tenant."""
    return tenant_store.create_tenant("Test Tenant")


@pytest.fixture()
def admin_user(tenant_store: TenantStore):
    """Create an admin user (admin=true)."""
    tenant = tenant_store.create_tenant("Admin Tenant")
    return UserInfo(
        tenant_id=tenant.id,
        tenant_name=tenant.name,
        api_key=tenant.api_key,
        roles=[Role.ADMIN],
        permissions=["*"],
    )


@pytest.fixture()
def regular_user(tenant_store: TenantStore):
    """Create a regular user (non-admin)."""
    tenant = tenant_store.create_tenant("Regular Tenant")
    return UserInfo(
        tenant_id=tenant.id,
        tenant_name=tenant.name,
        api_key=tenant.api_key,
        roles=[Role.USER],
        permissions=["execute:commands", "read:reports"],
    )


@pytest.fixture()
def tenant_with_credits(tenant_store: TenantStore, credit_store: CreditStore):
    """Create tenant with pre-funded credits."""
    tenant = tenant_store.create_tenant("Funded Tenant")
    credit_store.add(tenant.id, 100, "test funding")
    return tenant


# ============================================================================
# Plugin Fixtures
# ============================================================================

@pytest.fixture()
def plugin_loader(tmp_path: Path):
    """PluginLoader with isolated plugin directory."""
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    return PluginLoader(plugin_dir=plugin_dir)


@pytest.fixture()
def sample_plugin_manifest():
    """Sample plugin manifest for testing."""
    return {
        "id": "test.plugin.sample",
        "name": "Sample Test Plugin",
        "version": "1.0.0",
        "description": "A sample plugin for testing",
        "entrypoint": "plugin.py",
        "commands": [
            {
                "name": "sample-command",
                "description": "Sample command",
                "handler": "main",
                "arguments": [
                    {"name": "input", "type": "string", "required": True}
                ],
            }
        ],
        "permissions": {"file": ["read"], "network": ["outbound"]},
    }


# ============================================================================
# Rate Limit Fixtures
# ============================================================================

@pytest.fixture()
def rate_limiter(tmp_path: Path):
    """RateLimiter with isolated storage."""
    return RateLimiter(storage_path=tmp_path / "rate_limit.db")


# ============================================================================
# App Factory Fixtures
# ============================================================================

@pytest.fixture()
def raas_app(
    credit_store: CreditStore,
    mission_store: MissionStore,
    tasks_dir: Path,
    tenant_store: TenantStore,
) -> FastAPI:
    """Create a FastAPI app with RaaS routes and injected test stores."""
    from src.raas.missions import MissionService

    svc = MissionService(
        mission_store=mission_store,
        credit_store=credit_store,
        tenant_tasks_dir=tasks_dir,
    )
    # Patch module-level singleton
    import src.raas.missions as missions_mod
    missions_mod._service = svc

    app = FastAPI()
    app.include_router(mission_router)
    return app


@pytest.fixture()
def auth_app(tenant_store: TenantStore) -> FastAPI:
    """Create a FastAPI app with auth routes."""
    from src.auth.routes import router as auth_router
    from src.auth.session_manager import SessionManager

    # Mock session manager with test secret
    with patch.object(SessionManager, '_jwt_secret', 'test-secret'):
        app = FastAPI()
        app.include_router(auth_router)
        return app


@pytest.fixture()
def billing_app(credit_store: CreditStore, tenant_store: TenantStore) -> FastAPI:
    """Create a FastAPI app with billing routes."""
    from src.api.billing_routes import router as billing_router

    app = FastAPI()
    app.include_router(billing_router)
    return app


@pytest.fixture()
def plugin_app(plugin_loader: PluginLoader) -> FastAPI:
    """Create a FastAPI app with plugin management routes."""
    from src.plugin.routes import router as plugin_router

    app = FastAPI()
    app.include_router(plugin_router)
    return app


# ============================================================================
# Test Client Fixtures
# ============================================================================

@pytest.fixture()
def client_with_auth(raas_app: FastAPI, tenant):
    """TestClient with auth override for a tenant."""
    def override_auth():
        return TenantContext(
            tenant_id=tenant.id,
            tenant_name=tenant.name,
            api_key=tenant.api_key,
        )
    raas_app.dependency_overrides[get_tenant_context] = override_auth
    with TestClient(raas_app) as c:
        yield c
    raas_app.dependency_overrides.clear()


@pytest.fixture()
def admin_client(raas_app: FastAPI, admin_user: UserInfo):
    """TestClient with admin auth."""
    def override_auth():
        return admin_user
    raas_app.dependency_overrides[get_tenant_context] = override_auth
    with TestClient(raas_app) as c:
        yield c
    raas_app.dependency_overrides.clear()


# ============================================================================
# Mock External Services
# ============================================================================

@pytest.fixture(autouse=True)
def mock_external_services():
    """Mock all external service calls by default."""
    with patch('src.llm.router.LLMRouter.chat_completion') as mock_llm, \
         patch('src.billing.stripe.StripeCustomer.retrieve') as mock_stripe, \
         patch('src.email.service.EmailService.send') as mock_email, \
         patch('src.observability.tracer.trace') as mock_trace:
        mock_llm.return_value = {"choices": [{"message": {"content": "Mock LLM response"}}]}
        mock_stripe.return_value = MagicMock()
        mock_email.return_value = True
        mock_trace.return_value = MagicMock()
        yield {
            'llm': mock_llm,
            'stripe': mock_stripe,
            'email': mock_email,
            'trace': mock_trace,
        }


@pytest.fixture()
def enable_real_llm():
    """Disable LLM mock for tests that need real LLM (marked slow)."""
    with patch('src.llm.router.LLMRouter.chat_completion', side_effect=lambda *args, **kwargs: None):
        yield  # Test will use real LLM if configured via env vars


# ============================================================================
# Test Data Factories
# ============================================================================

def make_command_payload(command: str, args: dict = None) -> dict:
    """Factory for command execution payloads."""
    payload = {"command": command, "args": args or {}}
    return payload


def make_webhook_payload(event_type: str, data: dict) -> dict:
    """Factory for webhook payloads."""
    return {
        "id": f"evt_test_{hash(str(data)) % 10000}",
        "type": event_type,
        "data": data,
    }
