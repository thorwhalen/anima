"""Verification protocol — same interface for human, lint, vision-LM, MoVer."""

from anima.verify._base import (
    Verifier,
    Finding,
    VerificationReport,
    Severity,
)

__all__ = [
    "Verifier",
    "Finding",
    "VerificationReport",
    "Severity",
]
