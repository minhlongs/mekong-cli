# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Core/adapter boundary gate — static analysis only (ast.parse, no imports).

Architecture rule: ``src/core/`` is provider-neutral. Vendor SDKs
(``anthropic``, ``openai``) must NEVER be imported from core — provider
access goes through ``llm_router_adapter`` wrapping ``llm_client``.

Generic HTTP libraries (``requests``/``httpx``) are permitted only in the
documented allowlist below; every entry is an HTTP client module talking to
an internal gateway or external service, not a provider SDK. Adding a new
HTTP-lib importer to core requires a documented entry here.

Also pins the Buzz seam: ``runtime_adapter.py`` may reference buzz ONLY via
a lazy import inside ``run_from_payload`` — never at module level.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = REPO_ROOT / "src" / "core"

VENDOR_SDKS = frozenset({"anthropic", "openai"})
HTTP_LIBS = frozenset({"requests", "httpx"})

# Documented allowlist for generic HTTP libs in src/core/ (repo-root-relative
# path -> reason). Verified by grep on 2026-08-26 at d6138541a + E1 changes.
HTTP_LIB_ALLOWLIST: dict[str, str] = {
    "src/core/llm_client.py": "transitional OpenRouter HTTP client, wrapped by llm_router_adapter; MOVE to src/providers/ deferred",
    "src/core/plugin_marketplace.py": "httpx client for the plugin marketplace API",
    "src/core/gateway/gateway_main.py": "httpx used by the in-process gateway app",
    "src/core/activation_sync.py": "requests client syncing activation state with the gateway",
    "src/core/agi_loop.py": "lazy requests import posting Telegram updates from the self-improvement loop",
    "src/core/executor.py": "lazy requests import executing API recipe steps (SSRF-guarded)",
    "src/core/gateway_api.py": "requests client for the public AgencyOS gateway API",
    "src/core/gateway_client/__init__.py": "requests-based gateway client package",
    "src/core/health_reporter.py": "requests client reporting health to the gateway",
    "src/core/image_generator.py": "requests client calling the DashScope/Qwen image endpoint",
    "src/core/memory_client.py": "requests client for the NeuralMemory service",
    "src/core/providers.py": "lazy httpx import probing the LiteLLM provider health endpoint",
    "src/core/raas_audit_logger.py": "requests client flushing audit records to the gateway",
    "src/core/raas_auth/__init__.py": "requests-based RaaS auth client package",
    "src/core/raas_auth/auth_gateway_mixin.py": "requests-based RaaS auth gateway mixin",
    "src/core/rate_limit_client.py": "requests client for the rate-limit service",
    "src/core/swarm.py": "requests client used by the swarm registry for remote agents",
    "src/core/telegram_client.py": "requests client for the Telegram Bot API",
    "src/core/telemetry_reporter.py": "lazy requests import flushing telemetry to the gateway",
}


def _core_python_files() -> list[Path]:
    return sorted(p for p in CORE_DIR.rglob("*.py"))


def _top_module(node: ast.Import | ast.ImportFrom) -> str | None:
    if isinstance(node, ast.Import):
        return node.names[0].name.split(".")[0]
    return (node.module or "").split(".")[0] or None


def _full_module(node: ast.Import | ast.ImportFrom) -> str:
    if isinstance(node, ast.Import):
        return node.names[0].name
    return node.module or ""


def _collect_imports(tree: ast.AST) -> list[tuple[int, str]]:
    """All (lineno, top-level module) pairs for Import/ImportFrom nodes."""
    out: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            module = _top_module(node)
            if module:
                out.append((node.lineno, module))
    return out


def _parse_all_core_files() -> dict[Path, ast.Module]:
    trees: dict[Path, ast.Module] = {}
    assert CORE_DIR.is_dir(), f"core directory missing: {CORE_DIR}"
    for path in _core_python_files():
        try:
            trees[path] = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            pytest.fail(f"src/core file does not parse: {path} ({exc})")
    assert trees, "no python files found under src/core/"
    return trees


