# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Packaging & Distribution Bridge for Mekong CLI × Antigravity.

Provides standard-library-only release packaging, asset bundling (skills, subagents,
hooks, and MCP servers), Homebrew formula generation, and multi-stage Docker
synthesizers.

STRICT INVARIANT: Provider-neutral and standard-library-only. Zero external vendor
SDKs or heavy third-party packages (complies with tests/test_core_boundary.py).
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import shutil
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


@dataclass
class PackageMetadata:
    """Parsed package specification and release metadata."""

    name: str = "mekong-cli"
    version: str = "6.0.0"
    description: str = "AI-operated business platform with PEV Engine"
    authors: List[str] = field(default_factory=lambda: ["Binh Phap Venture Studio <admin@binhphap.io>"])
    license: str = "MIT"
    homepage: str = "https://github.com/minhlongs/mekong-cli"
    repository: str = "https://github.com/minhlongs/mekong-cli"
    entry_point: str = "mekong = src.main:app"
    python_requires: str = ">=3.9,<3.15"

    def to_dict(self) -> dict[str, Any]:
        """Convert metadata to dictionary."""
        return asdict(self)


@dataclass
class DistributionArtifact:
    """Represents a generated release artifact with cryptographic checksum."""

    artifact_type: str  # "homebrew_formula", "dockerfile", "docker_compose", "manifest", "asset_archive"
    file_path: str
    sha256: str
    size_bytes: int
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Convert artifact to dictionary."""
        return {
            "artifact_type": self.artifact_type,
            "file_path": self.file_path,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "created_at": self.created_at,
        }


@dataclass
class PackagingReport:
    """Summary report of distribution packaging build."""

    project_root: str
    version: str
    artifacts: List[DistributionArtifact] = field(default_factory=list)
    skills_bundled: int = 0
    subagents_bundled: int = 0
    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "project_root": self.project_root,
            "version": self.version,
            "artifacts": [a.to_dict() for a in self.artifacts],
            "skills_bundled": self.skills_bundled,
            "subagents_bundled": self.subagents_bundled,
            "is_valid": self.is_valid,
            "errors": self.errors,
            "created_at": self.created_at,
        }


def _sha256_of_file(path: Path) -> str:
    """Compute SHA-256 hash of a file using standard library hashlib."""
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
        """Parse release metadata from pyproject.toml using standard library regex."""
        pyproject_path = self.project_root / "pyproject.toml"
        meta = PackageMetadata()
        if not pyproject_path.exists():
            return meta

        try:
            content = pyproject_path.read_text(encoding="utf-8")

            # Extract name
            m_name = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
            if m_name:
                meta.name = m_name.group(1).strip()

            # Extract version
            m_ver = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
            if m_ver:
                meta.version = m_ver.group(1).strip()

            # Extract description
            m_desc = re.search(r'description\s*=\s*["\']([^"\']+)["\']', content)
            if m_desc:
                meta.description = m_desc.group(1).strip()

            # Extract license
            m_lic = re.search(r'license\s*=\s*["\']([^"\']+)["\']', content)
            if m_lic:
                meta.license = m_lic.group(1).strip()

            # Extract homepage
            m_hp = re.search(r'homepage\s*=\s*["\']([^"\']+)["\']', content)
            if m_hp:
                meta.homepage = m_hp.group(1).strip()

            # Extract repository
            m_repo = re.search(r'repository\s*=\s*["\']([^"\']+)["\']', content)
            if m_repo:
                meta.repository = m_repo.group(1).strip()

            # Extract entry point from [tool.poetry.scripts]
            m_ep = re.search(r'mekong\s*=\s*["\']([^"\']+)["\']', content)
            if m_ep:
                meta.entry_point = f"mekong = {m_ep.group(1).strip()}"

            # Extract python dependency
            m_py = re.search(r'python\s*=\s*["\']([^"\']+)["\']', content)
            if m_py:
                meta.python_requires = m_py.group(1).strip()

        except Exception as exc:
            logger.warning(f"Error parsing pyproject.toml: {exc}")

        return meta

    def validate_metadata(self) -> Tuple[bool, List[str]]:
        """Validate PEP 517/621 compliance and required repository files."""
        errors: List[str] = []
        meta = self.read_metadata()

        if not meta.name:
            errors.append("Package name is missing")
        if not meta.version:
            errors.append("Package version is missing")
        elif not re.match(r"^\d+\.\d+\.\d+", meta.version):
            errors.append(f"Invalid semantic version: {meta.version}")

        # Check entrypoint
        if "mekong" not in meta.entry_point:
            errors.append("Entry point 'mekong' not defined in pyproject.toml scripts")

        # Check README and LICENSE
        if not (self.project_root / "README.md").exists():
            errors.append("README.md missing from repository root")
        if not (self.project_root / "LICENSE").exists() and not (self.project_root / "LICENSE.md").exists():
            errors.append("LICENSE file missing from repository root")

        return len(errors) == 0, errors

    def bundle_antigravity_assets(self, output_dir: Path) -> dict[str, int]:
        """Bundle skills, subagents, and hooks into output directory and return counts."""
        skills_dir = self.project_root / ".agents" / "skills"
        subagents_dir = self.project_root / ".agents" / "subagents"
        hooks_file = self.project_root / ".agents" / "hooks.json"

        target_agents_dir = output_dir / ".agents"
        target_agents_dir.mkdir(parents=True, exist_ok=True)

        skills_count = 0
        if skills_dir.exists():
            target_skills = target_agents_dir / "skills"
            target_skills.mkdir(parents=True, exist_ok=True)
            for skill_dir in skills_dir.iterdir():
                if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                    skills_count += 1
                    dest = target_skills / skill_dir.name
                    dest.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(skill_dir / "SKILL.md", dest / "SKILL.md")

        subagents_count = 0
        if subagents_dir.exists():
            target_subagents = target_agents_dir / "subagents"
            target_subagents.mkdir(parents=True, exist_ok=True)
            for agent_file in subagents_dir.iterdir():
                if agent_file.is_file() and agent_file.name.endswith(".json"):
                    subagents_count += 1
                    shutil.copy2(agent_file, target_subagents / agent_file.name)

        if hooks_file.exists():
            shutil.copy2(hooks_file, target_agents_dir / "hooks.json")

        return {
            "skills_bundled": skills_count,
            "subagents_bundled": subagents_count,
        }

    def generate_homebrew_formula(
        self,
        output_path: Path,
        tarball_url: Optional[str] = None,
        sha256_hash: Optional[str] = None,
    ) -> DistributionArtifact:
        """Synthesize official Homebrew formula (Formula/mekong.rb)."""
        meta = self.read_metadata()
        url = tarball_url or f"https://github.com/minhlongs/mekong-cli/archive/refs/tags/v{meta.version}.tar.gz"
        sha = sha256_hash or "0000000000000000000000000000000000000000000000000000000000000000"

        formula_content = f"""# Documentation: https://docs.brew.sh/Formula-Cookbook
