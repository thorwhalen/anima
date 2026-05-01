"""Cutout-style 2D animation backend.

Phase 2A ships the Python-side substrate: scene graph, animations, timeline,
JSON serialization. The actual mp4 rendering (JS runtime + headless capture)
arrives in Phases 2B/2C.

>>> from anima.adapters.cutout import CutoutRenderer, compile_shot
>>> CutoutRenderer().name
'cutout'
"""

from anima.adapters.cutout.compile import compile_shot
from anima.adapters.cutout.serialize import (
    AnimationClipJSON,
    AssetJSON,
    AssetsJSON,
    ChannelJSON,
    CutoutSceneJSON,
    KeyframeJSON,
    NodeJSON,
    PlacedClipJSON,
    RigJSON,
    SkinJSON,
    TimelineJSON,
    TrackJSON,
    VisualJSON,
)
from anima.adapters.cutout.render import CutoutRenderer, CutoutRenderError

__all__ = [
    "CutoutRenderer",
    "CutoutRenderError",
    "compile_shot",
    "CutoutSceneJSON",
    "NodeJSON",
    "VisualJSON",
    "RigJSON",
    "SkinJSON",
    "AnimationClipJSON",
    "ChannelJSON",
    "KeyframeJSON",
    "TimelineJSON",
    "TrackJSON",
    "PlacedClipJSON",
    "AssetsJSON",
    "AssetJSON",
]


# Register on import so `anima.adapters.list_renderers()` finds it.
from anima.adapters._base import register_renderer as _register_renderer

_register_renderer(CutoutRenderer())
