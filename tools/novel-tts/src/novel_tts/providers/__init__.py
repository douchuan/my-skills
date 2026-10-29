"""Speech synthesis provider implementations."""

from novel_tts.providers.base import TTSProvider
from novel_tts.providers.qwen import QwenTTSProvider


def create_provider(provider_name: str, **kwargs) -> TTSProvider:
    name = provider_name.lower()
    if name == "qwen":
        return QwenTTSProvider(**kwargs)
    if name == "azure":
        from novel_tts.providers.azure import AzureTTSProvider

        return AzureTTSProvider(**kwargs)
    raise ValueError(f"Unsupported TTS provider: {provider_name}")
