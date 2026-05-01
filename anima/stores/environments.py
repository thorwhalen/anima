"""Environments store — backgrounds, set pieces, and prop bundles."""

from __future__ import annotations

from anima.stores._common import JsonSidecarStore


class EnvironmentsStore(JsonSidecarStore):
    """Per-environment directory store (meta + sidecar art)."""
