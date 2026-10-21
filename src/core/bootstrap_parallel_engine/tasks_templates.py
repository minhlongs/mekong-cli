"""Domain template scaffolding task (default, vas, fintech, agent)."""

from __future__ import annotations

import json

from .models import BootstrapContext
from .tasks_templates_ext import _scaffold_agent, _scaffold_fintech


def _scaffold_vas(context: BootstrapContext) -> None:
    context.write_file("src/vas/__init__.py", '"""VAS Accounting Module."""\n')
    context.write_file(
        "src/vas/accounting.py",
        '''"""Vietnamese Accounting System (VAS) core ledger."""
from typing import List, Dict, Any

class VasLedger:
    def __init__(self) -> None:
        self.entries: List[Dict[str, Any]] = []

    def record_entry(self, debit_acc: str, credit_acc: str, amount: float, description: str = "") -> Dict[str, Any]:
        entry = {
            "debit": debit_acc,
            "credit": credit_acc,
            "amount": amount,
            "description": description,
        }
        self.entries.append(entry)
        return entry

    def total_balance(self) -> float:
        return sum(e["amount"] for e in self.entries)
''',
    )
    context.write_file(
        "src/vas/tt78_invoice.py",
        '''"""Circular 78 / Decree 123 E-Invoice validation."""
from typing import Dict, Any

def validate_invoice(invoice: Dict[str, Any]) -> bool:
    required_fields = ["invoice_number", "seller_tax_id", "buyer_tax_id", "total_amount"]
    return all(field in invoice for field in required_fields)
''',
    )
    chart_of_accounts = {
        "standard": "VAS Circular 200/2014/TT-BTC",
        "accounts": {
            "111": "Tien mat (Cash)",
            "112": "Tien gui ngan hang (Bank deposits)",
            "131": "Phai thu khach hang (Receivables)",
            "331": "Phai tra nguoi ban (Payables)",
            "511": "Doanh thu ban hang (Revenue)",
            "642": "Chi phi quan ly doanh nghiep (Management expenses)",
        },
    }
    context.write_file(
        "src/vas/chart_of_accounts.json",
        json.dumps(chart_of_accounts, indent=2) + "\n",
    )
    context.write_file(
        "tests/test_vas.py",
        '''"""Tests for VAS accounting module."""
from src.vas.accounting import VasLedger
from src.vas.tt78_invoice import validate_invoice

def test_vas_ledger():
    ledger = VasLedger()
    entry = ledger.record_entry("111", "511", 1000000.0, "Cash sale")
    assert entry["amount"] == 1000000.0
    assert ledger.total_balance() == 1000000.0

def test_validate_invoice():
    inv = {
        "invoice_number": "HD001",
        "seller_tax_id": "0100109106",
        "buyer_tax_id": "0300123456",
        "total_amount": 5000000.0,
    }
    assert validate_invoice(inv) is True
''',
    )


def task_scaffold_templates(context: BootstrapContext) -> None:
    """Scaffold domain-specific templates (default, vas, fintech, agent)."""
    tpl = context.template.lower()
    if tpl == "default":
        context.write_file(
            "src/__init__.py",
            '"""Mekong Application Package."""\n__version__ = "0.1.0"\n',
        )
        context.write_file(
            "src/main.py",
            '"""Application entry point."""\n\ndef main() -> int:\n    print("Hello from Mekong CLI Project!")\n    return 0\n\nif __name__ == "__main__":\n    import sys\n    sys.exit(main())\n',
        )
        context.write_file(
            "tests/test_main.py",
            '"""Smoke test for application."""\nfrom src.main import main\n\ndef test_main():\n    assert main() == 0\n',
        )
    elif tpl == "vas":
        _scaffold_vas(context)
    elif tpl == "fintech":
        _scaffold_fintech(context)
    elif tpl == "agent":
        _scaffold_agent(context)
    else:
        raise ValueError(
            f"Unknown template '{context.template}'. Expected one of: default, vas, fintech, agent"
        )
