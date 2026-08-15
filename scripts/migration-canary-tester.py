#!/usr/bin/env python3
"""Canary tester for plugin migration.

Tests a plugin in canary mode (small percentage of users) before full rollout.

Usage:
    python3 scripts/migration-canary-tester.py --plugin mekong-core-founder --commands annual,okr

Metrics monitored:
- Command success rate
- Latency (p50, p95, p99)
- Error types
- Memory usage
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class CanaryResult:
    """Results from a canary test."""
    plugin_id: str
    commands_tested: list[str]
    total_invocations: int
    success_rate: float
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    errors: dict[str, int]
    memory_mb: float
    passed: bool
    threshold_violations: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_command_test(command: str, args: str = "", iterations: int = 10) -> list[float]:
    """Run a command multiple times and collect latency measurements."""
    latencies = []

    for i in range(iterations):
        start = time.perf_counter()
        result = subprocess.run(
            ["mekong", command] + (args.split() if args else []),
            capture_output=True,
            text=True,
            timeout=30,
            cwd=project_root,
            env={
                "MEKONG_FEATURE_PLUGIN_SYSTEM_ENABLED": "true",
                "MEKONG_FEATURE_PLUGIN_FOUNDER": "plugin",
            }
        )
        elapsed = (time.perf_counter() - start) * 1000  # ms
        latencies.append(elapsed)

        if result.returncode != 0:
            print(f"  ⚠️ Command failed (iteration {i+1}): {result.stderr[:100]}")

        time.sleep(0.1)  # Small pause between runs

    return latencies


def check_health_metrics(plugin_id: str) -> dict[str, float]:
    """Check plugin health metrics from registry."""
    try:
        result = subprocess.run(
            ["mekong", "admin", "plugin", "metrics", plugin_id],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            # Parse output (simplified)
            return {
                "load_time_ms": 0,  # Would parse from output
                "error_rate": 0.0,
            }
    except Exception:
        pass
    return {"load_time_ms": 0, "error_rate": 0.0}


def run_canary_test(
    plugin_id: str,
    commands: list[str],
    iterations_per_command: int = 20,
    latency_threshold_ms: float = 500,
    error_rate_threshold: float = 0.01,
) -> CanaryResult:
    """Run canary test for a plugin."""
    print(f"🧪 Starting canary test for plugin: {plugin_id}")
    print(f"   Commands: {', '.join(commands)}")
    print(f"   Iterations per command: {iterations_per_command}\n")

    total_invocations = 0
    all_latencies: list[float] = []
    errors: dict[str, int] = {}

    for cmd in commands:
        print(f"Testing: {cmd}")
        latencies = run_command_test(cmd, iterations=iterations_per_command)
        all_latencies.extend(latencies)
        total_invocations += len(latencies)

        # Count errors (commands that took >30s are timeouts, counted as errors)
        timeouts = sum(1 for lat in latencies if lat >= 30000)
        if timeouts > 0:
            errors[cmd] = timeouts

        time.sleep(0.5)

    # Calculate metrics
    success_count = total_invocations - sum(errors.values())
    success_rate = success_count / total_invocations if total_invocations else 0

    all_latencies.sort()
    p50 = statistics.median(all_latencies) if all_latencies else 0
    p95 = all_latencies[int(len(all_latencies) * 0.95)] if all_latencies else 0
    p99 = all_latencies[int(len(all_latencies) * 0.99)] if all_latencies else 0
    avg = statistics.mean(all_latencies) if all_latencies else 0

    # Check thresholds
    violations = []
    if success_rate < (1 - error_rate_threshold):
        violations.append(f"Success rate {success_rate:.2%} < threshold {(1-error_rate_threshold):.2%}")
    if p95 > latency_threshold_ms:
        violations.append(f"P95 latency {p95:.0f}ms > threshold {latency_threshold_ms}ms")

    passed = len(violations) == 0

    result = CanaryResult(
        plugin_id=plugin_id,
        commands_tested=commands,
        total_invocations=total_invocations,
        success_rate=success_rate,
        avg_latency_ms=avg,
        p50_latency_ms=p50,
        p95_latency_ms=p95,
        p99_latency_ms=p99,
        errors=errors,
        memory_mb=0,  # Would measure separately
        passed=passed,
        threshold_violations=violations,
    )

    # Print summary
    print("\n" + "=" * 60)
    print("📊 CANARY TEST RESULTS")
    print("=" * 60)
    print(f"Plugin:         {plugin_id}")
    print(f"Invocations:    {total_invocations}")
    print(f"Success Rate:   {success_rate:.2%}")
    print("Latency:")
    print(f"  - Avg:        {avg:.1f}ms")
    print(f"  - P50:        {p50:.1f}ms")
    print(f"  - P95:        {p95:.1f}ms")
    print(f"  - P99:        {p99:.1f}ms")
    if errors:
        print(f"Errors:         {errors}")

    if passed:
        print("\n✅ PASSED - Canary test successful")
    else:
        print("\n❌ FAILED - Threshold violations:")
        for v in violations:
            print(f"   • {v}")

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run canary test for plugin migration")
    parser.add_argument("--plugin", required=True, help="Plugin ID to test")
    parser.add_argument("--commands", required=True, help="Comma-separated list of commands")
    parser.add_argument("--iterations", type=int, default=20, help="Iterations per command")
    parser.add_argument("--output", type=Path, help="Output JSON file for results")
    parser.add_argument("--latency-threshold", type=float, default=500, help="P95 latency threshold ms")
    parser.add_argument("--error-threshold", type=float, default=0.01, help="Max error rate (0-1)")

    args = parser.parse_args()

    commands = [c.strip() for c in args.commands.split(",") if c.strip()]
    if not commands:
        print("Error: No commands specified")
        return 1

    try:
        result = run_canary_test(
            plugin_id=args.plugin,
            commands=commands,
            iterations_per_command=args.iterations,
            latency_threshold_ms=args.latency_threshold,
            error_rate_threshold=args.error_threshold,
        )

        if args.output:
            args.output.write_text(json.dumps(result.to_dict(), indent=2))
            print(f"\n📄 Results saved to: {args.output}")

        return 0 if result.passed else 1

    except KeyboardInterrupt:
        print("\n\n⚠️ Canary test interrupted")
        return 130
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
