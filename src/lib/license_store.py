"""Compatibility shim: tests import src.lib.license_store; implementation lives in engine.license.license_store."""

class _CompatStore:
    """Minimal stub exposing the attribute the legacy test fixture touches."""
    _default_store = None


def get_license_store(*args, **kwargs):  # pragma: no cover — test-only entry point
    raise NotImplementedError("Use engine.license.license_store.get_license_store() instead.")
