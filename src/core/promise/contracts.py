# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Capability operation contracts.

An :class:`OperationSpec` is the machine-readable form of one advertised
promise: *what the command accepts, which real code executes it, what it is
allowed to touch, what must be true afterwards, and which test proves it*.

The registry built from these specs is the **executable** half of the
claim ledger. ``src/core/promise/truth.py`` diffs it against the
**advertised** half (``src/registry/capability_ledger.json`` +
``src/registry/cli_surface.json``) so CI fails when the website promises
something the runtime cannot do.
"""

from __future__ import annotations

import dataclasses
import typing

# ---------------------------------------------------------------------------
# Enumerations (string constants — stdlib only, JSON friendly)
# ---------------------------------------------------------------------------

#: Effect the operation has on the world outside the workspace database.
EXTERNAL_EFFECTS: frozenset[str] = frozenset({
    "NONE",                    # pure computation / read
    "WORKSPACE_WRITE",         # writes workspace-local artifacts or ledger rows
    "RECORD_AUDIT_LEDGER",     # appends to a compliance/audit ledger
    "PROVIDER_CALL",           # calls an external provider adapter
    "SEND_MESSAGE",            # Zalo/Telegram/email — irreversible
    "MOVE_MONEY",              # payment initiation — irreversible
    "FILE_SUBMISSION",         # tax/invoice/legal filing — irreversible
    "DEPLOY",                  # production deployment — irreversible
})

#: Effects whose outcome can be *unknown* after a crash (need reconciliation).
UNCERTAIN_EFFECTS: frozenset[str] = frozenset({
    "PROVIDER_CALL",
    "SEND_MESSAGE",
    "MOVE_MONEY",
    "FILE_SUBMISSION",
    "DEPLOY",
})

APPROVAL_POLICIES: frozenset[str] = frozenset({
    "AUTO",                    # deterministic, no external side effect
    "FOUNDER_CONFIRMATION",    # one human owner approval bound to the payload
    "DUAL_CONTROL",            # approval + second reviewer for money/filings
})

#: Derived maturity tiers (see ``truth.py`` — never hand-asserted).
MATURITY_REAL_VERIFIED = "REAL_VERIFIED"
MATURITY_PARTIAL_LOOKUP = "PARTIAL_LOOKUP"
MATURITY_CATALOG_ONLY = "CATALOG_ONLY"
MATURITY_BLOCKED = "BLOCKED"
MATURITY_NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
VALID_MATURITY_TIERS: frozenset[str] = frozenset({
    MATURITY_REAL_VERIFIED,
    MATURITY_PARTIAL_LOOKUP,
    MATURITY_CATALOG_ONLY,
    MATURITY_BLOCKED,
    MATURITY_NOT_IMPLEMENTED,
})


@dataclasses.dataclass(frozen=True)
class HandlerRef:
    """Pointer at the *real* code that performs the operation.

    ``module``/``factory``/``method`` resolve lazily at execution time so that
    heavy engines are only imported when their command actually runs.
    ``param_map`` renames operation parameters to method keyword arguments;
    ``constructor_param_map`` routes parameters into the engine constructor
    (used for per-workspace ``db_path`` isolation).
    """

    module: str = ""
    method: str = ""
    factory: str | None = None
    param_map: typing.Mapping[str, str] = dataclasses.field(default_factory=dict)
    constructor_param_map: typing.Mapping[str, str] = dataclasses.field(default_factory=dict)
    constructor_kwargs: typing.Mapping[str, typing.Any] = dataclasses.field(default_factory=dict)
    callable_path: str | None = None  # alternative: "pkg.module:function"

    def __post_init__(self) -> None:
        if self.callable_path and ":" not in self.callable_path:
            raise ValueError(f"callable_path must be 'package.module:function': {self.callable_path}")
        if not self.callable_path and not (self.module and self.method):
            raise ValueError("a handler reference needs either callable_path or module+method")

    def describe(self) -> str:
        if self.callable_path:
            return self.callable_path
        owner = f"{self.factory}.{self.method}" if self.factory else self.method
        return f"{self.module}:{owner}"


@dataclasses.dataclass(frozen=True)
class Postcondition:
    """One declarative business condition that must hold after execution."""

    check: str
    params: typing.Mapping[str, typing.Any] = dataclasses.field(default_factory=dict)
    required: bool = True
    description: str = ""

    def to_dict(self) -> dict[str, typing.Any]:
        return {"check": self.check, "params": dict(self.params), "required": self.required,
                "description": self.description}


@dataclasses.dataclass(frozen=True)
class OperationSpec:
    """Full contract for one executable capability operation."""

    op_id: str
    command: str
    subcommand: str
    title: str
    description: str
    input_schema: dict[str, typing.Any]
    handler: HandlerRef
    external_effect: str = "NONE"
    effects: tuple[str, ...] = ()
    approval_policy: str = "AUTO"
    idempotency_fields: tuple[str, ...] = ()
    postconditions: tuple[Postcondition, ...] = ()
    sop_steps: tuple[str, ...] = ()
    gate_id: str = ""
    department_id: str = ""
    layer_id: str = ""
    jurisdiction: str = "VN"
    rule_version: str = ""
    statutory_basis: tuple[str, ...] = ()
    output_contract: typing.Mapping[str, typing.Any] = dataclasses.field(default_factory=dict)
    cost_policy: typing.Mapping[str, typing.Any] = dataclasses.field(default_factory=dict)
    long_running: bool = False
    timeout_seconds: int = 60
    test_id: str = ""
    notes: str = ""

    def __post_init__(self) -> None:
        if self.external_effect not in EXTERNAL_EFFECTS:
            raise ValueError(f"{self.op_id}: unknown external_effect '{self.external_effect}'")
        if self.approval_policy not in APPROVAL_POLICIES:
            raise ValueError(f"{self.op_id}: unknown approval_policy '{self.approval_policy}'")
        if self.external_effect in UNCERTAIN_EFFECTS and self.approval_policy == "AUTO":
            raise ValueError(
                f"{self.op_id}: effect '{self.external_effect}' can never be AUTO-approved"
            )
        if not self.postconditions:
            raise ValueError(f"{self.op_id}: at least one business postcondition is required")

    @property
    def writes_workspace(self) -> bool:
        return any(e.startswith("WRITE:") for e in self.effects)

    def to_dict(self) -> dict[str, typing.Any]:
        data = dataclasses.asdict(self)
        data["handler"] = self.handler.describe()
        data["postconditions"] = [p.to_dict() for p in self.postconditions]
        return data


class OperationRegistry:
    """In-memory index of every executable operation contract."""

    def __init__(self) -> None:
        self._by_op_id: dict[str, OperationSpec] = {}
        self._by_command: dict[str, dict[str, OperationSpec]] = {}

    def register(self, spec: OperationSpec) -> OperationSpec:
        if spec.op_id in self._by_op_id:
            existing = self._by_op_id[spec.op_id]
            if existing != spec:
                raise ValueError(f"duplicate op_id with different contract: {spec.op_id}")
            return spec
        self._by_op_id[spec.op_id] = spec
        self._by_command.setdefault(spec.command, {})[spec.subcommand] = spec
        return spec

    def register_all(self, specs: typing.Iterable[OperationSpec]) -> None:
        for spec in specs:
            self.register(spec)

    def get(self, op_id: str) -> OperationSpec | None:
        return self._by_op_id.get(op_id)

    def resolve(self, command: str, subcommand: str | None = None) -> OperationSpec | None:
        subs = self._by_command.get(command)
        if not subs:
            return None
        if subcommand and subcommand in subs:
            return subs[subcommand]
        if subcommand and subcommand not in subs:
            return None
        # Default operation for the command group (explicit "default" subcommand).
        return subs.get("default") or subs.get("status")

    def operations_for(self, command: str) -> list[OperationSpec]:
        return sorted(self._by_command.get(command, {}).values(), key=lambda s: s.op_id)

    def commands(self) -> list[str]:
        return sorted(self._by_command)

    def all(self) -> list[OperationSpec]:
        return sorted(self._by_op_id.values(), key=lambda s: s.op_id)

    def __len__(self) -> int:
        return len(self._by_op_id)


REGISTRY = OperationRegistry()


def load_default_registry() -> OperationRegistry:
    """Populate :data:`REGISTRY` from the authored operation modules."""
    from src.core.promise import ops  # noqa: F401  (import side effect: registration)

    return REGISTRY


__all__ = [
    "APPROVAL_POLICIES",
    "EXTERNAL_EFFECTS",
    "MATURITY_BLOCKED",
    "MATURITY_CATALOG_ONLY",
    "MATURITY_NOT_IMPLEMENTED",
    "MATURITY_PARTIAL_LOOKUP",
    "MATURITY_REAL_VERIFIED",
    "REGISTRY",
    "UNCERTAIN_EFFECTS",
    "VALID_MATURITY_TIERS",
    "HandlerRef",
    "OperationRegistry",
    "OperationSpec",
    "Postcondition",
    "load_default_registry",
]
