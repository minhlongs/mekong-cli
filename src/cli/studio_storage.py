"""
Studio data persistence layer — JSON file storage.

Stores studio, portfolio, deals, and experts in .mekong/ directory.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


STUDIO_DATA_DIR = Path(".mekong/studio")
STUDIO_FILE = STUDIO_DATA_DIR / "studio.json"
PORTFOLIO_FILE = STUDIO_DATA_DIR / "portfolio.json"
DEALFLOW_FILE = STUDIO_DATA_DIR / "dealflow.json"
EXPERTS_FILE = STUDIO_DATA_DIR / "experts.json"
THESIS_FILE = STUDIO_DATA_DIR / "thesis.json"


def _ensure_dir() -> None:
    """Create studio data directory if it doesn't exist."""
    STUDIO_DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_json(filepath: Path, default: Any) -> Any:
    """Load JSON file or return default."""
    if filepath.exists():
        with open(filepath, "r") as f:
            return json.load(f)
    return default


def _save_json(filepath: Path, data: Any) -> None:
    """Save data to JSON file."""
    _ensure_dir()
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, default=str)


# === Studio ===

def get_studio() -> dict | None:
    """Get current studio config."""
    return _load_json(STUDIO_FILE, None)


def save_studio(name: str, thesis: str = "general") -> dict:
    """Save studio config."""
    studio = {"name": name, "thesis": thesis, "initialized": True}
    _save_json(STUDIO_FILE, studio)
    return studio


# === Portfolio ===

def get_portfolio() -> list:
    """Get all portfolio companies."""
    return _load_json(PORTFOLIO_FILE, [])


def save_portfolio_company(
    name: str, sector: str, stage: str = "idea", equity: float = 30.0
) -> dict:
    """Add portfolio company."""
    companies = get_portfolio()
    slug = name.lower().replace(" ", "-").replace("--", "-")

    company = {
        "slug": slug,
        "name": name,
        "sector": sector,
        "stage": stage,
        "equity": equity,
        "created_at": str(Path.cwd()),
    }
    companies.append(company)
    _save_json(PORTFOLIO_FILE, companies)
    return company


def get_portfolio_company(slug: str) -> dict | None:
    """Get single portfolio company by slug."""
    companies = get_portfolio()
    for company in companies:
        if company["slug"] == slug or company["name"].lower() == slug.lower():
            return company
    return None


# === Dealflow ===

def get_dealflow() -> list:
    """Get all deals in pipeline."""
    return _load_json(DEALFLOW_FILE, [])


def add_deal(
    name: str, sector: str, source: str = "manual", one_liner: str = ""
) -> dict:
    """Add deal to pipeline."""
    deals = get_dealflow()
    deal_id = f"deal-{len(deals) + 1:03d}"

    deal = {
        "id": deal_id,
        "name": name,
        "sector": sector,
        "source": source,
        "one_liner": one_liner,
        "stage": "sourced",
    }
    deals.append(deal)
    _save_json(DEALFLOW_FILE, deals)
    return deal


# === Experts ===

def get_experts() -> list:
    """Get all experts in pool."""
    return _load_json(EXPERTS_FILE, [])


def add_expert(name: str, email: str, specialties: list[str]) -> dict:
    """Add expert to pool."""
    experts = get_experts()
    expert_id = f"expert-{len(experts) + 1:03d}"

    expert = {
        "id": expert_id,
        "name": name,
        "email": email,
        "specialties": specialties,
    }
    experts.append(expert)
    _save_json(EXPERTS_FILE, experts)
    return expert


# === Thesis ===

def get_thesis() -> dict:
    """Get investment thesis."""
    return _load_json(THESIS_FILE, {
        "template": "general",
        "focus": "AI-powered video generation and content automation",
        "stages": ["idea", "validation", "mvp", "seed"],
        "sectors": ["ai", "video", "content", "automation"],
    })


def save_thesis(thesis: dict) -> None:
    """Save investment thesis."""
    _save_json(THESIS_FILE, thesis)
