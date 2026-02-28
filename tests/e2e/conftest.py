import pytest
pydantic_settings = pytest.importorskip("pydantic_settings", reason="pydantic-settings not installed")

from fastapi.testclient import TestClient

from backend.api.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
