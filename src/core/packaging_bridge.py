# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Packaging & Distribution Bridge for Mekong CLI × Antigravity.

STRICT INVARIANT: Provider-neutral and standard-library-only.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import shutil
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class PackageMetadata:
    name: str = "mekong-cli"; version: str = "6.0.0"; description: str = "AI-operated business platform with PEV Engine"  # noqa: E702
    authors: List[str] = field(default_factory=lambda: ["Binh Phap Venture Studio <admin@binhphap.io>"])
    license: str = "MIT"; homepage: str = "https://github.com/minhlongs/mekong-cli"  # noqa: E702
    repository: str = "https://github.com/minhlongs/mekong-cli"; entry_point: str = "mekong = src.main:app"  # noqa: E702
    python_requires: str = ">=3.9,<3.15"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DistributionArtifact:
    artifact_type: str; file_path: str; sha256: str; size_bytes: int; created_at: float = field(default_factory=time.time)  # noqa: E702

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PackagingReport:
    project_root: str; version: str; artifacts: List[DistributionArtifact] = field(default_factory=list)  # noqa: E702
    skills_bundled: int = 0; subagents_bundled: int = 0; is_valid: bool = True  # noqa: E702
    errors: List[str] = field(default_factory=list); created_at: float = field(default_factory=time.time)  # noqa: E702

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_root": self.project_root, "version": self.version,
            "artifacts": [a.to_dict() for a in self.artifacts], "skills_bundled": self.skills_bundled,
            "subagents_bundled": self.subagents_bundled, "is_valid": self.is_valid,
            "errors": self.errors, "created_at": self.created_at,
        }


