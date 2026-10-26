# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Skill and command installation helpers for RaaS Marketplace."""

from __future__ import annotations

import logging
import shutil
import sys
from pathlib import Path
from typing import Any, Callable, Dict

from fastapi import HTTPException

logger = logging.getLogger(__name__)

_DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_SKILLS = _DEFAULT_REPO_ROOT / ".claude" / "skills"
_DEFAULT_COMMANDS = _DEFAULT_REPO_ROOT / ".claude" / "commands"
_DEFAULT_USER_HOME = Path.home()
_DEFAULT_USER_SKILLS = _DEFAULT_USER_HOME / ".claude" / "skills"
_DEFAULT_USER_COMMANDS = _DEFAULT_USER_HOME / ".claude" / "commands"


def _mod() -> Any:
    return sys.modules.get("src.raas.marketplace_router")


def _install_skill(skill_name: str) -> Dict[str, Any]:
    """Copy a skill from marketplace to user's ~/.claude/skills/."""
    mod = _mod()
    marketplace_skills = getattr(mod, "_MARKETPLACE_SKILLS", _DEFAULT_SKILLS)
    user_skills = getattr(mod, "_USER_SKILLS", _DEFAULT_USER_SKILLS)

    src = marketplace_skills / skill_name
    if not src.exists():
        raise HTTPException(
            status_code=404, detail=f"Skill '{skill_name}' not found in marketplace."
        )

    if not (src / "SKILL.md").exists():
        raise HTTPException(
            status_code=404,
            detail=f"Skill '{skill_name}' exists but has no SKILL.md.",
        )

    dest = user_skills / skill_name
    if dest.exists():
        return {"status": "already_installed", "path": str(dest)}

    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dest)
    return {"status": "installed", "path": str(dest)}


def _install_command(command_name: str) -> Dict[str, Any]:
    """Copy a command from marketplace to user's ~/.claude/commands/."""
    mod = _mod()
    marketplace_commands = getattr(mod, "_MARKETPLACE_COMMANDS", _DEFAULT_COMMANDS)
    user_commands = getattr(mod, "_USER_COMMANDS", _DEFAULT_USER_COMMANDS)

    src_file = marketplace_commands / f"{command_name}.md"
    src_dir = marketplace_commands / command_name

    if src_file.exists():
        dest = user_commands / f"{command_name}.md"
        if dest.exists():
            return {"status": "already_installed", "path": str(dest)}
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dest)
        return {"status": "installed", "path": str(dest)}

    if src_dir.is_dir():
        dest = user_commands / command_name
        if dest.exists():
            return {"status": "already_installed", "path": str(dest)}
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_dir, dest)
        return {"status": "installed", "path": str(dest)}

    raise HTTPException(
        status_code=404,
        detail=f"Command '{command_name}' not found in marketplace.",
    )


def _deduct_and_install(
    tenant_id: str,
    item_type: str,
    name: str,
    cost: int,
    install_fn: Callable[[str], Dict[str, Any]],
) -> Dict[str, Any]:
    """Deduct credits via CreditStore and invoke install_fn."""
    from src.raas.credits import CreditStore as DefaultCreditStore

    mod = _mod()
    credit_store_cls = getattr(mod, "CreditStore", DefaultCreditStore)
    credit_store = credit_store_cls()
    balance = credit_store.get_balance(tenant_id)

    if balance < cost:
        raise HTTPException(
            status_code=402,
            detail=(
                f"Insufficient credits: need {cost}, "
                f"have {balance}. Add credits via Dual-Rail checkout at /v1/checkout."
            ),
            headers={
                "X-Credit-Balance": str(balance),
                "X-Credit-Required": str(cost),
            },
        )

    success = credit_store.deduct(
        tenant_id=tenant_id,
        amount=cost,
        reason=f"marketplace_install_{item_type}_{name}",
    )
    if not success:
        raise HTTPException(
            status_code=402,
            detail="Credit deduction failed. Insufficient balance.",
        )

    result = install_fn(name)
    new_balance = credit_store.get_balance(tenant_id)

    logger.info(
        "marketplace.install: tenant=%s type=%s name=%s cost=%d balance=%d",
        tenant_id,
        item_type,
        name,
        cost,
        new_balance,
    )

    return {
        **result,
        "item_type": item_type,
        "name": name,
        "cost": cost,
        "credit_balance": new_balance,
    }
