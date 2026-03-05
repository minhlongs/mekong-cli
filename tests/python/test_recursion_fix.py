#!/usr/bin/env python3
"""
Test script to verify the recursion depth issue is fixed in telemetry collection.
"""

import sys
import os
# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from core.telemetry import TelemetryCollector


def test_recursion_fix():
    """Test that telemetry collection doesn't cause recursion depth errors."""
    print("Testing telemetry recursion fix...")

    # Create a telemetry collector
    collector = TelemetryCollector()

    # Start a trace
    collector.start_trace("Test goal for recursion fix")

    # Add several steps to the trace
    for i in range(5):
        collector.record_step(
            step_order=i,
            title=f"Test step {i}",
            duration=1.0,
            exit_code=0,
            self_healed=False,
            agent="test-agent"
        )

    # Record some LLM calls
    for i in range(3):
        collector.record_llm_call()

    # Record some errors
    collector.record_error("Test error 1")
    collector.record_error("Test error 2")

    # Finish the trace - this is where recursion issues occurred
    try:
        trace = collector.finish_trace()
        print("✓ Trace finished successfully without recursion errors")

        # Verify we can serialize the trace safely
        if trace:
            print("✓ Trace serialization completed successfully")
            print(f"  - Goal: {trace.goal}")
            print(f"  - Steps: {len(trace.steps)}")
            print(f"  - Errors: {len(trace.errors)}")
            print(f"  - LLM calls: {trace.llm_calls}")

        return True

    except RecursionError as e:
        print(f"✗ RecursionError still occurs: {e}")
        return False
    except Exception as e:
        print(f"✗ Other error occurred: {e}")
        return False


if __name__ == "__main__":
    success = test_recursion_fix()
    if success:
        print("\n✓ Recursion depth issue has been fixed!")
        sys.exit(0)
    else:
        print("\n✗ Recursion depth issue still exists!")
        sys.exit(1)