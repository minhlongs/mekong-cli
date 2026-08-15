"""Stub: contract_gen loader for test collection."""
from __future__ import annotations


def load_template(key: str) -> dict:
    """Stub loader: returns a minimal template dict."""
    return {"key": key, "title": key.replace("_", " ").title()}
