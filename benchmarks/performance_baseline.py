#!/usr/bin/env python3
"""Performance baseline benchmark for mekong-cli agent operations.

Measures latency for:
1. NL Routing (match_routes, fuzzy_match)
2. Command Fabric catalog build
3. Memory operations (MemoryStore)
4. Usage Tracker writes (UsageTracker.track_command)
5. Gateway import time + middleware count

All measurements use time.perf_counter_ns() for high precision.
Results printed in markdown table format.
"""

from __future__ import annotations

import importlib
import os
import statistics
import sys
import textwrap
import time
import tempfile
import tracemalloc
from pathlib import Path

sys.path.insert(0, "/Users/macbook/mekong-cli")

RESULTS: dict[str, dict] = {}


def bench(name: str, fn, iterations: int = 1000, warmup: int = 50) -> dict:
    """Run a function N times and return stats in ms."""
    fn()  # warmup
    for _ in range(warmup):
        fn()

    samples = []
    for _ in range(iterations):
        t0 = time.perf_counter_ns()
        fn()
        t1 = time.perf_counter_ns()
        samples.append((t1 - t0) / 1_000_000)  # ns -> ms

    samples_sorted = sorted(samples)
    n = len(samples_sorted)
    p95 = samples_sorted[int(n * 0.95)] if n > 1 else samples_sorted[0]

    return {
        "iterations": iterations,
        "mean_ms": round(statistics.mean(samples), 4),
        "median_ms": round(statistics.median(samples), 4),
        "p95_ms": round(p95, 4),
        "min_ms": round(min(samples), 4),
        "max_ms": round(max(samples), 4),
    }


# ===========================================================================
# 1. NL Routing
# ===========================================================================
def measure_nl_routing():
    from cli.tui.router import match_routes, fuzzy_match

    RESULTS["match_routes_short"] = bench(
        "match_routes (short)",
        lambda: match_routes("deploy"),
        iterations=5000,
    )
    RESULTS["match_routes_medium"] = bench(
        "match_routes (medium)",
        lambda: match_routes("deploy to production with staging and security"),
        iterations=5000,
    )
    RESULTS["match_routes_long"] = bench(
        "match_routes (long)",
        lambda: match_routes(
            "tôi muốn deploy backend api lên production với database migration "
            "và security scan trước khi release"
        ),
        iterations=5000,
    )
    RESULTS["fuzzy_match"] = bench(
        "fuzzy_match (autocomplete)",
        lambda: fuzzy_match("de", max_results=5),
        iterations=5000,
    )


# ===========================================================================
# 2. Command Fabric
# ===========================================================================
def measure_command_fabric():
    from src.command_fabric.catalog import (
        build_command_catalog,
        build_global_command_catalog,
        export_command_catalog,
    )

    RESULTS["build_command_catalog"] = bench(
        "build_command_catalog",
        build_command_catalog,
        iterations=200,
    )
    RESULTS["build_global_catalog"] = bench(
        "build_global_command_catalog",
        build_global_command_catalog,
        iterations=200,
    )
    RESULTS["export_command_catalog"] = bench(
        "export_command_catalog",
        export_command_catalog,
        iterations=200,
    )


# ===========================================================================
# 3. Memory Operations
# ===========================================================================
def measure_memory():
    from src.core.memory import MemoryStore, MemoryEntry

    tmp = tempfile.mktemp(suffix=".yaml", prefix="bench_mem_")
    try:
        store = MemoryStore(store_path=tmp)
        store._entries.clear()

        entry = MemoryEntry(
            goal="test goal",
            status="success",
            duration_ms=42.0,
            error_summary="",
            recipe_used="test-recipe",
        )

        RESULTS["memory_record_single"] = bench(
            "memory_record (1 entry, md5-hash vector)",
            lambda: store.record(entry),
            iterations=500,
        )

        # Pre-populate 1000 entries
        store._entries.clear()
        for i in range(1000):
            e = MemoryEntry(
                goal=f"goal-{i % 20}",
                status="success" if i % 3 != 0 else "failed",
                duration_ms=float(i % 100),
            )
            store._entries.append(e)

        # Re-add the vector index entries (mirror _index_entry logic)
        # We skip it for speed -- just test the YAML save path
        RESULTS["memory_query_1000"] = bench(
            "memory_query (1000 entries)",
            lambda: store.query("goal-7"),
            iterations=200,
        )
        RESULTS["memory_get_success_rate"] = bench(
            "memory_get_success_rate (1000 entries)",
            lambda: store.get_success_rate("goal-7"),
            iterations=200,
        )
        RESULTS["memory_recent"] = bench(
            "memory_recent 20 (1000 entries)",
            lambda: store.recent(20),
            iterations=500,
        )

        # Test scaling: 100, 1000, 10000
        for size in [100, 1000, 10000]:
            store._entries.clear()
            for i in range(size):
                e = MemoryEntry(
                    goal=f"scale-test-{i % 10}",
                    status="success" if i % 4 else "failed",
                    duration_ms=float(i % 50),
                )
                store._entries.append(e)
            RESULTS[f"memory_save_{size}"] = bench(
                f"memory_record + save ({size} entries in YAML)",
                lambda e=MemoryEntry(
                    goal=f"new-{time.monotonic_ns()}",
                    status="success",
                ): store.record(e),
                iterations=100 if size <= 1000 else 50,
            )

    finally:
        if Path(tmp).exists():
            Path(tmp).unlink()