#                https://rubydoc.brew.sh/Formula
class Mekong < Formula
  include Language::Python::Virtualenv

  desc "{meta.description}"
  homepage "{meta.homepage}"
  url "{url}"
  sha256 "{sha}"
  license "{meta.license}"
  head "{meta.repository}.git", branch: "main"

  depends_on "python@3.11"

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match "Mekong CLI", shell_output("#{{bin}}/mekong --help")
  end
end
"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(formula_content, encoding="utf-8")

        return DistributionArtifact(
            artifact_type="homebrew_formula",
            file_path=str(output_path),
            sha256=_sha256_of_file(output_path),
            size_bytes=output_path.stat().st_size,
        )

    def generate_docker_assets(self, output_dir: Path) -> List[DistributionArtifact]:
        """Synthesize minimal, production-grade Dockerfile and docker-compose.yml."""
        meta = self.read_metadata()
        output_dir.mkdir(parents=True, exist_ok=True)

        dockerfile_path = output_dir / "Dockerfile"
        compose_path = output_dir / "docker-compose.yml"

        dockerfile_content = f"""# syntax=docker/dockerfile:1
# Mekong CLI & Production Gateway Standalone Container
# Multi-stage build for minimal container footprint.

FROM python:3.11-slim AS builder

WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --no-cache-dir poetry && poetry export -f requirements.txt --output requirements.txt --without-hashes

FROM python:3.11-slim AS runtime

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \\
    PYTHONDONTWRITEBYTECODE=1 \\
    MEKONG_GATEWAY_HOST=0.0.0.0 \\
    MEKONG_GATEWAY_PORT=8080

RUN apt-get update && apt-get install -y --no-install-recommends git curl && rm -rf /var/lib/apt/lists/*

COPY --from=builder /build/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY .agents/ ./.agents/
COPY scripts/ ./scripts/
COPY pyproject.toml README.md LICENSE ./
RUN pip install --no-deps -e .

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \\
  CMD curl -f http://localhost:8080/health || exit 1

ENTRYPOINT ["mekong"]
CMD ["gateway", "--host", "0.0.0.0", "--port", "8080"]
"""
        dockerfile_path.write_text(dockerfile_content, encoding="utf-8")

        compose_content = """version: '3.8'

services:
  mekong-gateway:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: mekong-gateway
    restart: unless-stopped
    ports:
      - "8080:8080"
    environment:
      - MEKONG_GATEWAY_HOST=0.0.0.0
      - MEKONG_GATEWAY_PORT=8080
    volumes:
      - mekong-data:/app/.mekong

volumes:
  mekong-data:
"""
        compose_path.write_text(compose_content, encoding="utf-8")

        return [
            DistributionArtifact(
                artifact_type="dockerfile",
                file_path=str(dockerfile_path),
                sha256=_sha256_of_file(dockerfile_path),
                size_bytes=dockerfile_path.stat().st_size,
            ),
            DistributionArtifact(
                artifact_type="docker_compose",
                file_path=str(compose_path),
                sha256=_sha256_of_file(compose_path),
                size_bytes=compose_path.stat().st_size,
            ),
        ]

    def build_distribution_package(
        self,
        target: str = "all",
        output_dir: Optional[Path] = None,
    ) -> PackagingReport:
        """Run complete packaging build for specified target ('pypi', 'homebrew', 'docker', 'all')."""
        out_dir = Path(output_dir or (self.project_root / "dist")).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

        meta = self.read_metadata()
        is_valid, validation_errors = self.validate_metadata()

        report = PackagingReport(
            project_root=str(self.project_root),
            version=meta.version,
            is_valid=is_valid,
            errors=validation_errors,
        )

        # 1. Bundle assets
        bundle_stats = self.bundle_antigravity_assets(out_dir)
        report.skills_bundled = bundle_stats["skills_bundled"]
        report.subagents_bundled = bundle_stats["subagents_bundled"]

        # 2. Build Homebrew formula
        if target in ("all", "homebrew"):
            formula_file = out_dir / "Formula" / "mekong.rb"
            formula_art = self.generate_homebrew_formula(formula_file)
            report.artifacts.append(formula_art)

        # 3. Build Docker assets
        if target in ("all", "docker"):
            docker_artifacts = self.generate_docker_assets(out_dir)
            report.artifacts.extend(docker_artifacts)

        # 4. Generate manifest.json
        manifest_path = out_dir / "manifest.json"
        manifest_data = {
            "name": meta.name,
            "version": meta.version,
            "created_at": time.time(),
            "skills_bundled": report.skills_bundled,
            "subagents_bundled": report.subagents_bundled,
            "artifacts": [a.to_dict() for a in report.artifacts],
        }
        manifest_path.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")
        manifest_art = DistributionArtifact(
            artifact_type="manifest",
            file_path=str(manifest_path),
            sha256=_sha256_of_file(manifest_path),
            size_bytes=manifest_path.stat().st_size,
        )
        report.artifacts.append(manifest_art)

        return report
