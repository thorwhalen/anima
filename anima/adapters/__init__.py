"""Renderer adapters — facades over backends (cutout, Manim, Remotion, etc.).

In Phase 1 only the protocol and registry live here. Concrete backends arrive
in subsequent phases.
"""

from anima.adapters._base import (
    Renderer,
    RendererRegistry,
    RenderContext,
    RenderResult,
    register_renderer,
    get_renderer,
    list_renderers,
)

__all__ = [
    "Renderer",
    "RendererRegistry",
    "RenderContext",
    "RenderResult",
    "register_renderer",
    "get_renderer",
    "list_renderers",
]
