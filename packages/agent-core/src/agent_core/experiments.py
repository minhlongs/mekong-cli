"""A/B testing primitive — Giai đoạn 3.4.B (Pillar 3 Statsig-style 3-step final slot).

Deterministic hash-based bucket assignment: same (user_id, experiment_name)
always resolves to the same variant. Uniform distribution across variants
when user_ids are uniformly distributed.

Pairs with offline evals (Giai đoạn 3.3.A) + online signals (Giai đoạn 3.2)
to complete the Statsig 3-step gate: offline regression guard → online
quality signal → A/B variant exposure.
"""

from __future__ import annotations

import hashlib

DEFAULT_VARIANTS: tuple[str, ...] = ("control", "treatment")


def bucket(
    user_id: str,
    experiment_name: str,
    variants: list[str] | tuple[str, ...] | None = None,
) -> str:
    """Assign a user to one variant of an experiment.

    Uses SHA-256(f"{user_id}:{experiment_name}") to pick a variant by modulo.
    Same inputs always yield the same variant (deterministic, sticky).

    Cross-experiment isolation comes from the experiment_name being part of
    the hash key: user X in exp-A is uncorrelated with user X in exp-B.

    Args:
        user_id: Non-empty unique user identifier.
        experiment_name: Non-empty experiment name.
        variants: Variant names, defaults to ``("control", "treatment")``.
            Must be non-empty. Equal weight only (YAGNI — weighted rollout
            is a later feature).

    Returns:
        The chosen variant string.

    Raises:
        ValueError: If ``user_id`` / ``experiment_name`` is empty or if
            ``variants`` is an empty list.
    """
    if not user_id:
        raise ValueError("user_id must be non-empty")
    if not experiment_name:
        raise ValueError("experiment_name must be non-empty")

    resolved = tuple(variants) if variants is not None else DEFAULT_VARIANTS
    if not resolved:
        raise ValueError("variants must be non-empty")

    key = f"{user_id}:{experiment_name}".encode()
    digest = hashlib.sha256(key).digest()
    # Take first 8 bytes for a 64-bit unsigned integer — more than enough
    # entropy for bucket selection and faster than decoding the full digest.
    slot = int.from_bytes(digest[:8], "big") % len(resolved)
    return resolved[slot]
