# Phase 06: Zero-Mock Testing & Quality Verification

## Overview
- Priority: High
- Status: Ready to Implement
- Standards: Mekong CLI Strict Zero-Mock Policy, < 200 LOC per file
- Target Files:
  - `tests/test_maritime_purifier_steering_unit_suite.py` (< 200 LOC)
  - `tests/test_maritime_heeling_sniffer_unit_suite.py` (< 200 LOC)
  - `tests/test_maritime_383_to_386_cli_mcp_suite.py` (< 200 LOC)

## Coverage Objectives
- 100% Zero-mock testing covering all edge cases:
  - Phase 383: Optimal purification, low separation temperature, cat fines breakthrough, excessive bowl vibration.
  - Phase 384: Main steering travel compliant, emergency steering travel compliant, slow steering alarm, power loss failover.
  - Phase 385: Static heel compliant, dynamic rapid heel rate trigger, low-level tank cavitation interlock, crane emergency shutdown.
  - Phase 386: Atmosphere normal, hydrocarbon 10% LEL warning, 20% LEL pump trip, H2S toxic hazard, ventilation failure interlock.
- CLI sub-app execution verification (both English and Vietnamese aliases).
- FastMCP async tools invocation and dictionary response verification.
