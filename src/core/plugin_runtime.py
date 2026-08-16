# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Plugin Runtime — bridges SDK lifecycle into CLI runtime.

Discovers ``.plugin.json`` manifests, instantiates plugins via the SDK
``create_plugin()`` factory (with legacy ``register()`` fallback), runs
lifecycle (initialize → start), and exposes registry entries for Typer
wiring and hook dispatch.

Isolation boundary
-------------------
SDK (``packages/mekong-plugin-sdk/``) — contract-only, no runtime.
This module — runtime: discovery + instantiation + lifecycle.
CLI (``src/cli/plugin_integration.py``) — wires commands into Typer.
"""

from __future__ import annotations

import importlib.metadata
import importlib.util
import logging
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Public result types
# ---------------------------------------------------------------------------

@dataclass
class PluginInfo:
    """Lightweight summary returned by PluginRuntime.load_plugin()."""

    plugin_id: str = ""
    name: str = ""
    version: str = ""
    status: str = "loaded"
    plugin_type: Optional[str] = None
    description: str = ""
    source: str = ""
    error_message: str = ""


@dataclass
class LoadedPlugin:
    """Internal record for a fully-instantiated plugin inside the runtime."""

    plugin_id: str
    manifest: Any  # PluginManifestSchema
    instance: Any  # MekongPlugin subclass instance
    commands: List[Any] = field(default_factory=list)  # SDK Command[]
    hooks: List[Any] = field(default_factory=list)  # SDK Hook[]
    source: str = ""


# ---------------------------------------------------------------------------
# Runtime
# ---------------------------------------------------------------------------

class PluginRuntime:
    """Discover, instantiate, and lifecycle-manage Mekong CLI plugins.

    Parameters
    ----------
    plugin_dirs:
        Filesystem directories to scan for ``.plugin.json`` plugins.
    """

    def __init__(self, plugin_dirs: Optional[List[Path]] = None) -> None:
        self.plugin_dirs: List[Path] = [
            (d if isinstance(d, Path) else Path(d))
            for d in (plugin_dirs or [Path.home() / ".mekong" / "plugins"])
        ]
        self._loaded: Dict[str, LoadedPlugin] = {}

    # ---- discovery ---------------------------------------------------------

    def discover_manifests(self) -> List[Path]:
        """Return paths to every ``.plugin.json`` found under *plugin_dirs*.

        Walks depth-1: ``<plugin_dir>/*/.plugin.json``.
        """
        found: List[Path] = []
        for base in self.plugin_dirs:
            if not base.is_dir():
                continue
            for child in sorted(base.iterdir()):
                pj = child / ".plugin.json"
                if pj.is_file():
                    found.append(pj)
        return found

    # ---- load single -------------------------------------------------------

    def load_plugin(self, manifest_path: Path) -> PluginInfo:
        """Read, validate, instantiate, and lifecycle-start one plugin.

        Returns a **PluginInfo** summary regardless of outcome.
        The plugin is also registered internally (``_loaded``) on success.

        Raises nothing — all errors are captured in the returned PluginInfo.
        """
        info = PluginInfo(source=str(manifest_path))

        # -- read + validate manifest ----------------------------------------
        try:
            from src.core.plugin_schema import PluginManifestSchema
            schema = PluginManifestSchema.from_file(manifest_path)
        except Exception as exc:
            info.error_message = f"manifest_error: {exc}"
            info.status = "error"
            logger.warning("Plugin manifest invalid at %s: %s", manifest_path, exc)
            return info

        info.plugin_id = schema.id
        info.name = schema.name
        info.version = schema.version
        info.plugin_type = _extract_type_from_id(schema.id)
        info.description = schema.description or ""
        info.source = str(manifest_path)

        # -- instantiate plugin instance -------------------------------------
        try:
            from packages.mekong_plugin_sdk.plugin import create_plugin
            from packages.mekong_plugin_sdk.context import PluginContext

            plugin_dir = manifest_path.parent
            _plugin_name = schema.name or schema.id

            context = PluginContext(
                plugin_id=schema.id,
                manifest=schema,
                config_dir=plugin_dir,
                storage_dir=Path.home() / ".mekong" / "storage" / schema.id.replace("/", "_"),
                cache_dir=Path.home() / ".mekong" / "cache" / schema.id.replace("/", "_"),
                data_dir=plugin_dir,
                logger=logging.getLogger(f"mekong.plugin.{schema.id}"),
            )

            instance = create_plugin(context)
            instance.initialize(context)
            instance.start()

            commands = list(instance.get_commands())
            instance.register_commands(_noop_registry(commands))

            from packages.mekong_plugin_sdk.hooks import HookRegistry, HookPoint

            hook_registry = HookRegistry()
            hook_registry.initialize(schema.id)
            instance.register_hooks(hook_registry)
            captured_hooks: List[Any] = []
            for point in HookPoint:
                captured_hooks.extend(hook_registry.get_hooks(point))


            if schema.id in self._loaded:
                logger.warning(
                    "Duplicate plugin id '%s' â overwriting previous instance",
                    schema.id,
                )
            self._loaded[schema.id] = LoadedPlugin(
                plugin_id=schema.id,
                manifest=schema,
                instance=instance,
                commands=commands,
                hooks=captured_hooks,
                source=str(manifest_path),
            )
            info.status = "loaded"

        except TypeError as exc:
            if "missing" in str(exc).lower() or "required" in str(exc).lower():
                # SDK factory failed — try legacy register() pattern -------------
                try:
                    loaded = self._load_via_legacy(manifest_path, schema)
                    if loaded:
                        self._loaded[schema.id] = loaded
                        info.status = "loaded"
                        info.plugin_type = loaded.source.split("/")[-1]
                        return info
                except Exception as exc2:
                    info.error_message = f"legacy_load_error: {exc2}"
                    info.status = "error"
                    return info
            info.error_message = f"instantiation_error: {exc}"
            info.status = "error"

        except Exception as exc:
            info.error_message = f"lifecycle_error: {exc}"
            info.status = "error"

        return info

    # ---- load all ----------------------------------------------------------

    def load_all(self) -> List[PluginInfo]:
        """Discover and load every plugin under all *plugin_dirs*.

        Also loads plugin-type entry-points exposed via ``pyproject.toml``.
        Returns a list of **PluginInfo** (one per attempted plugin).
        """
        results: List[PluginInfo] = []

        # -- filesystem .plugin.json plugins ----------------------------------
        for manifest_path in self.discover_manifests():
            logger.info("Loading plugin from %s", manifest_path)
            results.append(self.load_plugin(manifest_path))

        # -- entry-point plugins (optional complement) ------------------------
        eps = self._load_entry_point_plugins()
        results.extend(eps)

        if hasattr(self, "_enabled_plugins"):
            self._enabled_plugins = {
                pid: lp.plugin_id
                for pid, lp in self._loaded.items()
                if lp.plugin_id
            }

        return results

    # ---- unload / shutdown ------------------------------------------------

    def unload_all(self) -> None:
        """Call ``stop()`` then ``dispose()`` on every loaded plugin."""
        for loaded in self._loaded.values():
            try:
                loaded.instance.stop()
                loaded.instance.dispose()
            except Exception as exc:
                logger.warning("Error unloading %s: %s", loaded.plugin_id, exc)
        self._loaded.clear()

    # ---- access ------------------------------------------------------------

    def get_loaded(self, plugin_id: str) -> Optional[LoadedPlugin]:
        """Return the internal record for *plugin_id*, or ``None``."""
        return self._loaded.get(plugin_id)

    def iter_loaded(self):
        yield from self._loaded.values()

    @property
    def loaded_plugins(self) -> List[str]:
        return list(self._loaded.keys())

    # ---- install -----------------------------------------------------------

    def install(
        self,
        source: Union[str, Path],
        name: str = "",
        force: bool = False,
        *,
        _plugins_dir: Optional[Path] = None,
        _progress_callback=None,
    ) -> Dict[str, Any]:
        """Install a plugin from a local path, git URL, ZIP URL, or PyPI pkg.

        Returns a dict with keys: status, plugin_id, install_name, source_type, error_message.
        On success, status == ``installed`` and the plugin dir is present under the first *plugin_dirs* entry.
        """
        result: Dict[str, Any] = {
            "status": "error",
            "plugin_id": "",
            "install_name": "",
            "source_type": "",
            "error_message": "",
        }

        try:
            source_type, resolved = _detect_source_type(source)
            if source_type == "unknown":
                result["error_message"] = f"Unrecognised source: {source!r}"
                return result
            result["source_type"] = source_type

            target_dir = _resolve_or_clone(source_type, resolved)
            manifest_path = target_dir / ".plugin.json"

            if not manifest_path.is_file():
                result["error_message"] = f"No .plugin.json in {source_type} source"
                shutil.rmtree(target_dir, ignore_errors=True)
                return result

            schema = _load_manifest_safe(manifest_path)
            if schema is None:
                result["error_message"] = "Invalid .plugin.json (schema validation failed)"
                shutil.rmtree(target_dir, ignore_errors=True)
                return result

            result["plugin_id"] = schema.id
            install_name = name if name else (schema.name or target_dir.name)
            install_slug = _slugify(install_name)

            dest_plugins = _plugins_dir or (
                self.plugin_dirs[0] if self.plugin_dirs else Path.home() / ".mekong" / "plugins"
            )
            if not isinstance(dest_plugins, Path):
                dest_plugins = Path(dest_plugins)

            dest_plugins.mkdir(parents=True, exist_ok=True)
            dest = dest_plugins / install_slug

            if dest.exists() and dest != target_dir:
                if not force:
                    result["error_message"] = (
                        f"'{install_slug}' already exists. Use --force to overwrite."
                    )
                    shutil.rmtree(target_dir, ignore_errors=True)
                    return result
                shutil.rmtree(dest, ignore_errors=True)

            if target_dir != dest:
                shutil.copytree(target_dir, dest)
                shutil.rmtree(target_dir, ignore_errors=True)

            result["status"] = "installed"
            result["install_name"] = install_slug

        except Exception as exc:
            result["error_message"] = str(exc)

        return result

    # ---- legacy fallback ---------------------------------------------------

    def _load_via_legacy(
        self, manifest_path: Path, schema
    ) -> Optional[LoadedPlugin]:
        """Fallback: import the legacy plugin module and call ``register()``."""
        plugin_dir = manifest_path.parent
        init_py = plugin_dir / "src" / "__init__.py"

        if not init_py.is_file():
            return None

        spec = importlib.util.spec_from_file_location(
            f"_legacy_plugin_{schema.id.replace('.', '_')}",
            init_py,
        )
        if spec is None or spec.loader is None:
            return None

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if not hasattr(module, "register"):
            return None

        registry_holder: Dict[str, Any] = {}
        module.register(registry_holder)

        commands = registry_holder.get("commands", [])
        hooks = registry_holder.get("hooks", [])

        return LoadedPlugin(
            plugin_id=schema.id,
            manifest=schema,
            instance=None,
            commands=list(commands),
            hooks=list(hooks),
            source="legacy",
        )

    # ---- entry-point discovery ---------------------------------------------

    def _load_entry_point_plugins(self) -> List[PluginInfo]:
        """Load plugins registered as console-script entry points."""
        results: List[PluginInfo] = []
        groups = ("mekong.agents", "mekong.providers", "mekong.hooks", "mekong.recipes")
        for group in groups:
            try:
                eps = importlib.metadata.entry_points().select(group=group)
            except TypeError:
                eps = importlib.metadata.entry_points().get(group, [])
            for ep in eps:
                try:
                    fn = ep.load()
                    if callable(fn):
                        fn(self)
                    plugin_id = getattr(fn, "__mekong_plugin_id__", ep.name)
                    results.append(
                        PluginInfo(
                            plugin_id=plugin_id or ep.name,
                            name=ep.name,
                            version="0.0.0",
                            source=f"entry_point:{group}:{ep.name}",
                            status="loaded",
                        )
                    )
                except Exception as exc:
                    results.append(
                        PluginInfo(
                            plugin_id=ep.name,
                            name=ep.name,
                            version="0.0.0",
                            source=f"entry_point:{group}:{ep.name}",
                            status="error",
                            error_message=str(exc),
                        )
                    )
        return results


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _extract_type_from_id(plugin_id: str) -> Optional[str]:
    """Guess plugin type from the reverse-domain id (last segment).

    Examples::

        com.example.my-agent -> "agent"
        com.example.data-provider -> "provider"
        com.example.my-hook -> "hook"
        com.example.my-recipe -> "recipe"
        com.example.something -> None
    """
    slug = plugin_id.rsplit(".", 1)[-1].lower()
    for t in ("agent", "provider", "hook", "recipe"):
        if slug.endswith(f"-{t}"):
            return t
    return None


def _detect_source_type(source: Union[str, Path]) -> Tuple[str, Union[str, Path]]:
    """Return (type, resolved_value) for git/zip/local/pypi/unknown."""
    s = str(source)
    # zip — check before host-based git detection (zip URLs often on github)
    if s.endswith(".zip") or re.match(r"https?://.*\.zip(\?.*)?$", s):
        return "zip", s
    # git URL
    if s.startswith("git+") or re.match(r"https?://[^/]+/(.+?/|.+?)\.git$", s):
        return "git", s
    if re.match(r"https?://(github\.com|gitlab\.com|bitbucket\.org)/", s):
        if s.endswith(".git"):
            return "git", s
        # plain repo page — clone repo and find .plugin.json in first dir
        return "git_repo", s
    # pypi
    if re.match(r"^[a-z][a-z0-9_\-]*$", s) and not Path(s).exists():
        if s.startswith("mekong-plugin-") or s.startswith("mekong_plugin_"):
            return "pypi", s
    # local path
    p = Path(s)
    if p.exists():
        return "local", p
    # unknown
    return "unknown", source


def _resolve_or_clone(source_type: str, resolved: Union[str, Path]) -> Path:
    """Materialise the plugin source to a temp dir. Return its path."""
    tmp = Path(tempfile.mkdtemp(prefix="mekong-install-"))
    if source_type == "local":
        p = Path(resolved)
        if not p.exists():
            raise FileNotFoundError(f"Local path not found: {p}")
        dest = tmp / "src"
        shutil.copytree(p, dest)
        return dest
    if source_type in ("git", "git_repo"):
        url = str(resolved)
        # strip git+ prefix if present
        url = re.sub(r"^git\+", "", url)
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", url, str(tmp / "src")],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            # mask credentials in error
            safe_url = _mask_credentials(url)
            raise RuntimeError(
                f"git clone failed for {safe_url}: {exc.stderr or exc}"
            ) from exc
        return tmp / "src"
    if source_type == "zip":
        url = str(resolved)
        zip_path = tmp / "download.zip"
        try:
            _curl_download(url, zip_path)
            subprocess.run(
                ["unzip", "-q", str(zip_path), "-d", str(tmp / "src")],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"ZIP extraction failed: {exc}") from exc
        return tmp / "src"
    if source_type == "pypi":
     pkg = str(resolved)
     target = tmp / "src"
     target.mkdir(parents=True, exist_ok=True)
     try:
      subprocess.run(
       ["pipx", "install", "--pip-args", f"--target {target}", pkg],
       check=True,
       capture_output=True,
       text=True,
      )
     except FileNotFoundError:
      raise RuntimeError(
       "pipx is required for PyPI install. "
       f"Install it: pip install pipx. Or manually: pipx install {pkg}"
      ) from None
     except subprocess.CalledProcessError as exc:
      raise RuntimeError(
       f"PyPI install failed for {pkg}: {exc.stderr or exc}"
      ) from exc
     return target
    raise ValueError(f"Unsupported source_type: {source_type}")


def _load_manifest_safe(manifest_path: Path):
    """Load and validate .plugin.json; return schema or None on failure."""
    try:
        from src.core.plugin_schema import PluginManifestSchema
        return PluginManifestSchema.from_file(manifest_path)
    except Exception:
        return None


def _slugify(name: str) -> str:
    """Collapse a plugin name to a kebab-case directory slug."""
    return re.sub(r"[^a-z0-9-]+", "-", name.strip().lower()).strip("-")


def _curl_download(url: str, dest: Path, timeout: int = 60) -> None:
    """Download URL to dest using curl, masking credentials for logging."""
    try:
        subprocess.run(
            ["curl", "-fsSL", "--max-time", str(timeout), url, "-o", str(dest)],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"Download failed: {exc.stderr or exc}") from exc


def _mask_credentials(url: str) -> str:
    """Strip basic-auth credentials from a URL for safe logging."""
    return re.sub(r"https?://[^@]+@", "https://***@", url)


def _safe_cleanup(path: Path) -> None:
    """Remove a directory tree, ignoring errors."""
    shutil.rmtree(path, ignore_errors=True)


class _noop_registry:
    """Collector that satisfies register(context) calls."""

    def __init__(self, initial: Optional[List[Any]] = None) -> None:
        self._items: List[Any] = list(initial or [])

    def register(self, item: Any) -> None:
        self._items.append(item)

    @property
    def items(self) -> List[Any]:
        return list(self._items)
