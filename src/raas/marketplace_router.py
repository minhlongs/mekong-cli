"""RaaS Marketplace API — browse and install skills & commands.

Exposes the .claude/skills/ and .claude/commands/ directories as a
browseable marketplace. Installation copies assets to the user's
~/.claude/ directory and deducts MCU credits via CreditStore.

Endpoints:
    GET    /marketplace/browse          — list all skills + commands
    GET    /marketplace/skills           — list skills only
    GET    /marketplace/commands         — list commands only
    GET    /marketplace/skills/{name}    — skill detail
    GET    /marketplace/commands/{name}  — command detail
    POST   /marketplace/install/skill/{name}     — install skill (deducts credits)
    POST   /marketplace/install/command/{name}   — install command (deducts credits)
"""
from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from src.raas.auth import TenantContext, get_tenant_context
from src.raas.credits import CreditStore
from src.raas.marketplace.license import verify_license_key, verify_purchase
from src.raas.marketplace.payout import monthly_settlement_report

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

# Marketplace source: mekong-cli repo .claude/ directories
_REPO_ROOT = Path(__file__).resolve().parents[2]  # mekong-cli/
_MARKETPLACE_SKILLS = _REPO_ROOT / ".claude" / "skills"
_MARKETPLACE_COMMANDS = _REPO_ROOT / ".claude" / "commands"

# User destination: ~/.claude/ directories
_USER_HOME = Path.home()
_USER_SKILLS = _USER_HOME / ".claude" / "skills"
_USER_COMMANDS = _USER_HOME / ".claude" / "commands"

# Install cost in MCU credits
SKILL_INSTALL_COST = 1
COMMAND_INSTALL_COST = 1

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class MarketplaceItem:
    """Single skill or command entry."""

    name: str
    item_type: str  # "skill" or "command"
    description: str = ""
    category: str = ""
    tags: List[str] = field(default_factory=list)
    path: str = ""
    cost: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.item_type,
            "description": self.description,
            "category": self.category,
            "tags": self.tags,
            "path": self.path,
            "cost": self.cost,
        }


# ---------------------------------------------------------------------------
# Catalog builders
# ---------------------------------------------------------------------------


def _parse_frontmatter(text: str) -> Dict[str, str]:
    """Extract YAML-like frontmatter from markdown text."""
    meta: Dict[str, str] = {}
    if not text.startswith("---"):
        return meta
    end = text.find("---", 3)
    if end < 0:
        return meta
    block = text[3:end].strip()
    for line in block.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip().lower()
            val = val.strip().strip('"').strip("'")
            if key:
                meta[key] = val
    return meta


def _scan_skills() -> List[MarketplaceItem]:
    """Scan .claude/skills/ for all SKILL.md entries."""
    items: List[MarketplaceItem] = []
    if not _MARKETPLACE_SKILLS.exists():
        return items

    for entry in sorted(_MARKETPLACE_SKILLS.iterdir()):
        if not entry.is_dir() or entry.name.startswith("_"):
            continue
        skill_file = entry / "SKILL.md"
        if not skill_file.exists():
            continue

        text = skill_file.read_text(encoding="utf-8", errors="replace")
        fm = _parse_frontmatter(text)

        # First line after frontmatter as fallback description
        desc = fm.get("description", "")
        if not desc:
            # Grab first non-empty line after ---
            end = text.find("---", 3)
            if end >= 0:
                remainder = text[end + 3:].strip()
                desc = remainder.splitlines()[0].lstrip("# ").strip() if remainder else ""

        # Extract tags from content (lines starting with "Tags:" or similar)
        tags: List[str] = []
        if "tags" in fm:
            tags = [t.strip() for t in fm["tags"].split(",") if t.strip()]

        items.append(
            MarketplaceItem(
                name=entry.name,
                item_type="skill",
                description=desc[:200],
                category=fm.get("category", ""),
                tags=tags,
                path=str(skill_file.relative_to(_REPO_ROOT)),
                cost=SKILL_INSTALL_COST,
            )
        )
    return items


