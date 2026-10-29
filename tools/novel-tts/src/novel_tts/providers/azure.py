"""Optional Azure Speech provider."""

import os
from pathlib import Path

from novel_tts.models import Character, Segment, TTSConfig
from novel_tts.providers.base import TTSProvider


class AzureTTSProvider(TTSProvider):
    """Synthesize a segment using Azure Speech SDK."""

    def __init__(self, config: TTSConfig):
        super().__init__(config)
        key = os.getenv("AZURE_SPEECH_KEY")
        region = os.getenv("AZURE_SPEECH_REGION")
        if not key or not region:
            raise RuntimeError("AZURE_SPEECH_KEY and AZURE_SPEECH_REGION must be set.")
        try:
            import azure.cognitiveservices.speech as speechsdk
        except ImportError as exc:
            raise RuntimeError(
                "Azure support is optional. Install it with `uv sync --extra azure`."
            ) from exc
        self.speechsdk = speechsdk
        self.speech_config = speechsdk.SpeechConfig(subscription=key, region=region)

    def synthesize(self, segment: Segment, character: Character, destination: Path) -> None:
        speechsdk = self.speechsdk
        self.speech_config.speech_synthesis_voice_name = character.voice
        audio_config = speechsdk.audio.AudioOutputConfig(filename=str(destination))
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config, audio_config=audio_config
        )
        result = synthesizer.speak_text_async(segment.text).get()
        if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
            details = result.cancellation_details
            raise RuntimeError(f"Azure synthesis failed: {details.reason}: {details.error_details}")
