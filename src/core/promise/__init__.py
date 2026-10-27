# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong Product-Promise execution spine.

This package is the *single* path that turns an advertised CLI capability
(``https://www.mekongmind.com/cli``) into a real, authorized, verified and
persisted business execution:

    UI/CLI -> identity + workspace RBAC -> schema validation -> job record
           -> runtime handler/agent/tool -> persistence -> postcondition
           verifier -> signed evidence -> status returned to UI/CLI

Design rules enforced here (founder directive, 2026-10):

* No fail-open dispatch. A command without a bound operation returns
  ``NOT_IMPLEMENTED`` — never ``EXECUTED``/``success``.
* Maturity tiers are *derived* from observed behaviour
  (:mod:`src.core.promise.truth`), never asserted by hand.
* Evidence separates three facts: the handler ran, the artifact is intact,
  and the business condition was met.
* Standard library only (``tests/test_core_boundary.py``).
"""

from __future__ import annotations

__all__ = [
    "contracts",
    "evidence",
    "identity",
    "jobs",
    "schema",
    "service",
    "truth",
]
