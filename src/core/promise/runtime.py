# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Handler resolution and execution for capability operations.

The runtime is deliberately boring: import the module named in the contract,
build the engine (with a workspace-scoped database when the contract asks for
one), map validated parameters onto the real method, call it, and normalise the
result. Nothing here fabricates an outcome — if the module, class or method is
missing the operation reports ``HANDLER_UNRESOLVED`` and the run fails.
"""

from __future__ import annotations

import dataclasses
import importlib
import inspect
import pathlib
import time
import typing

from src.core.promise.contracts import HandlerRef, OperationSpec


class HandlerResolutionError(RuntimeError):
    """Raised when a contract points at code that does not exist."""


@dataclasses.dataclass(frozen=True)
class HandlerContext:
    """Injected into handlers that declare a ``context`` parameter.

    Gives an operation the workspace-scoped services it needs to record real
    business facts (revenue reconciliation, deployment proofs, attestations)
    without inventing its own persistence path.
    """

    run_id: str
    workspace_id: str
    principal_id: str
    workspace_root: pathlib.Path
    state_dir: pathlib.Path
    params: dict[str, typing.Any]
    engine_db_path: str | None = None

    def evidence_store(self) -> typing.Any:
        from src.core.promise.evidence import EvidenceStore

        return EvidenceStore(self.state_dir / "promise_evidence.db")


@dataclasses.dataclass
class HandlerOutcome:
    """What the runtime observed while executing one operation."""

    handler_ran: bool
    payload: dict[str, typing.Any]
    error: str | None = None
    error_code: str | None = None
    engine: typing.Any = None
    engine_db_path: str | None = None
    duration_ms: int = 0
    handler_ref: str = ""
    artifacts: list[str] = dataclasses.field(default_factory=list)


def _plain(value: typing.Any) -> typing.Any:
    """Convert engine return values into JSON-safe primitives."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return _plain(dataclasses.asdict(value))
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    if isinstance(value, (set, frozenset)):
        return sorted(_plain(v) for v in value)
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, "value") and hasattr(value, "name"):  # Enum
        return str(value.value)
    for converter in ("to_dict", "as_dict", "_asdict", "model_dump"):
        fn = getattr(value, converter, None)
        if callable(fn):
            try:
                return _plain(fn())
            except Exception:  # noqa: BLE001 — fall through to str()
                break
    return str(value)


def workspace_db_path(spec: OperationSpec, workspace_root: pathlib.Path, workspace_id: str) -> str:
    """Per-workspace database location, so tenants never share a ledger file."""
    declared = ""
    for effect in spec.effects:
        if effect.startswith("WRITE:"):
            declared = effect.split(":", 1)[1]
            break
    if not declared:
        declared = f".mekong/workspaces/{workspace_id}/{spec.command}.db"
    path = pathlib.Path(declared)
    if not path.is_absolute():
        path = workspace_root / path
    if "{workspace_id}" in str(path):
        path = pathlib.Path(str(path).replace("{workspace_id}", workspace_id))
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)


def resolve_callable(ref: HandlerRef) -> tuple[typing.Any, typing.Any]:
    """Return ``(instance_or_none, callable)`` for a handler reference."""
    if ref.callable_path:
        module_name, func_name = ref.callable_path.split(":", 1)
        try:
            module = importlib.import_module(module_name)
            fn = getattr(module, func_name)
        except (ImportError, AttributeError) as exc:
            raise HandlerResolutionError(f"{ref.describe()} could not be imported: {exc}") from exc
        return None, fn

    try:
        module = importlib.import_module(ref.module)
    except ImportError as exc:
        raise HandlerResolutionError(f"module '{ref.module}' not importable: {exc}") from exc

    factory: typing.Any = None
    if ref.factory:
        factory = getattr(module, ref.factory, None)
        if factory is None:
            raise HandlerResolutionError(f"class '{ref.factory}' not found in '{ref.module}'")
        method = getattr(factory, ref.method, None)
        if method is None:
            raise HandlerResolutionError(f"method '{ref.factory}.{ref.method}' not found in '{ref.module}'")
        return factory, method

    fn = getattr(module, ref.method, None)
    if fn is None:
        raise HandlerResolutionError(f"function '{ref.method}' not found in '{ref.module}'")
    return None, fn


def build_engine(
    ref: HandlerRef,
    factory: typing.Any,
    params: dict[str, typing.Any],
    *,
    db_path: str | None = None,
) -> tuple[typing.Any, str | None]:
    """Instantiate the engine, injecting the workspace database when declared."""
    if factory is None:
        return None, None
    kwargs: dict[str, typing.Any] = dict(ref.constructor_kwargs)
    for param_name, kwarg_name in ref.constructor_param_map.items():
        if param_name in params:
            kwargs[kwarg_name] = params[param_name]
    used_db: str | None = None
    try:
        signature = inspect.signature(factory.__init__)
    except (TypeError, ValueError):  # pragma: no cover — exotic factories
        signature = None
    if db_path is not None and signature is not None and "db_path" in signature.parameters:
        kwargs.setdefault("db_path", db_path)
        used_db = str(kwargs["db_path"])
    elif db_path is not None and signature is not None and "db_file" in signature.parameters:
        kwargs.setdefault("db_file", db_path)
        used_db = str(kwargs["db_file"])
    try:
        return factory(**kwargs), used_db
    except TypeError as exc:
        raise HandlerResolutionError(f"{factory.__name__} could not be constructed: {exc}") from exc


