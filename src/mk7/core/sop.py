"""Mekong CLI 7 — SOP engine (port of mekong v6 sops/).

Loads markdown SOPs from sops/<layer>/<name>.md, extracts steps, and builds
repo-specific ship commands (commit/push/deploy/smoke) from the repo's own
doctrine (package.json scripts, CLAUDE.deploy.md, docs/deploy*.md).
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

SOPS_DIR = Path(__file__).resolve().parents[3] / "sops"

LAYERS = ["business", "ceo", "engineering", "ops", "shared"]


@dataclass
class SopDocument:
    name: str
    layer: str
    path: Path
    body: str
    steps: list[str] = field(default_factory=list)

    @property
    def intent(self) -> str:
        m = re.search(r"## Intent\s*\n+(.+?)(?=\n##|\Z)", self.body, re.S)
        return m.group(1).strip() if m else self.name


def load_all() -> list[SopDocument]:
    docs: list[SopDocument] = []
    if not SOPS_DIR.exists():
        return docs
    for layer in LAYERS:
        layer_dir = SOPS_DIR / layer
        if not layer_dir.exists():
            continue
        for f in sorted(layer_dir.glob("*.md")):
            body = f.read_text()
            steps = _extract_steps(body)
            docs.append(SopDocument(name=f.stem, layer=layer, path=f, body=body, steps=steps))
    return docs


def find(name_or_keyword: str) -> SopDocument | None:
    key = name_or_keyword.lower()
    docs = load_all()
    for d in docs:
        if d.name.lower() == key or key in d.name.lower() or key in d.layer:
            return d
    for d in docs:
        if key in d.intent.lower():
            return d
    return None


def _extract_steps(body: str) -> list[str]:
    """Extract numbered/§/### steps from a SOP markdown body."""
    steps: list[str] = []
    for m in re.finditer(r"^#{2,4}\s+(?:§\s*)?(?:\d+[\.\)]?\s*[—-]?\s*)?(.+)$", body, re.M):
        title = m.group(1).strip()
        if title and title.lower() not in ("intent", "severity levels", "response steps"):
            steps.append(title)
    if not steps:
        for m in re.finditer(r"^\s*[-*]\s+(.+)$", body, re.M):
            steps.append(m.group(1).strip())
    return steps[:25]


# ── Ship command builder (repo doctrine) ───────────────────────

def _pkg_scripts(cwd: Path) -> dict[str, str]:
    for p in (cwd / "package.json", cwd / "apps" / "sophia-ai-factory" / "package.json"):
        if p.exists():
            try:
                data = json.loads(p.read_text())
                return data.get("scripts", {})
            except Exception:
                continue
    return {}


def _find_deploy_doc(cwd: Path) -> Path | None:
    for name in ("CLAUDE.deploy.md", "CLAUDE.deploy.md"):
        p = cwd / name
        if p.exists():
            return p
    for g in ("docs/deploy*.md", "CLAUDE.deploy.md", ".claude/CLAUDE.deploy.md"):
        hits = list(cwd.glob(g))
        if hits:
            return hits[0]
    # also check apps/<app>/CLAUDE.deploy.md
    for p in (cwd / "apps" / "sophia-ai-factory" / "CLAUDE.deploy.md",):
        if p.exists():
            return p
    return None


def build_ship_commands(cwd: Path) -> list[tuple[str, str, str]]:
    """Return [(desc, command, verify)] based on repo doctrine."""
    steps: list[tuple[str, str, str]] = []
    scripts = _pkg_scripts(cwd)
    deploy_key = next(
        (k for k in ("deploy:full", "deploy", "deploy:prod") if k in scripts), None
    )
    deploy_script = scripts.get(deploy_key) if deploy_key else None
    smoke_url = ""

    doc = _find_deploy_doc(cwd)
    if doc:
        text = doc.read_text()[:4000]
        m = re.search(r"https?://[^\s\)]+", text)
        if m:
            smoke_url = m.group(0).rstrip(".,;")

    # 1) commit (if dirty)
    steps.append((
        "Commit changes",
        "git add -A && git commit -m 'chore: orchestrate pipeline ship' || echo 'nothing to commit'",
        "",
    ))
    # 2) push
    steps.append(("Push", "git push 2>&1 || echo 'no upstream'", ""))
    # 3) deploy (repo doctrine)
    if deploy_key:
        steps.append((f"Deploy: {deploy_key}", f"npm run {deploy_key} 2>&1", "live SHA == local SHA"))
    elif doc:
        steps.append(("Deploy (doctrine doc)", f"cat {doc} | grep -iE 'deploy|wrangler|pnpm' | head -5", ""))
    else:
        steps.append(("Build", "npm run build 2>&1 || pnpm run build 2>&1", "build exit 0"))
    # 4) smoke
    if smoke_url:
        steps.append((f"Smoke {smoke_url}", f"curl -s -m 20 -o /dev/null -w '%{{http_code}}' {smoke_url}", "HTTP 200"))
    else:
        steps.append(("Smoke (local)", "curl -s -m 10 -o /dev/null -w '%{http_code}' http://localhost:3000", "HTTP 200 (if server)"))

    return steps
