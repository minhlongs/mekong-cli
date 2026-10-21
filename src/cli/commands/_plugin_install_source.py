# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Plugin source detection, fetching, and installation helpers."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path
from typing import Optional

from src.core.plugin_runtime import PluginRuntime


def _get_plugins_dir() -> Path:
    return Path.home() / ".mekong" / "plugins"


def _get_runtime(plugins_dir: Optional[Path] = None) -> PluginRuntime:
    import src.cli.commands.plugin_install as _mod

    target = plugins_dir or _mod._get_plugins_dir()
    return _mod.PluginRuntime(plugin_dirs=[target])


def _detect_source(source: str) -> tuple[str, str]:
    s = source.strip()
    if s.startswith("git+") or (
        "github.com" in s or "gitlab.com" in s or "bitbucket.org" in s
    ):
        return "git", s
    if s.startswith("https://") and s.endswith(".zip"):
        return "zip", s
    if s.startswith("https://"):
        return "git", s
    p = Path(s)
    if p.exists():
        return "local", s
    return "pypi", s


def _clone_git(url: str, dest: Path) -> Path:
    """Clone a git repo, stripping `git+` prefix if present."""
    import src.cli.commands.plugin_install as _mod

    repo_url = url.removeprefix("git+")
    clone_path = dest / "repo"
    _mod.console.print(f"[dim]Cloning {repo_url} ...[/dim]")
    _mod.subprocess.run(
        ["git", "clone", "--depth", "1", repo_url, str(clone_path)],
        check=True,
        capture_output=True,
    )
    return clone_path


def _fetch_zip(url: str, dest: Path) -> Path:
    import src.cli.commands.plugin_install as _mod

    url_hash = hashlib.sha256(url.encode()).hexdigest()[:8]
    extract_path = dest / f"zip-{url_hash}"
    if not extract_path.exists():
        extract_path.mkdir(parents=True, exist_ok=True)
    _mod.console.print(f"[dim]Fetching {url} ...[/dim]")
    with urllib.request.urlopen(url) as resp:  # noqa: S310
        data = resp.read()
    zip_path = dest / f"{url_hash}.zip"
    zip_path.write_bytes(data)
    shutil.unpack_archive(zip_path, extract_path)
    return extract_path


def _install_source(source: str, name: str, force: bool) -> dict:
    import src.cli.commands.plugin_install as _mod

    plugins_dir = _mod._get_plugins_dir()
    runtime = _mod._get_runtime(plugins_dir)
    plugins_dir.mkdir(parents=True, exist_ok=True)

    source_type, resolved = _mod._detect_source(source)

    with tempfile.TemporaryDirectory(prefix="mekong-install-") as tmp:
        tmp_path = Path(tmp)

        if source_type == "git":
            try:
                work_dir = _mod._clone_git(resolved, tmp_path)
            except subprocess.CalledProcessError as exc:
                err_msg = (
                    exc.stderr.decode(errors="replace") if exc.stderr else str(exc)
                )
                return {
                    "status": "error",
                    "source_type": "git",
                    "error_message": f"Git clone failed: {err_msg}",
                }
        elif source_type == "zip":
            try:
                work_dir = _mod._fetch_zip(resolved, tmp_path)
            except Exception as exc:  # noqa: BLE001
                return {
                    "status": "error",
                    "source_type": "zip",
                    "error_message": f"ZIP fetch failed: {exc}",
                }
        else:
            work_dir = Path(resolved)

        manifest = work_dir / ".plugin.json"
        if not manifest.is_file():
            return {
                "status": "error",
                "source_type": source_type,
                "error_message": f"No .plugin.json found in {work_dir}",
            }

        temps = list(work_dir.iterdir())
        plugin_src = work_dir
        if len(temps) == 1 and temps[0].is_dir():
            plugin_src = temps[0]

        return runtime.install(
            plugin_src,
            name=name or "",
            force=force,
        )
