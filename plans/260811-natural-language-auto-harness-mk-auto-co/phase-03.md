# Phase 03 — 01.03

**Date:** 260811 · **Status:** pending

## Task
Define gate registry in registry.yaml with hard_gates: code_review_required, ci_checks_pass, no_force_push_main. Default gates for deploy, rm, git-push-force, chi-tien, xoa-data. Implement GateRegistry loader and GateProtocol with exit code 42.

## Files

- registry.yaml
- core/gates.py

## Acceptance criteria

registry.yaml loads 5 default gates + 3 hard gates; GateProtocol.evaluate('deploy') returns gate decision with exit_code=42 when gate blocks; hard gates cannot be overridden
