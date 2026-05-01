"""Audio pipeline — TTS and lip-sync protocols (concrete impls land in P3)."""

from anima.audio.tts import TTSProvider, AudioClip, VoiceMeta
from anima.audio.lipsync import LipSyncProvider, Viseme, VisemeTrack

__all__ = [
    "TTSProvider",
    "AudioClip",
    "VoiceMeta",
    "LipSyncProvider",
    "Viseme",
    "VisemeTrack",
]