def _sha256_of_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class PackagingBridge:
    """Coordinates release packaging, artifact generation, and integrity verification."""

    def __init__(self, project_root: Optional[Path] = None) -> None:
        self.project_root = Path(project_root or Path.cwd()).resolve()

    def read_metadata(self) -> PackageMetadata:
        pyproject_path = self.project_root / "pyproject.toml"
        meta = PackageMetadata()
        if not pyproject_path.exists():
            return meta
        try:
            content = pyproject_path.read_text(encoding="utf-8")
            for attr, key in (("name", "name"), ("version", "version"), ("description", "description"), ("license", "license"), ("homepage", "homepage"), ("repository", "repository"), ("python_requires", "python")):
                if m := re.search(rf'{key}\s*=\s*["\']([^"\']+)["\']', content):
                    setattr(meta, attr, m.group(1).strip())
            if m_ep := re.search(r'mekong\s*=\s*["\']([^"\']+)["\']', content):
                meta.entry_point = f"mekong = {m_ep.group(1).strip()}"
        except Exception as exc:
            logger.warning("Error parsing pyproject.toml: %s", exc)
        return meta

    def validate_metadata(self) -> Tuple[bool, List[str]]:
        errors: List[str] = []
        meta = self.read_metadata()
        if not meta.name:
            errors.append("Package name is missing")
        if not meta.version:
            errors.append("Package version is missing")
        elif not re.match(r"^\d+\.\d+\.\d+", meta.version):
            errors.append(f"Invalid semantic version: {meta.version}")
        if "mekong" not in meta.entry_point:
            errors.append("Entry point 'mekong' not defined in pyproject.toml scripts")
        if not (self.project_root / "README.md").exists():
            errors.append("README.md missing from repository root")
        if not (self.project_root / "LICENSE").exists() and not (self.project_root / "LICENSE.md").exists():
            errors.append("LICENSE file missing from repository root")
        return len(errors) == 0, errors

    def bundle_antigravity_assets(self, output_dir: Path) -> dict[str, int]:
        skills_dir = self.project_root / ".agents" / "skills"
        subagents_dir = self.project_root / ".agents" / "subagents"
        hooks_file = self.project_root / ".agents" / "hooks.json"
        target_agents = output_dir / ".agents"
        target_agents.mkdir(parents=True, exist_ok=True)
        skills_count = subagents_count = 0
        if skills_dir.exists():
            ts = target_agents / "skills"
            ts.mkdir(parents=True, exist_ok=True)
            for sd in skills_dir.iterdir():
                if sd.is_dir() and (sd / "SKILL.md").exists():
                    skills_count += 1
                    (ts / sd.name).mkdir(parents=True, exist_ok=True)
                    shutil.copy2(sd / "SKILL.md", ts / sd.name / "SKILL.md")
        if subagents_dir.exists():
            tsa = target_agents / "subagents"
            tsa.mkdir(parents=True, exist_ok=True)
            for af in subagents_dir.iterdir():
                if af.is_file() and af.name.endswith(".json"):
                    subagents_count += 1
                    shutil.copy2(af, tsa / af.name)
        if hooks_file.exists():
            shutil.copy2(hooks_file, target_agents / "hooks.json")
        return {"skills_bundled": skills_count, "subagents_bundled": subagents_count}

    def generate_homebrew_formula(self, output_path: Path, tarball_url: Optional[str] = None, sha256_hash: Optional[str] = None) -> DistributionArtifact:
        meta = self.read_metadata()
        url = tarball_url or f"https://github.com/minhlongs/mekong-cli/archive/refs/tags/v{meta.version}.tar.gz"
        sha = sha256_hash or ("0" * 64)
        formula = f'class Mekong < Formula\n  include Language::Python::Virtualenv\n  desc "{meta.description}"\n  homepage "{meta.homepage}"\n  url "{url}"\n  sha256 "{sha}"\n  license "{meta.license}"\n  head "{meta.repository}.git", branch: "main"\n  depends_on "python@3.11"\n  def install\n    virtualenv_install_with_resources\n  end\n  test do\n    assert_match "Mekong CLI", shell_output("#{{bin}}/mekong --help")\n  end\nend\n'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(formula, encoding="utf-8")
        return DistributionArtifact("homebrew_formula", str(output_path), _sha256_of_file(output_path), output_path.stat().st_size)

    def generate_docker_assets(self, output_dir: Path) -> List[DistributionArtifact]:
        output_dir.mkdir(parents=True, exist_ok=True)
        df, cp = output_dir / "Dockerfile", output_dir / "docker-compose.yml"
        df.write_text('FROM python:3.11-slim AS builder\nWORKDIR /build\nRUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev && rm -rf /var/lib/apt/lists/*\nCOPY pyproject.toml ./\nRUN pip install --no-cache-dir poetry && poetry export -f requirements.txt --output requirements.txt --without-hashes\nFROM python:3.11-slim AS runtime\nWORKDIR /app\nENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 MEKONG_GATEWAY_HOST=0.0.0.0 MEKONG_GATEWAY_PORT=8080\nRUN apt-get update && apt-get install -y --no-install-recommends git curl && rm -rf /var/lib/apt/lists/*\nCOPY --from=builder /build/requirements.txt ./\nRUN pip install --no-cache-dir -r requirements.txt\nCOPY src/ ./src/\nCOPY .agents/ ./.agents/\nCOPY scripts/ ./scripts/\nCOPY pyproject.toml README.md LICENSE ./\nRUN pip install --no-deps -e .\nEXPOSE 8080\nHEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 CMD curl -f http://localhost:8080/health || exit 1\nENTRYPOINT ["mekong"]\nCMD ["gateway", "--host", "0.0.0.0", "--port", "8080"]\n', encoding="utf-8")
        cp.write_text("version: '3.8'\nservices:\n  mekong-gateway:\n    build:\n      context: .\n      dockerfile: Dockerfile\n    container_name: mekong-gateway\n    restart: unless-stopped\n    ports:\n      - \"8080:8080\"\n    environment:\n      - MEKONG_GATEWAY_HOST=0.0.0.0\n      - MEKONG_GATEWAY_PORT=8080\n    volumes:\n      - mekong-data:/app/.mekong\nvolumes:\n  mekong-data:\n", encoding="utf-8")
        return [DistributionArtifact("dockerfile", str(df), _sha256_of_file(df), df.stat().st_size), DistributionArtifact("docker_compose", str(cp), _sha256_of_file(cp), cp.stat().st_size)]

    def build_distribution_package(self, target: str = "all", output_dir: Optional[Path] = None) -> PackagingReport:
        out_dir = Path(output_dir or (self.project_root / "dist")).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        meta = self.read_metadata()
        is_valid, validation_errors = self.validate_metadata()
        stats = self.bundle_antigravity_assets(out_dir)
        report = PackagingReport(str(self.project_root), meta.version, [], stats["skills_bundled"], stats["subagents_bundled"], is_valid, validation_errors)
        if target in ("all", "homebrew"):
            report.artifacts.append(self.generate_homebrew_formula(out_dir / "Formula" / "mekong.rb"))
        if target in ("all", "docker"):
            report.artifacts.extend(self.generate_docker_assets(out_dir))
        manifest_path = out_dir / "manifest.json"
        manifest_path.write_text(json.dumps({"name": meta.name, "version": meta.version, "created_at": time.time(), "skills_bundled": report.skills_bundled, "subagents_bundled": report.subagents_bundled, "artifacts": [a.to_dict() for a in report.artifacts]}, indent=2), encoding="utf-8")
        report.artifacts.append(DistributionArtifact("manifest", str(manifest_path), _sha256_of_file(manifest_path), manifest_path.stat().st_size))
        return report
