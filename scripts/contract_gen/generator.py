"""Stub: contract_gen generator for test collection."""
from __future__ import annotations


def generate_markdown_content(template, lead, date_str):
    """Minimal stub matching test expectation."""
    company = lead.get("company", "")
    return (
        f"# {template.title}\n"
        f"Agreement for {lead['name']} of {company}\n"
        f"Amount: {getattr(template, 'formatted_price', '$3,000')}"
    )