def _rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


class TestVendorSdkBoundary:
    def test_no_vendor_sdk_imports_anywhere_in_core(self):
        violations: list[str] = []
        for path, tree in _parse_all_core_files().items():
            for lineno, module in _collect_imports(tree):
                if module in VENDOR_SDKS:
                    violations.append(f"{_rel(path)}:{lineno} imports '{module}'")
        assert not violations, (
            "src/core/ must stay provider-neutral — vendor SDK imports found:\n  "
            + "\n  ".join(violations)
            + "\nRoute provider access through llm_router_adapter/llm_client instead."
        )


class TestHttpLibAllowlist:
    def test_http_lib_imports_only_in_documented_allowlist(self):
        violations: list[str] = []
        for path, tree in _parse_all_core_files().items():
            rel = _rel(path)
            if rel in HTTP_LIB_ALLOWLIST:
                continue
            for lineno, module in _collect_imports(tree):
                if module in HTTP_LIBS:
                    violations.append(f"{rel}:{lineno} imports '{module}'")
        assert not violations, (
            "HTTP-lib import outside the documented allowlist:\n  "
            + "\n  ".join(violations)
            + "\nAdd a documented allowlist entry only if the module is a "
            "legitimate HTTP client; otherwise route through an adapter."
        )

    def test_allowlist_entries_exist_and_still_import_http_libs(self):
        trees = _parse_all_core_files()
        by_rel = {_rel(path): tree for path, tree in trees.items()}
        stale: list[str] = []
        for rel in HTTP_LIB_ALLOWLIST:
            tree = by_rel.get(rel)
            if tree is None:
                stale.append(f"{rel} (file no longer exists)")
                continue
            modules = {module for _, module in _collect_imports(tree)}
            if not modules & HTTP_LIBS:
                stale.append(f"{rel} (no longer imports requests/httpx)")
        assert not stale, (
            "Stale allowlist entries — remove them from this test:\n  "
            + "\n  ".join(stale)
        )


def _find_function(tree: ast.Module, name: str) -> ast.FunctionDef | None:
    """Find a function or method named `name` anywhere in the module tree."""
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name == name:
                    return child
        elif isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


class TestBuzzSeam:
    def test_buzz_import_is_lazy_inside_run_from_payload_only(self):
        path = CORE_DIR / "runtime_adapter.py"
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

        module_level = [
            node
            for node in tree.body
            if isinstance(node, (ast.Import, ast.ImportFrom))
            and _full_module(node).startswith("src.core.buzz")
        ]
        assert not module_level, (
            "buzz_adapter must not be imported at module level in runtime_adapter.py"
        )

        func = _find_function(tree, "run_from_payload")
        assert func is not None, "run_from_payload missing from runtime_adapter.py"

        lazy = [
            node
            for node in ast.walk(func)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            and _full_module(node).startswith("src.core.buzz")
        ]
        assert lazy, (
            "run_from_payload must lazily import buzz_adapter inside the function body"
        )

    def test_no_buzz_reference_outside_run_from_payload(self):
        path = CORE_DIR / "runtime_adapter.py"
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        sanctioned = _find_function(tree, "run_from_payload")
        assert sanctioned is not None

        leaks: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)) and _full_module(
                node
            ).startswith("src.core.buzz"):
                if any(node.lineno >= n.lineno and node.end_lineno <= n.end_lineno
                       for n in [sanctioned] if n.end_lineno):
                    continue
                owner = "<module>"
                for top in tree.body:
                    if (
                        isinstance(top, (ast.ClassDef, ast.FunctionDef))
                        and top.lineno <= node.lineno
                        and (top.end_lineno or 0) >= node.lineno
                    ):
                        owner = f"{type(top).__name__}:{top.name}"
                        break
                leaks.append(f"{owner} line {node.lineno}")
        assert not leaks, (
            "buzz import found outside run_from_payload:\n  " + "\n  ".join(leaks)
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
