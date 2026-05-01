"""anima — AI-driven structured animation.

Public API surface (curated). See `anima.ir` for the Scene IR, `anima.adapters`
for renderer plumbing, `anima.audio` for TTS/lip-sync protocols, `anima.verify`
for verification, and `anima.stores` for the project mall.

>>> import anima
>>> 'SceneIR' in anima.__all__
True
"""

from anima.base import (
    SCHEMA_VERSION,
    COMPATIBLE_VERSION,
    DEFAULT_FPS,
    DEFAULT_RESOLUTION,
    SUPPORTED_STYLES,
)
from anima.ir import (
    SceneIR,
    Meta,
    AssetRef,
    Shot,
    Action,
    Dialogue,
    Camera,
    Resolution,
    set_,
    tween,
    play,
    sequence,
    parallel,
    delay,
    loop,
    flatten,
    FlatAction,
    validate_schema,
    validate_semantic,
    markdown_to_ir,
    ir_to_markdown,
)
from anima.project import init, load, save, Project
from anima.check_requirements import check_requirements
from anima.stores import build_project_mall

__version__ = "0.0.1"

__all__ = [
    # Versions / constants
    "SCHEMA_VERSION",
    "COMPATIBLE_VERSION",
    "DEFAULT_FPS",
    "DEFAULT_RESOLUTION",
    "SUPPORTED_STYLES",
    # Scene IR
    "SceneIR",
    "Meta",
    "AssetRef",
    "Shot",
    "Action",
    "Dialogue",
    "Camera",
    "Resolution",
    # Composition
    "set_",
    "tween",
    "play",
    "sequence",
    "parallel",
    "delay",
    "loop",
    "flatten",
    "FlatAction",
    # Validation
    "validate_schema",
    "validate_semantic",
    # Sync
    "markdown_to_ir",
    "ir_to_markdown",
    # Project
    "init",
    "load",
    "save",
    "Project",
    "build_project_mall",
    # System diagnostics
    "check_requirements",
]