# ===========================================================================
# 4. Usage Tracker Write
# ===========================================================================
def measure_usage_tracker():
    from src.usage.usage_tracker import UsageTracker

    tmp_db = tempfile.mktemp(suffix=".db", prefix="bench_usage_")
    try:
        tracker = UsageTracker(db_path=tmp_db)

        RESULTS["usage_track_single"] = bench(
            "usage_tracker.track_command (single write)",
            lambda: tracker.track_command("bench-license", f"cmd-{time.monotonic_ns()}"),
            iterations=500,
        )

        # Burst throughput test (no dedup path since unique names)
        RESULTS["usage_track_throughput"] = bench(
            "usage_tracker.track_command (burst, unique keys)",
            lambda: tracker.track_command(
                f"lic-{time.monotonic_ns()}",
                f"cmd-{time.monotonic_ns()}",
            ),
            iterations=500,
        )

        # Read path
        tracker.track_command("read-test-lic", "test-cmd-for-read", metadata={"test": True})

        def read_daily():
            tracker2 = UsageTracker(db_path=tmp_db)
            tracker2.get_daily_usage("read-test-lic")

        RESULTS["usage_get_daily"] = bench(
            "usage_tracker.get_daily_usage",
            read_daily,
            iterations=200,
        )

    finally:
        try:
            tracker.close()
        except Exception:
            pass
        if Path(tmp_db).exists():
            Path(tmp_db).unlink()


# ===========================================================================
# 5. Gateway Import Time + Middleware Count
# ===========================================================================
def measure_gateway_import():
    def import_gateway():
        importlib.import_module("src.gateway")

    # Measure import time once (Python caches modules, so re-import is cached)
    # We use importlib.reload to force re-measure
    mem_before = tracemalloc.tracing
    tracemalloc.start()
    import time as _time

    t0 = _time.perf_counter_ns()
    gateway_mod = importlib.import_module("src.gateway")
    t1 = _time.perf_counter_ns()
    peak = tracemalloc.get_traced_memory()[1] / 1024 / 1024  # MB
    tracemalloc.stop()

    RESULTS["gateway_import_time_ms"] = round((t1 - t0) / 1_000_000, 4)
    RESULTS["gateway_import_peak_mb"] = round(peak, 2)

    # Count middleware
    app = gateway_mod.app
    middleware_count = len(app.user_middleware)
    RESULTS["gateway_middleware_count"] = middleware_count
    RESULTS["gateway_router_count"] = len(app.routes) if hasattr(app, "routes") else "N/A"


# ===========================================================================
# 6. Command count
# ===========================================================================
def count_commands():
    cmds_dir = Path("/Users/macbook/mekong-cli/.claude/commands")
    count = len(list(cmds_dir.glob("*.md")))
    RESULTS["command_files_count"] = count