def map_arguments(
    ref: HandlerRef,
    method: typing.Any,
    params: dict[str, typing.Any],
) -> dict[str, typing.Any]:
    """Map validated operation params onto the real method's keyword arguments."""
    try:
        signature = inspect.signature(method)
    except (TypeError, ValueError):  # pragma: no cover
        return dict(params)
    accepts_kwargs = any(
        p.kind == inspect.Parameter.VAR_KEYWORD for p in signature.parameters.values()
    )
    known = {
        name
        for name, p in signature.parameters.items()
        if p.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
    }
    mapped: dict[str, typing.Any] = {}
    for key, value in params.items():
        target = ref.param_map.get(key, key)
        if target in known or accepts_kwargs:
            mapped[target] = value
    return mapped


def execute(
    spec: OperationSpec,
    params: dict[str, typing.Any],
    *,
    workspace_root: pathlib.Path,
    workspace_id: str,
    state_dir: pathlib.Path | None = None,
    run_id: str = "",
    principal_id: str = "",
) -> HandlerOutcome:
    """Run one operation contract and report exactly what happened."""
    started = time.monotonic_ns()
    ref = spec.handler
    db_path: str | None = None
    if spec.writes_workspace or ref.constructor_param_map or "db_path" in ref.constructor_kwargs:
        db_path = workspace_db_path(spec, workspace_root, workspace_id)

    try:
        factory, method = resolve_callable(ref)
    except HandlerResolutionError as exc:
        return HandlerOutcome(False, {"status": "FAILED", "error": str(exc)}, error=str(exc),
                              error_code="HANDLER_UNRESOLVED", handler_ref=ref.describe(),
                              duration_ms=_elapsed_ms(started))

    engine: typing.Any = None
    engine_db: str | None = None
    try:
        engine, engine_db = build_engine(ref, factory, params, db_path=db_path)
        if engine is not None:
            bound = getattr(engine, ref.method)
        else:
            bound = method
        target = bound if engine is not None else method
        arguments = map_arguments(ref, target, params)
        arguments = _inject_context(target, arguments, spec, params, workspace_root,
                                    workspace_id, state_dir, run_id, principal_id,
                                    engine_db_path=db_path)
        raw = target(**arguments)
    except HandlerResolutionError as exc:
        return HandlerOutcome(False, {"status": "FAILED", "error": str(exc)}, error=str(exc),
                              error_code="HANDLER_UNRESOLVED", engine=engine,
                              engine_db_path=engine_db or db_path, handler_ref=ref.describe(),
                              duration_ms=_elapsed_ms(started))
    except TypeError as exc:
        return HandlerOutcome(False, {"status": "FAILED", "error": str(exc)}, error=str(exc),
                              error_code="HANDLER_ARGUMENT_MISMATCH", engine=engine,
                              engine_db_path=engine_db or db_path, handler_ref=ref.describe(),
                              duration_ms=_elapsed_ms(started))
    except Exception as exc:  # noqa: BLE001 — real failures must surface honestly
        return HandlerOutcome(
            True,
            {"status": "FAILED", "error": f"{type(exc).__name__}: {exc}"},
            error=f"{type(exc).__name__}: {exc}",
            error_code="HANDLER_EXCEPTION",
            engine=engine,
            engine_db_path=engine_db or db_path,
            handler_ref=ref.describe(),
            duration_ms=_elapsed_ms(started),
        )

    payload = _plain(raw)
    if not isinstance(payload, dict):
        payload = {"result": payload}
    artifacts = _collect_artifacts(payload, workspace_root)
    return HandlerOutcome(
        True, payload, engine=engine, engine_db_path=engine_db or db_path,
        duration_ms=_elapsed_ms(started), handler_ref=ref.describe(), artifacts=artifacts,
    )


def _collect_artifacts(payload: dict[str, typing.Any], workspace_root: pathlib.Path) -> list[str]:
    found: list[str] = []
    for key in ("artifact_path", "path", "output_path", "file", "document_path", "export_path"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            candidate = pathlib.Path(value)
            if not candidate.is_absolute():
                candidate = workspace_root / candidate
            if candidate.exists():
                found.append(str(candidate))
    return found


def _inject_context(
    target: typing.Any,
    arguments: dict[str, typing.Any],
    spec: OperationSpec,
    params: dict[str, typing.Any],
    workspace_root: pathlib.Path,
    workspace_id: str,
    state_dir: pathlib.Path | None,
    run_id: str,
    principal_id: str,
    engine_db_path: str | None = None,
) -> dict[str, typing.Any]:
    """Pass a :class:`HandlerContext` when the handler declares ``context``."""
    try:
        signature = inspect.signature(target)
    except (TypeError, ValueError):  # pragma: no cover
        return arguments
    if "context" not in signature.parameters:
        return arguments
    resolved_state = state_dir or (workspace_root / ".mekong")
    arguments = dict(arguments)
    arguments["context"] = HandlerContext(
        run_id=run_id, workspace_id=workspace_id, principal_id=principal_id,
        workspace_root=workspace_root, state_dir=pathlib.Path(resolved_state), params=dict(params),
        engine_db_path=engine_db_path,
    )
    _ = spec
    return arguments


def _elapsed_ms(started_ns: int) -> int:
    return (time.monotonic_ns() - started_ns) // 1_000_000


__all__ = [
    "HandlerContext",
    "HandlerOutcome",
    "HandlerResolutionError",
    "build_engine",
    "execute",
    "map_arguments",
    "resolve_callable",
    "workspace_db_path",
]