def _scan_commands() -> List[MarketplaceItem]:
    """Scan .claude/commands/ for all .md entries."""
    items: List[MarketplaceItem] = []
    if not _MARKETPLACE_COMMANDS.exists():
        return items

    # Scan root level and one subdirectory deep
    for entry in sorted(_MARKETPLACE_COMMANDS.iterdir()):
        if entry.is_file() and entry.suffix == ".md" and not entry.name.startswith("_"):
            text = entry.read_text(encoding="utf-8", errors="replace")
            fm = _parse_frontmatter(text)
            desc = fm.get("description", "")
            if not desc:
                end = text.find("---", 3)
                if end >= 0:
                    remainder = text[end + 3:].strip()
                    desc = remainder.splitlines()[0].lstrip("# ").strip() if remainder else ""

            items.append(
                MarketplaceItem(
                    name=entry.stem,
                    item_type="command",
                    description=desc[:200],
                    category="",
                    tags=[],
                    path=str(entry.relative_to(_REPO_ROOT)),
                    cost=COMMAND_INSTALL_COST,
                )
            )
        elif entry.is_dir() and not entry.name.startswith("_"):
            # Subdirectory — scan .md files inside
            for sub in sorted(entry.iterdir()):
                if sub.is_file() and sub.suffix == ".md":
                    text = sub.read_text(encoding="utf-8", errors="replace")
                    fm = _parse_frontmatter(text)
                    desc = fm.get("description", "")
                    if not desc:
                        end = text.find("---", 3)
                        if end >= 0:
                            remainder = text[end + 3:].strip()
                            desc = (
                                remainder.splitlines()[0].lstrip("# ").strip()
                                if remainder
                                else ""
                            )
                    items.append(
                        MarketplaceItem(
                            name=f"{entry.name}/{sub.stem}",
                            item_type="command",
                            description=desc[:200],
                            category=entry.name,
                            tags=[],
                            path=str(sub.relative_to(_REPO_ROOT)),
                            cost=COMMAND_INSTALL_COST,
                        )
                    )
    return items


# Cache for catalog (rebuild on each request for simplicity; could add TTL)
_catalog_cache: Optional[Dict[str, List[MarketplaceItem]]] = None


def _get_catalog() -> Dict[str, List[MarketplaceItem]]:
    """Return {skills: [...], commands: [...]}."""
    return {
        "skills": _scan_skills(),
        "commands": _scan_commands(),
    }


# ---------------------------------------------------------------------------
# Install logic
# ---------------------------------------------------------------------------


def _install_skill(skill_name: str) -> Dict[str, Any]:
    """Copy a skill from marketplace to user's ~/.claude/skills/.

    Returns dict with status info.
    """
    src = _MARKETPLACE_SKILLS / skill_name
    if not src.exists():
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found in marketplace.")

    if not (src / "SKILL.md").exists():
        raise HTTPException(
            status_code=404,
            detail=f"Skill '{skill_name}' exists but has no SKILL.md.",
        )

    dest = _USER_SKILLS / skill_name
    if dest.exists():
        return {"status": "already_installed", "path": str(dest)}

    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dest)
    return {"status": "installed", "path": str(dest)}


def _install_command(command_name: str) -> Dict[str, Any]:
    """Copy a command from marketplace to user's ~/.claude/commands/.

    Handles both flat commands (name.md) and nested (category/name.md).
    """
    # Try flat file first
    src_file = _MARKETPLACE_COMMANDS / f"{command_name}.md"
    src_dir = _MARKETPLACE_COMMANDS / command_name

    if src_file.exists():
        dest = _USER_COMMANDS / f"{command_name}.md"
        if dest.exists():
            return {"status": "already_installed", "path": str(dest)}
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dest)
        return {"status": "installed", "path": str(dest)}

    if src_dir.is_dir():
        # Nested command — copy entire directory
        dest = _USER_COMMANDS / command_name
        if dest.exists():
            return {"status": "already_installed", "path": str(dest)}
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_dir, dest)
        return {"status": "installed", "path": str(dest)}

    raise HTTPException(
        status_code=404,
        detail=f"Command '{command_name}' not found in marketplace.",
    )


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/marketplace", tags=["Marketplace"])


