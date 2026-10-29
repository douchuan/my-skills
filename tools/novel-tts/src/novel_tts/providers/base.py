"""Provider interface for speech synthesis."""

from abc import ABC, abstractmethod
from pathlib import Path

from novel_tts.models import Character, Segment, TTSConfig


class TTSProvider(ABC):
    def __init__(self, config: TTSConfig):
        self.config = config

    @abstractmethod
    def synthesize(self, segment: Segment, character: Character, destination: Path) -> None:
        """Synthesize one segment and write audio to destination."""
