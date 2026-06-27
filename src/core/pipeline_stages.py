"""Mekong CLI - Pipeline Stages Module.

Specialized pipeline stages (FilePicker, Editor, Reviewer) that compose
within the existing PEV loop. Mirrors Codebuff's 4-stage pipeline
(FilePicker -> Planner -> Editor -> Reviewer) adapted to mekong-cli's
Plan-Execute-Verify architecture.

Each stage is a configuration dict defining:
- agent_class: which AgentBase subclass to use
- allowed_tools: tool restriction for this stage
- phase: which PEV phase this stage belongs to
- optional: whether the stage is opt-in (default: True)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PipelineStage:
    """Definition of a pipeline stage.

    Attributes:
        name: Stage identifier (e.g. 'file-picker', 'editor').
        agent_class: AgentBase subclass to instantiate.
        allowed_tools: Tool names this stage can use.
        phase: PEV phase this stage belongs to ('plan', 'execute', 'verify').
        optional: If True, stage is skipped unless explicitly enabled.
        description: Human-readable description.
    """

    name: str
    agent_class: str  # dotted path, e.g. "agents.file_picker_agent.FilePickerAgent"
    allowed_tools: list[str] = field(default_factory=list)
    phase: str = "execute"  # plan | execute | verify
    optional: bool = True
    description: str = ""


# ─── Stage definitions ─────────────────────────────────────────────────────────

FILE_PICKER_STAGE = PipelineStage(
    name="file-picker",
    agent_class="agents.file_picker_agent.FilePickerAgent",
    allowed_tools=["read_files", "find_files", "glob", "code_search", "file:list"],
    phase="plan",
    optional=True,
    description="Scan codebase and surface relevant files for a given task",
)

EDITOR_STAGE = PipelineStage(
    name="editor",
    agent_class="agents.editor_agent.EditorAgent",
    allowed_tools=[
        "read_files",
        "write_file",
        "str_replace",
        "apply_patch",
        "run_terminal_command",
        "shell:run",
        "file:list",
        "file:write",
    ],
    phase="execute",
    optional=True,
    description="Perform precise code edits using restricted tool set",
)

REVIEWER_STAGE = PipelineStage(
    name="reviewer",
    agent_class="agents.reviewer_agent.ReviewerAgent",
    allowed_tools=[
        "read_files",
        "code_search",
        "find_files",
        "glob",
        "file:list",
    ],
    phase="verify",
    optional=True,
    description="Validate changes and check for regressions after edits (read-only)",
)

# All available stages
ALL_STAGES: dict[str, PipelineStage] = {
    "file-picker": FILE_PICKER_STAGE,
    "editor": EDITOR_STAGE,
    "reviewer": REVIEWER_STAGE,
}

# Default pipeline: all stages enabled
DEFAULT_PIPELINE = ["file-picker", "editor", "reviewer"]


def get_stage(name: str) -> PipelineStage:
    """Get a stage definition by name.

    Args:
        name: Stage name (e.g. 'file-picker', 'editor').

    Returns:
        PipelineStage definition.

    Raises:
        KeyError: If stage name not found.
    """
    if name not in ALL_STAGES:
        available = list(ALL_STAGES.keys())
        raise KeyError(f"Unknown pipeline stage: '{name}'. Available: {available}")
    return ALL_STAGES[name]


def compose_pipeline(
    stage_names: list[str] | None = None,
    enabled_phases: list[str] | None = None,
) -> list[PipelineStage]:
    """Compose a pipeline from stage names.

    Args:
        stage_names: Stage names to include. None = all non-optional stages.
        enabled_phases: If set, only include stages from these PEV phases
            (e.g. ['plan', 'verify'] to skip execute-stage tools).

    Returns:
        Ordered list of PipelineStage objects.
    """
    if stage_names is None:
        # Include all non-optional stages by default
        stage_names = [n for n, s in ALL_STAGES.items() if not s.optional]

    stages = []
    for name in stage_names:
        try:
            stage = get_stage(name)
            if enabled_phases and stage.phase not in enabled_phases:
                logger.debug("Skipping stage %r (phase %r not in %r)", name, stage.phase, enabled_phases)
                continue
            stages.append(stage)
        except KeyError:
            logger.warning("Unknown pipeline stage: %r", name)

    return stages


def stages_by_phase(phase: str) -> list[PipelineStage]:
    """Get all stages for a specific PEV phase.

    Args:
        phase: PEV phase ('plan', 'execute', 'verify').

    Returns:
        List of PipelineStage objects for that phase.
    """
    return [s for s in ALL_STAGES.values() if s.phase == phase]


# Export
__all__ = [
    "ALL_STAGES",
    "DEFAULT_PIPELINE",
    "EDITOR_STAGE",
    "FILE_PICKER_STAGE",
    "PipelineStage",
    "REVIEWER_STAGE",
    "compose_pipeline",
    "get_stage",
    "stages_by_phase",
]
