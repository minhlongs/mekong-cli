"""Stub: contract_gen models for test collection."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class ContractTemplate:
    key: str = ""
    title: str = ""
    price: int = 0
    term: str = ""
    scope: str = ""
    _extra: dict = field(default_factory=dict, repr=False)

    @property
    def formatted_price(self) -> str:
        return f"${self.price:,}"
