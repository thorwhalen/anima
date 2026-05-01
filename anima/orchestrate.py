"""Orchestrator entry points (Phase-1 stub).

The full orchestration flow — interview → IR draft → validate → audio →
render → verify → iterate — lands in Phase 5. Phase 1 ships only the entry
points so the skill suite has stable names to call into.
"""

from __future__ import annotations

from pathlib import Path

from anima.ir.schema import SceneIR
from anima.ir.validate import (
    ValidationReport,
    validate_schema,
    validate_semantic,
)
from anima.project import Project, load


def validate_project(project_dir: str | Path) -> ValidationReport:
    """Schema + semantic validation of the scene at ``project_dir``."""
    project: Project = load(project_dir)
    schema_report = validate_schema(project.scene)
    semantic_report = validate_semantic(
        project.scene,
        available_voices=project.mall.get("voices"),
        available_characters=project.mall.get("characters"),
    )
    return schema_report.merge(semantic_report)


def render_project(project_dir: str | Path) -> str:
    """Render the project's scene. Phase-1 stub: not yet implemented."""
    raise NotImplementedError(
        "Render is not implemented in Phase 1. "
        "The cutout adapter (Phase 2) wires this up."
    )


def iterate(project_dir: str | Path, instruction: str) -> SceneIR:
    """Apply a free-text edit instruction. Phase-1 stub: not yet implemented."""
    raise NotImplementedError(
        "Iterative edit loop arrives in Phase 5 along with the orchestrator skill."
    )
