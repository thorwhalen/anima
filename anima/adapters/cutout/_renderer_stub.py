"""CutoutRenderer skeleton — implements `Renderer`, defers `render` to Phase 2C.

Registering this stub now lets the orchestrator (and `anima check`) see the
cutout renderer in the registry, so plumbing can be exercised end-to-end
even before the JS runtime + headless capture exist.
"""

from __future__ import annotations

from anima.adapters._base import RenderContext, RenderResult
from anima.ir.schema import Shot


class CutoutRenderer:
    """Phase 2A stub. ``render`` raises until Phase 2C lights up the JS runtime."""

    name: str = "cutout"
    supported_styles: tuple[str, ...] = ("cutout",)

    def can_render(self, shot: Shot) -> bool:
        return shot.style == "cutout"

    def render(self, shot: Shot, ctx: RenderContext) -> RenderResult:  # pragma: no cover
        raise NotImplementedError(
            "CutoutRenderer.render lands in Phase 2C (Playwright + ffmpeg). "
            "Use anima.adapters.cutout.compile_shot to produce the runtime JSON for now."
        )
