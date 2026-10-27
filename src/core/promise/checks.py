# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Business postcondition evaluator.

A postcondition answers the founder's third question — *"was the business
condition actually met?"* — which is strictly stronger than *"the handler
ran"* and independent from *"the artifact digest matches"*.

Checks are declarative (data authored next to the operation contract) so they
can be listed in the claim ledger and diffed in CI. Nothing here trusts the
handler's own ``status`` field: every check re-measures the outcome from the
payload, the engine's own database, or the filesystem.
"""

from __future__ import annotations

import dataclasses
import importlib
import json
import pathlib
import re
import sqlite3
import typing

PLACEHOLDER_RE = re.compile(r"^\{(params|result)\.([A-Za-z0-9_.\[\]]+)\}$")


@dataclasses.dataclass
class CheckContext:
    """Everything a postcondition is allowed to look at."""

    params: dict[str, typing.Any]
    result: dict[str, typing.Any]
    engine: typing.Any = None
    engine_db_path: str | None = None
    workspace_root: pathlib.Path | None = None
    run_id: str = ""
    workspace_id: str = ""


@dataclasses.dataclass(frozen=True)
class CheckResult:
    """Outcome of one postcondition."""

    check: str
    status: str  # PASSED | FAILED | SKIPPED
    detail: str = ""
    measured: typing.Mapping[str, typing.Any] = dataclasses.field(default_factory=dict)
    required: bool = True

    def to_dict(self) -> dict[str, typing.Any]:
        return dataclasses.asdict(self)


def resolve_path(obj: typing.Any, path: str) -> typing.Any:
    """Resolve ``a.b[0].c`` against nested dicts/lists. Returns ``None`` if absent."""
    cur: typing.Any = obj
    for token in re.findall(r"[^.\[\]]+|\[\d+\]", path):
        if cur is None:
            return None
        if token.startswith("[") and token.endswith("]"):
            idx = int(token[1:-1])
            if not isinstance(cur, (list, tuple)) or idx >= len(cur):
                return None
            cur = cur[idx]
        else:
            if isinstance(cur, dict):
                cur = cur.get(token)
            else:
                cur = getattr(cur, token, None)
    return cur


def _resolve_placeholders(value: typing.Any, ctx: CheckContext) -> typing.Any:
    if isinstance(value, str):
        match = PLACEHOLDER_RE.match(value.strip())
        if match:
            source = ctx.params if match.group(1) == "params" else ctx.result
            return resolve_path(source, match.group(2))
        # Embedded placeholder inside a larger string (e.g. table name suffix).
        def _sub(m: re.Match[str]) -> str:
            source = ctx.params if m.group(1) == "params" else ctx.result
            return str(resolve_path(source, m.group(2)))

        return re.sub(r"\{(params|result)\.([A-Za-z0-9_.\[\]]+)\}", _sub, value)
    if isinstance(value, dict):
        return {k: _resolve_placeholders(v, ctx) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_placeholders(v, ctx) for v in value]
    return value


def _to_number(value: typing.Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(",", "").replace(" ", ""))
        except ValueError:
            return None
    return None


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_output_fields(ctx: CheckContext, params: dict[str, typing.Any]) -> CheckResult:
    required = [str(p) for p in params.get("required", [])]
    non_empty = [str(p) for p in params.get("non_empty", [])]
    missing = [p for p in required if resolve_path(ctx.result, p) is None]
    empty = [
        p
        for p in non_empty
        if resolve_path(ctx.result, p) in (None, "", [], {}, 0)
    ]
    if missing or empty:
        return CheckResult(
            "output_fields",
            "FAILED",
            f"missing={missing} empty={empty}",
            {"missing": missing, "empty": empty},
        )
    return CheckResult("output_fields", "PASSED", "required output fields present",
                       {"checked": required + non_empty})


def check_echoes_input(ctx: CheckContext, params: dict[str, typing.Any]) -> CheckResult:
    """Prove the payload was derived from *this* input (defeats canned samples)."""
    pairs = params.get("pairs") or []
    if not pairs and params.get("result_path"):
        pairs = [{"result_path": params["result_path"], "param_path": params.get("param_path")}]
    mismatches: list[dict[str, typing.Any]] = []
    checked = 0
    for pair in pairs:
        r_path = str(pair.get("result_path", ""))
        p_path = pair.get("param_path")
        expected = resolve_path(ctx.params, str(p_path)) if p_path else pair.get("value")
        actual = resolve_path(ctx.result, r_path)
        checked += 1
        if expected is None:
            continue
        if _to_number(expected) is not None and _to_number(actual) is not None:
            if abs(float(_to_number(expected) or 0) - float(_to_number(actual) or 0)) > float(
                pair.get("tolerance", 0)
            ):
                mismatches.append({"result_path": r_path, "expected": expected, "actual": actual})
        elif str(actual) != str(expected):
            mismatches.append({"result_path": r_path, "expected": expected, "actual": actual})
    if mismatches:
        return CheckResult("echoes_input", "FAILED",
                           "output does not reflect the submitted input",
                           {"mismatches": mismatches})
    return CheckResult("echoes_input", "PASSED", f"{checked} input/output linkage(s) verified",
                       {"checked": checked})


def check_numeric_identity(ctx: CheckContext, params: dict[str, typing.Any]) -> CheckResult:
    left = _to_number(resolve_path(ctx.result, str(params.get("left", ""))))
    right_paths = [str(p) for p in params.get("right", [])]
    tolerance = float(params.get("tolerance", 1))
    if left is None:
        return CheckResult("numeric_identity", "FAILED", f"left operand '{params.get('left')}' is not numeric")
    total = 0.0
    for rp in right_paths:
        val = _to_number(resolve_path(ctx.result, rp)) or _to_number(resolve_path(ctx.params, rp))
        if val is None:
            return CheckResult("numeric_identity", "FAILED", f"right operand '{rp}' is not numeric")
        total += val
    scale = float(params.get("scale", 1))
    if abs(left - total * scale) > tolerance:
        return CheckResult(
            "numeric_identity", "FAILED",
            f"{params.get('left')}={left} != sum({right_paths})={total} (scale={scale}, tol={tolerance})",
            {"left": left, "right_total": total},
        )
    return CheckResult("numeric_identity", "PASSED",
                       f"{params.get('left')} == sum({right_paths}) within {tolerance}",
                       {"left": left, "right_total": total})


def check_value_bounds(ctx: CheckContext, params: dict[str, typing.Any]) -> CheckResult:
    path = str(params.get("path", ""))
    value = _to_number(resolve_path(ctx.result, path))
    if value is None:
        return CheckResult("value_bounds", "FAILED", f"'{path}' is not numeric in the result")
    lo = params.get("min")
    hi = params.get("max")
    if lo is not None and value < float(_resolve_placeholders(lo, ctx)):  # type: ignore[arg-type]
        return CheckResult("value_bounds", "FAILED", f"{path}={value} below statutory minimum {lo}")
    if hi is not None and value > float(_resolve_placeholders(hi, ctx)):  # type: ignore[arg-type]
        return CheckResult("value_bounds", "FAILED", f"{path}={value} above statutory maximum {hi}")
    return CheckResult("value_bounds", "PASSED", f"{path}={value} within [{lo}, {hi}]",
                       {"value": value})


def check_enum_member(ctx: CheckContext, params: dict[str, typing.Any]) -> CheckResult:
    path = str(params.get("path", ""))
    allowed = list(params.get("allowed", []))
    actual = resolve_path(ctx.result, path)
    if actual not in allowed:
        return CheckResult("enum_member", "FAILED", f"{path}='{actual}' not in {allowed}")
    return CheckResult("enum_member", "PASSED", f"{path}='{actual}' is a legal value")


def check_record_persisted(ctx: CheckContext, params: dict[str, typing.Any]) -> CheckResult:
    """Prove the write really landed in the engine's own database."""
    db_path = params.get("db_path") or ctx.engine_db_path
    if not db_path:
        return CheckResult("record_persisted", "FAILED", "no database path available for the engine")
    table = str(params.get("table", ""))
    match = _resolve_placeholders(dict(params.get("match", {})), ctx)
    path = pathlib.Path(str(db_path))
    if not path.exists():
        return CheckResult("record_persisted", "FAILED", f"engine database '{path}' does not exist")
    where = " AND ".join(f"{col} = ?" for col in match) or "1"
    sql = f"SELECT COUNT(*) AS cnt FROM {table} WHERE {where}"
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            row = conn.execute(sql, [str(v) for v in match.values()]).fetchone()
        finally:
            conn.close()
    except sqlite3.Error as exc:
        return CheckResult("record_persisted", "FAILED", f"query error on {table}: {exc}")
    count = int(row[0]) if row else 0
    if count < int(params.get("min_rows", 1)):
        return CheckResult("record_persisted", "FAILED",
                           f"no row in {table} matching {match} (found {count})",
                           {"table": table, "match": match, "count": count})
    return CheckResult("record_persisted", "PASSED", f"{count} row(s) persisted in {table}",
                       {"table": table, "match": match, "count": count})


