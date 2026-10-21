# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - Plan Constraint System."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from .parser import Recipe


@dataclass
class ConstraintViolation:
    step_order: int
    constraint_name: str
    message: str


@dataclass
class ResourceLimit:
    max_concurrent_steps: int = 0
    max_total_steps: int = 0


@dataclass
class TimeBound:
    max_step_duration_s: Optional[float] = None
    max_total_duration_s: Optional[float] = None


@dataclass
class OrderingConstraint:
    before_step: str
    after_step: str


@dataclass
class MutualExclusion:
    step_titles: List[str] = field(default_factory=list)


@dataclass
class PlanConstraints:
    resource_limit: Optional[ResourceLimit] = None
    time_bound: Optional[TimeBound] = None
    ordering: List[OrderingConstraint] = field(default_factory=list)
    mutual_exclusions: List[MutualExclusion] = field(default_factory=list)


class ConstraintEngine:
    """Validates a Recipe against a PlanConstraints set."""

    def validate(self, recipe: "Recipe", constraints: PlanConstraints) -> List[ConstraintViolation]:
        violations: List[ConstraintViolation] = []
        if constraints.resource_limit:
            violations.extend(self._check_resource_limits(recipe, constraints.resource_limit))
        for ordering in constraints.ordering:
            violations.extend(self._check_ordering(recipe, ordering))
        for exclusion in constraints.mutual_exclusions:
            violations.extend(self._check_mutual_exclusion(recipe, exclusion))
        if constraints.time_bound:
            violations.extend(self._check_time_bound(recipe, constraints.time_bound))
        return violations

    def _check_resource_limits(self, recipe: "Recipe", limit: ResourceLimit) -> List[ConstraintViolation]:
        violations: List[ConstraintViolation] = []
        if limit.max_total_steps > 0 and len(recipe.steps) > limit.max_total_steps:
            violations.append(ConstraintViolation(
                0, "ResourceLimit.max_total_steps",
                f"Plan has {len(recipe.steps)} steps, exceeds limit of {limit.max_total_steps}",
            ))
        if limit.max_concurrent_steps > 0:
            width = self._dag_width(recipe)
            if width > limit.max_concurrent_steps:
                violations.append(ConstraintViolation(
                    0, "ResourceLimit.max_concurrent_steps",
                    f"Plan has up to {width} concurrent steps, exceeds limit of {limit.max_concurrent_steps}",
                ))
        return violations

    def _check_ordering(self, recipe: "Recipe", ordering: OrderingConstraint) -> List[ConstraintViolation]:
        violations: List[ConstraintViolation] = []
        before_steps = [s for s in recipe.steps if ordering.before_step.lower() in s.title.lower()]
        after_steps = [s for s in recipe.steps if ordering.after_step.lower() in s.title.lower()]
        if not before_steps or not after_steps:
            return violations
        reachable = self._build_reachability(recipe)
        for a_step in after_steps:
            if not any(b.order in reachable.get(a_step.order, set()) for b in before_steps):
                violations.append(ConstraintViolation(
                    a_step.order, "OrderingConstraint",
                    f"Step {a_step.order} ('{a_step.title}') must depend on a step matching '{ordering.before_step}'",
                ))
        return violations

    def _check_mutual_exclusion(self, recipe: "Recipe", exclusion: MutualExclusion) -> List[ConstraintViolation]:
        violations: List[ConstraintViolation] = []
        matched = [s for s in recipe.steps if any(p.lower() in s.title.lower() for p in exclusion.step_titles)]
        if len(matched) < 2:
            return violations
        reachable = self._build_reachability(recipe)
        for i, s1 in enumerate(matched):
            for s2 in matched[i + 1:]:
                if s1.order not in reachable.get(s2.order, set()) and s2.order not in reachable.get(s1.order, set()):
                    violations.append(ConstraintViolation(
                        s1.order, "MutualExclusion",
                        f"Steps {s1.order} ('{s1.title}') and {s2.order} ('{s2.title}') may run concurrently but are mutually exclusive",
                    ))
        return violations

    def _check_time_bound(self, recipe: "Recipe", bound: TimeBound) -> List[ConstraintViolation]:
        violations: List[ConstraintViolation] = []
        if bound.max_step_duration_s is not None and bound.max_step_duration_s <= 0:
            violations.append(ConstraintViolation(0, "TimeBound.max_step_duration_s", "max_step_duration_s must be positive"))
        if bound.max_total_duration_s is not None and bound.max_total_duration_s <= 0:
            violations.append(ConstraintViolation(0, "TimeBound.max_total_duration_s", "max_total_duration_s must be positive"))
        return violations

    def _build_reachability(self, recipe: "Recipe") -> dict:
        step_map = {s.order: s for s in recipe.steps}
        cache: dict = {}

        def ancestors(order: int) -> set:
            if order in cache:
                return cache[order]
            result: set = set()
            step = step_map.get(order)
            if step is not None:
                for dep in step.params.get("dependencies", []) or step.dependencies:
                    result.add(dep)
                    result.update(ancestors(dep))
            cache[order] = result
            return result

        return {s.order: ancestors(s.order) for s in recipe.steps}

    def _dag_width(self, recipe: "Recipe") -> int:
        if not recipe.steps:
            return 0
        order_to_deps = {s.order: set(s.params.get("dependencies", []) or s.dependencies) for s in recipe.steps}
        levels: dict = {}
        for step in recipe.steps:
            deps = order_to_deps[step.order]
            parent_levels = [levels.get(d, 0) for d in deps if d in levels]
            levels[step.order] = (max(parent_levels) + 1) if (deps and parent_levels) else 0
        level_counts = Counter(levels.values())
        return max(level_counts.values()) if level_counts else 0


__all__ = [
    "ConstraintEngine", "ConstraintViolation", "MutualExclusion",
    "OrderingConstraint", "PlanConstraints", "ResourceLimit", "TimeBound",
]