@router.get("/browse")
def browse_marketplace(
    item_type: Optional[str] = Query(
        None, description="Filter by type: 'skill' or 'command'"
    ),
    q: Optional[str] = Query(None, description="Search query (matches name + description)"),
    limit: int = Query(100, ge=1, le=500, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    tenant: TenantContext = Depends(get_tenant_context),
) -> Dict[str, Any]:
    """Browse all marketplace items (skills + commands).

    Requires Bearer auth. Returns paginated list with total count.
    """
    catalog = _get_catalog()
    all_items: List[MarketplaceItem] = []

    if item_type == "skill":
        all_items = catalog["skills"]
    elif item_type == "command":
        all_items = catalog["commands"]
    else:
        all_items = catalog["skills"] + catalog["commands"]

    # Search filter
    if q:
        q_lower = q.lower()
        all_items = [
            i
            for i in all_items
            if q_lower in i.name.lower() or q_lower in i.description.lower()
        ]

    total = len(all_items)
    page = all_items[offset : offset + limit]

    return {
        "items": [i.to_dict() for i in page],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/skills")
def list_skills(
    q: Optional[str] = Query(None, description="Search query"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    tenant: TenantContext = Depends(get_tenant_context),
) -> Dict[str, Any]:
    """List all available skills."""
    skills = _get_catalog()["skills"]
    if q:
        q_lower = q.lower()
        skills = [
            s for s in skills
            if q_lower in s.name.lower() or q_lower in s.description.lower()
        ]
    total = len(skills)
    return {
        "skills": [s.to_dict() for s in skills[offset : offset + limit]],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/commands")
def list_commands(
    q: Optional[str] = Query(None, description="Search query"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    tenant: TenantContext = Depends(get_tenant_context),
) -> Dict[str, Any]:
    """List all available commands."""
    commands = _get_catalog()["commands"]
    if q:
        q_lower = q.lower()
        commands = [
            c for c in commands
            if q_lower in c.name.lower() or q_lower in c.description.lower()
        ]
    total = len(commands)
    return {
        "commands": [c.to_dict() for c in commands[offset : offset + limit]],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/skills/{name}")
def get_skill_detail(
    name: str,
    tenant: TenantContext = Depends(get_tenant_context),
) -> Dict[str, Any]:
    """Get detail for a specific skill."""
    skills = _get_catalog()["skills"]
    skill = next((s for s in skills if s.name == name), None)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{name}' not found.")
    return skill.to_dict()


@router.get("/commands/{name}")
def get_command_detail(
    name: str,
    tenant: TenantContext = Depends(get_tenant_context),
) -> Dict[str, Any]:
    """Get detail for a specific command."""
    commands = _get_catalog()["commands"]
    cmd = next((c for c in commands if c.name == name), None)
    if not cmd:
        raise HTTPException(status_code=404, detail=f"Command '{name}' not found.")
    return cmd.to_dict()


@router.post("/install/skill/{name}")
def install_skill(
    name: str,
    tenant: TenantContext = Depends(get_tenant_context),
) -> Dict[str, Any]:
    """Install a skill to user's ~/.claude/skills/.

    Deducts 1 MCU credit via CreditStore.
    Returns 402 if insufficient credits.
    """
    # Check and deduct credits
    credit_store = CreditStore()
    balance = credit_store.get_balance(tenant.tenant_id)

    if balance < SKILL_INSTALL_COST:
        raise HTTPException(
            status_code=402,
            detail=(
                f"Insufficient credits: need {SKILL_INSTALL_COST}, "
                f"have {balance}. Add credits at https://polar.sh/mekong."
            ),
            headers={
                "X-Credit-Balance": str(balance),
                "X-Credit-Required": str(SKILL_INSTALL_COST),
            },
        )

    success = credit_store.deduct(
        tenant_id=tenant.tenant_id,
        amount=SKILL_INSTALL_COST,
        reason=f"marketplace_install_skill_{name}",
    )
    if not success:
        raise HTTPException(
            status_code=402,
            detail="Credit deduction failed. Insufficient balance.",
        )

    # Install the skill
    result = _install_skill(name)
    new_balance = credit_store.get_balance(tenant.tenant_id)

    logger.info(
        "marketplace.install: tenant=%s type=skill name=%s cost=%d balance=%d",
        tenant.tenant_id,
        name,
        SKILL_INSTALL_COST,
        new_balance,
    )

    return {
        **result,
        "item_type": "skill",
        "name": name,
        "cost": SKILL_INSTALL_COST,
        "credit_balance": new_balance,
    }


@router.post("/install/command/{name}")
def install_command(
    name: str,
    tenant: TenantContext = Depends(get_tenant_context),
) -> Dict[str, Any]:
    """Install a command to user's ~/.claude/commands/.

    Deducts 1 MCU credit via CreditStore.
    Returns 402 if insufficient credits.
    """
    # Check and deduct credits
    credit_store = CreditStore()
    balance = credit_store.get_balance(tenant.tenant_id)

    if balance < COMMAND_INSTALL_COST:
        raise HTTPException(
            status_code=402,
            detail=(
                f"Insufficient credits: need {COMMAND_INSTALL_COST}, "
                f"have {balance}. Add credits at https://polar.sh/mekong."
            ),
            headers={
                "X-Credit-Balance": str(balance),
                "X-Credit-Required": str(COMMAND_INSTALL_COST),
            },
        )

    success = credit_store.deduct(
        tenant_id=tenant.tenant_id,
        amount=COMMAND_INSTALL_COST,
        reason=f"marketplace_install_command_{name}",
    )
    if not success:
        raise HTTPException(
            status_code=402,
            detail="Credit deduction failed. Insufficient balance.",
        )

    # Install the command
    result = _install_command(name)
    new_balance = credit_store.get_balance(tenant.tenant_id)

    logger.info(
        "marketplace.install: tenant=%s type=command name=%s cost=%d balance=%d",
        tenant.tenant_id,
        name,
        COMMAND_INSTALL_COST,
        new_balance,
    )

    return {
        **result,
        "item_type": "command",
        "name": name,
        "cost": COMMAND_INSTALL_COST,
        "credit_balance": new_balance,
    }


# ---------------------------------------------------------------------------
# License validation
# ---------------------------------------------------------------------------

@router.post("/license/validate")
def validate_plugin_license(
    license_key: str = Query(..., description="License key (lp_...)"),
    plugin_id: str = Query(..., description="Plugin ID"),
    tenant: TenantContext = Depends(get_tenant_context),
) -> Dict[str, Any]:
    """Validate a purchased plugin license for the current tenant."""
    try:
        result = verify_license_key(license_key, plugin_id, tenant.tenant_id)
        return result
    except Exception as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/license/verify-purchase")
def verify_plugin_purchase(
    purchase_id: str = Query(...),
    plugin_id: str = Query(...),
    amount_cents: int = Query(..., ge=0),
) -> Dict[str, Any]:
    """Verify a marketplace purchase record."""
    return verify_purchase(purchase_id, plugin_id, amount_cents)


# ---------------------------------------------------------------------------
# Admin: payout + revenue summary
# ---------------------------------------------------------------------------

@router.get("/admin/revenue-summary")
def revenue_summary(tenant: TenantContext = Depends(get_tenant_context)) -> Dict[str, Any]:
    """Platform-wide (or tenant-scoped) revenue summary."""
    credit_store = CreditStore()
    balance = credit_store.get_balance(tenant.tenant_id)

    return {
        "tenant_id": tenant.tenant_id,
        "credit_balance": balance,
        "marketplace_installs_today": 0,
        "revenue_today_cents": 0,
        "top_plugins": [],
    }


@router.get("/admin/payout-report")
def payout_report(
    plugin_id: Optional[str] = Query(None),
    tenant: TenantContext = Depends(get_tenant_context),
) -> Dict[str, Any]:
    """Monthly settlement report for a plugin or tenant.

    Query params:
        plugin_id: optional — filter to one plugin
    """
    # In production: aggregate actual purchase transactions
    # For now: return structure with placeholder data
    report = monthly_settlement_report(
        plugin_id=plugin_id or "all",
        transactions=[],
    )
    report["tenant_id"] = tenant.tenant_id
    return report


__all__ = ["router"]