def check_artifact_written(ctx: CheckContext, params: dict[str, typing.Any]) -> CheckResult:
    """Prove a usable document artifact exists on disk with required content."""
    raw_path = _resolve_placeholders(str(params.get("path", "")), ctx)
    resolved = resolve_path(ctx.result, str(params.get("path_from_result", ""))) if params.get(
        "path_from_result"
    ) else None
    candidate = pathlib.Path(str(resolved or raw_path))
    if not candidate.is_absolute() and ctx.workspace_root:
        candidate = ctx.workspace_root / candidate
    if not candidate.exists():
        return CheckResult("artifact_written", "FAILED", f"artifact '{candidate}' was not written")
    size = candidate.stat().st_size
    min_bytes = int(params.get("min_bytes", 1))
    if size < min_bytes:
        return CheckResult("artifact_written", "FAILED",
                           f"artifact '{candidate.name}' is {size}B, expected >= {min_bytes}B")
    required_keys = [str(k) for k in params.get("required_keys", [])]
    if required_keys and candidate.suffix == ".json":
        try:
            payload = json.loads(candidate.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            return CheckResult("artifact_written", "FAILED", f"artifact is not valid JSON: {exc}")
        missing = [k for k in required_keys if resolve_path(payload, k) is None]
        if missing:
            return CheckResult("artifact_written", "FAILED", f"artifact JSON missing keys {missing}")
    required_text = [str(t) for t in params.get("required_text", [])]
    if required_text and candidate.suffix in {".md", ".txt", ".html", ".csv", ".json"}:
        body = candidate.read_text(encoding="utf-8", errors="replace")
        missing = [t for t in required_text if t not in body]
        if missing:
            return CheckResult("artifact_written", "FAILED", f"artifact text missing {missing}")
    return CheckResult("artifact_written", "PASSED", f"artifact '{candidate.name}' ({size}B) verified",
                       {"path": str(candidate), "bytes": size})


def check_provenance_recorded(ctx: CheckContext, params: dict[str, typing.Any]) -> CheckResult:
    """Research outputs must carry source, retrieval time and uncertainty."""
    base = str(params.get("path", ""))
    node = resolve_path(ctx.result, base) if base else ctx.result
    if not isinstance(node, dict):
        return CheckResult("provenance_recorded", "FAILED", f"'{base}' is not an object")
    required = [str(k) for k in params.get("required_keys", ["sources", "retrieved_at", "confidence"])]
    missing = [k for k in required if node.get(k) in (None, "", [], {})]
    if missing:
        return CheckResult("provenance_recorded", "FAILED", f"provenance fields missing: {missing}")
    verified_flag = params.get("verified_flag_key")
    if verified_flag and node.get(verified_flag) is True and not node.get("independent_confirmation"):
        return CheckResult(
            "provenance_recorded", "FAILED",
            "model-generated content is marked as verified fact without independent confirmation",
        )
    return CheckResult("provenance_recorded", "PASSED", "source/time/confidence recorded",
                       {"keys": required})


def check_custom(ctx: CheckContext, params: dict[str, typing.Any]) -> CheckResult:
    target = str(params.get("callable_path", ""))
    if ":" not in target:
        return CheckResult("custom", "FAILED", f"invalid callable_path '{target}'")
    module_name, func_name = target.split(":", 1)
    try:
        fn = getattr(importlib.import_module(module_name), func_name)
        outcome = fn(ctx, dict(params.get("args", {})))
    except Exception as exc:  # noqa: BLE001 — a broken check must never pass silently
        return CheckResult("custom", "FAILED", f"{target} raised {type(exc).__name__}: {exc}")
    if isinstance(outcome, CheckResult):
        return outcome
    if isinstance(outcome, dict):
        return CheckResult("custom", str(outcome.get("status", "FAILED")),
                           str(outcome.get("detail", "")), dict(outcome.get("measured", {})))
    return CheckResult("custom", "PASSED" if outcome else "FAILED", str(outcome))


CHECKS: dict[str, typing.Callable[[CheckContext, dict[str, typing.Any]], CheckResult]] = {
    "output_fields": check_output_fields,
    "echoes_input": check_echoes_input,
    "numeric_identity": check_numeric_identity,
    "value_bounds": check_value_bounds,
    "enum_member": check_enum_member,
    "record_persisted": check_record_persisted,
    "artifact_written": check_artifact_written,
    "provenance_recorded": check_provenance_recorded,
    "custom": check_custom,
}


def evaluate(
    postconditions: typing.Sequence[typing.Any],
    ctx: CheckContext,
) -> list[CheckResult]:
    """Run every declared postcondition and return honest results."""
    results: list[CheckResult] = []
    for post in postconditions:
        check_name = getattr(post, "check", None) or (post.get("check") if isinstance(post, dict) else None)
        check_params = getattr(post, "params", None)
        if check_params is None and isinstance(post, dict):
            check_params = post.get("params", {})
        required = bool(getattr(post, "required", True) if not isinstance(post, dict) else post.get("required", True))
        description = str(getattr(post, "description", "") if not isinstance(post, dict) else post.get("description", ""))
        fn = CHECKS.get(str(check_name))
        if fn is None:
            results.append(CheckResult(str(check_name), "FAILED",
                                       f"unknown postcondition check '{check_name}'", required=required))
            continue
        try:
            outcome = fn(ctx, dict(check_params or {}))
        except Exception as exc:  # noqa: BLE001
            outcome = CheckResult(str(check_name), "FAILED", f"{type(exc).__name__}: {exc}")
        results.append(
            dataclasses.replace(outcome, check=str(check_name), required=required)
            if description and not outcome.detail
            else outcome
        )
    return results


__all__ = [
    "CHECKS",
    "CheckContext",
    "CheckResult",
    "evaluate",
    "resolve_path",
]
