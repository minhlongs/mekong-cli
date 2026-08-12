#!/usr/bin/env python3
"""
Performance Regression Checker

Compares current benchmark results against baseline.
Fails if overhead exceeds acceptable threshold.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any


def load_results(filepath: Path) -> Dict[str, Any]:
    """Load benchmark results from JSON."""
    with open(filepath) as f:
        return json.load(f)


def check_regression(results: Dict[str, Any], max_overhead_pct: float = 5.0) -> List[str]:
    """Check for performance regressions.

    Returns list of failure messages, empty if all good.
    """
    failures = []

    comparisons = results.get('comparisons', [])

    for comp in comparisons:
        metric = comp['metric']
        overhead = comp.get('overhead_pct', 0)
        target = comp.get('target_pct', max_overhead_pct)

        if overhead > target:
            failures.append(
                f"{metric}: overhead {overhead:.1f}% exceeds target {target:.1f}% "
                f"(core: {comp['core']['median_ms']:.1f}ms, "
                f"plugin: {comp['plugin']['median_ms']:.1f}ms)"
            )

    # Check individual metrics against targets
    targets = results.get('targets', {})
    for result in results.get('results', []):
        if result['mode'] == 'plugin':
            name = result['name']

            # Command invocation target
            if 'command_invocation' in name:
                if result['median_ms'] > targets.get('command_invocation_ms', 100):
                    failures.append(
                        f"Command invocation too slow: {result['median_ms']:.1f}ms "
                        f"(target: <{targets.get('command_invocation_ms', 100)}ms)"
                    )

            # Startup time targets
            if 'startup' in name:
                warm_target = targets.get('warm_startup_ms', 1000)
                if result['median_ms'] > warm_target:
                    failures.append(
                        f"Plugin startup too slow: {result['median_ms']:.1f}ms "
                        f"(target: <{warm_target}ms)"
                    )

            # Memory target
            if result.get('memory_mb') and result['memory_mb'] > targets.get('plugin_memory_mb', 10):
                failures.append(
                    f"Plugin memory too high: {result['memory_mb']:.1f}MB "
                    f"(target: <{targets.get('plugin_memory_mb', 10)}MB)"
                )

    return failures


def main():
    """CLI entrypoint."""
    import argparse

    parser = argparse.ArgumentParser(description="Check for performance regressions")
    parser.add_argument(
        "results",
        type=Path,
        help="Benchmark results JSON file"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=5.0,
        help="Maximum allowed overhead percentage"
    )

    args = parser.parse_args()

    try:
        results = load_results(args.results)
    except Exception as e:
        print(f"Error loading results: {e}")
        sys.exit(2)

    failures = check_regression(results, args.threshold)

    if failures:
        print("PERFORMANCE REGRESSION DETECTED")
        print("=" * 60)
        for failure in failures:
            print(f"  ✗ {failure}")
        print("=" * 60)
        sys.exit(1)
    else:
        print("Performance check: PASSED")
        print(f"All metrics within {args.threshold}% overhead threshold")
        sys.exit(0)


if __name__ == "__main__":
    main()
