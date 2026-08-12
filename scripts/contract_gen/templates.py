"""Stub: contract_gen templates for test collection."""
from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class _ContractTemplate:
    key: str
    title: str
    price: int = 3000
    term: str = "1 month"
    scope: str = ""

    @property
    def formatted_price(self) -> str:
        return f"${self.price:,}"

TEMPLATES: dict = {"ghost_cto": _ContractTemplate(key="ghost_cto", title="Ghost CTO Lite Service Agreement")}