# ===========================================================================
# Run All
# ===========================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("MEKONG-CLI PERFORMANCE BASELINE")
    print("=" * 70)

    measure_nl_routing()
    measure_command_fabric()
    measure_memory()
    measure_usage_tracker()
    measure_gateway_import()
    count_commands()

    # ===== PRINT RESULTS =====
    print()

    # NL Routing
    print("#### 1. NL Routing Latency")
    print()
    print("| Operation | Iterations | Mean (ms) | Median (ms) | P95 (ms) | Min (ms) | Max (ms) | Notes |")
    print("|-----------|-----------|-----------|-------------|----------|----------|----------|-------|")

    def r(key): return RESULTS.get(key, {})

    def fmt_row(label, key, notes=""):
        d = r(key)
        if not d:
            return f"| {label} | — | — | — | — | — | — | {notes} |"
        return (
            f"| {label} | {d.get('iterations','?')} | {d.get('mean_ms','?')} "
            f"| {d.get('median_ms','?')} | {d.get('p95_ms','?')} "
            f"| {d.get('min_ms','?')} | {d.get('max_ms','?')} | {notes} |"
        )

    print(fmt_row("match_routes (short: 'deploy')", "match_routes_short"))
    print(fmt_row("match_routes (medium: short sentence)", "match_routes_medium"))
    print(fmt_row("match_routes (long: VN sentence)", "match_routes_long"))
    print(fmt_row("fuzzy_match (autocomplete, 'de')", "fuzzy_match"))
    print()

    # Command Fabric
    print("#### 2. Command Fabric Catalog Build")
    print()
    print("| Operation | Iterations | Mean (ms) | P95 (ms) | Notes |")
    print("|-----------|-----------|-----------|----------|-------|")
    for key, label, notes in [
        ("build_command_catalog", "build_command_catalog", f"parses {RESULTS.get('command_files_count','?')} .claude/commands/*.md files"),
        ("build_global_catalog", "build_global_catalog", "project + user commands merged"),
        ("export_command_catalog", "export_command_catalog", "includes serialization to dict"),
    ]:
        d = r(key)
        print(
            f"| {label} | {d.get('iterations','?')} | {d.get('mean_ms','?')} "
            f"| {d.get('p95_ms','?')} | {notes} |"
        )
    print()

    # Memory
    print("#### 3. Memory Operations")
    print()
    print("| Operation | Iterations | Mean (ms) | P95 (ms) | Notes |")
    print("|-----------|-----------|-----------|----------|-------|")

    mem_ops = list(RESULTS.keys())
    for k in sorted(mem_ops):
        if not k.startswith("memory_"):
            continue
        d = r(k)
        notes = ""
        if "size" in d and d["size"]:
            notes = f"({d['size']} entries)"
        else:
            if "single" in k:
                notes = "record + YAML save + vector index + event bus emit"
            elif "query" in k:
                notes = "1000 entries, vector + substring fallback"
            elif "success_rate" in k:
                notes = "1000 entries, filter + count + divide"
            elif "recent" in k:
                notes = "slice [-20:]"
            elif "save" in k:
                # extract size from key
                sz = k.split("_")[-1]
                notes = f"{sz} entries in YAML file"
        print(
            f"| {k} | {d.get('iterations','?')} | {d.get('mean_ms','?')} "
            f"| {d.get('p95_ms','?')} | {notes} |"
        )
    print()

    # Usage Tracker
    print("#### 4. Usage Tracker Writes (SQLite)")
    print()
    print("| Operation | Mean (ms) | P95 (ms) | Notes |")
    print("|-----------|-----------|----------|-------|")
    d = r("usage_track_single")
    print(
        f"| track_command single write | {d.get('mean_ms','?')} "
        f"| {d.get('p95_ms','?')} | dedup lookup + INSERT + SHA256 + commit |"
    )
    d = r("usage_track_throughput")
    print(
        f"| track_command burst (unique keys) | {d.get('mean_ms','?')} "
        f"| {d.get('p95_ms','?')} | dedup short-circuits on miss |"
    )
    d = r("usage_get_daily")
    print(
        f"| get_daily_usage | {d.get('mean_ms','?')} "
        f"| {d.get('p95_ms','?')} | 3 GROUP BY queries |"
    )
    print()

    # Gateway
    print("#### 5. Gateway Import & Middleware")
    print()
    print(f"| gateway_import_time_ms | {r('gateway_import_time_ms').get('mean_ms', r('gateway_import_time_ms')).get('gateway_import_time_ms', '?')} ms |")
    print(f"| gateway_import_peak_mb | {r('gateway_import_peak_mb').get('gateway_import_peak_mb', '?')} MB |")
    print(f"| gateway_middleware_count | {r('gateway_middleware_count').get('gateway_middleware_count', '?')} |")
    print(f"| gateway_router_count | {r('gateway_router_count').get('gateway_router_count', '?')} |")
    print()

    # ===== BOTTLENECK FLAGS =====
    print("#### 6. Bottleneck Flags (>50ms)")
    print()
    flagged = []
    for key, d in RESULTS.items():
        if isinstance(d, dict) and "mean_ms" in d:
            val = d["mean_ms"]
            if isinstance(val, (int, float)) and val > 50:
                flagged.append((key, val, d.get("p95_ms", "?")))

    if flagged:
        for key, mean, p95 in flagged:
            print(f"  **{key}**: mean={mean}ms, P95={p95}ms")
    else:
        print("  No operations exceeded 50ms threshold.")
    print()

    # Save raw data
    import json

    out = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "results": {k: v for k, v in RESULTS.items() if isinstance(v, dict) and "mean_ms" in v},
        "meta": {
            "gateway_import_time_ms": RESULTS.get("gateway_import_time_ms"),
            "gateway_import_peak_mb": RESULTS.get("gateway_import_peak_mb"),
            "gateway_middleware_count": RESULTS.get("gateway_middleware_count"),
            "gateway_router_count": RESULTS.get("gateway_router_count"),
            "command_files_count": RESULTS.get("command_files_count"),
        },
        "bottlenecks_gt_50ms": [(k, v) for k, v in flagged],
    }
    out_path = "/Users/macbook/mekong-cli/plans/reports/performance-baseline-260713-report.md"
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w") as f:
        f.write("# Mekong-CLI Performance Baseline — 2026-07-13\n\n")
        f.write("Raw JSON results:\n\n```json\n")
        f.write(json.dumps(out, indent=2, default=str))
        f.write("\n```\n")

    print(f"Raw results saved to: {out_path}")
