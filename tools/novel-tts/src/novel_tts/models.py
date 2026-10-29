"""Typed data models used by novel-tts."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TTSConfig:
    provider: str = "qwen"
    model: str = "qwen-audio-3.1-tts-flash"
    region: str = "cn-beijing"
    format: str = "mp3"
    sample_rate: int = 24000


@dataclass(frozen=True)
class Character:
    name: str
    voice: str


@dataclass(frozen=True)
class Segment:
    id: str
    speaker: str
    text: str
    emotion: str = "neutral"
    rate: float = 1.0
    pause_after: float = 0.0


@dataclass(frozen=True)
class Script:
    title: str
    tts: TTSConfig
    characters: dict[str, Character]
    segments: list[Segment]
    output_dir: Path
    source_path: Path
    raw: dict[str, Any] = field(default_factory=dict)
