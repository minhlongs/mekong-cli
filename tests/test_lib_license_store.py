"""Tests for src.lib.license_store."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.lib import license_store as ls_mod
from src.lib.license_store import LicenseStore, get_license_store


@pytest.fixture(autouse=True)
def _reset_singleton(monkeypatch):
    ls_mod._default_store = None
    yield
    ls_mod._default_store = None


def _write(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data))


class TestEmptyStore:
    def test_get_returns_none(self, tmp_path):
        store = LicenseStore(path=tmp_path / "missing.json")
        assert store.get("any") is None
        assert store.is_active("any") is False
        assert store.tenant_id("any") is None
        assert store.tier("any") is None

    def test_corrupt_file_treated_as_empty(self, tmp_path):
        path = tmp_path / "licenses.json"
        path.write_text("not-json")
        store = LicenseStore(path=path)
        assert store.get("anything") is None


class TestActiveLookup:
    def test_active_license(self, tmp_path):
        path = tmp_path / "licenses.json"
        _write(
            path,
            {
                "lic_a": {
                    "customer_id": "cus_1",
                    "tier": "starter",
                    "status": "active",
                }
            },
        )
        store = LicenseStore(path=path)
        assert store.is_active("lic_a") is True
        assert store.tenant_id("lic_a") == "cus_1"
        assert store.tier("lic_a") == "starter"

    def test_cancelled_license(self, tmp_path):
        path = tmp_path / "licenses.json"
        _write(
            path,
            {"lic_c": {"customer_id": "cus_2", "tier": "pro", "status": "cancelled"}},
        )
        store = LicenseStore(path=path)
        assert store.is_active("lic_c") is False

    def test_root_array_treated_as_empty(self, tmp_path):
        path = tmp_path / "licenses.json"
        path.write_text(json.dumps(["not", "a", "dict"]))
        store = LicenseStore(path=path)
        assert store.get("any") is None


class TestSingleton:
    def test_get_license_store_returns_singleton(self, monkeypatch, tmp_path):
        monkeypatch.setenv("LICENSE_STORE_PATH", str(tmp_path / "x.json"))
        a = get_license_store()
        b = get_license_store()
        assert a is b

    def test_env_override_path(self, monkeypatch, tmp_path):
        target = tmp_path / "custom.json"
        monkeypatch.setenv("LICENSE_STORE_PATH", str(target))
        store = get_license_store()
        assert store.path == target
