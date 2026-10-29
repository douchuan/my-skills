"""Alibaba Cloud Model Studio Qwen-Audio-TTS provider."""

import os
from pathlib import Path

from novel_tts.models import Character, Segment, TTSConfig
from novel_tts.providers.base import TTSProvider

# Voices confirmed compatible with qwen-audio-3.1-tts-flash.
# Only voices with the _v3.1 suffix work with this model; v3.6 and
# non-versioned voices will cause an InvalidParameter error.
_KNOWN_VOICES_31 = frozenset(
    {
        "longanhuan_v3.1",
        "longanlingxin_v3.1",
        "xunanchuan_v3.1",
        "xuyuyuan_v3.1",
    }
)

_EMOTION_INSTRUCTIONS = {
    # 1. 基础情绪
    "neutral": "Speak naturally and clearly, with a balanced, neutral tone.",
    # 2. 温暖与亲和
    "gentle": "Speak gently and warmly, with a soft and reassuring tone.",
    "empathetic": "Speak with warmth, compassion, and genuine understanding.",
    "tender": "Speak with soft affection and delicate care.",
    "grateful": "Speak with sincere gratitude and heartfelt appreciation.",
    # 3. 快乐与积极
    "cheerful": "Speak brightly and cheerfully, with a light, upbeat tone.",
    "excited": "Speak with energetic excitement and enthusiasm.",
    "hopeful": "Speak with optimism and confidence in a positive outcome.",
    "playful": "Speak in a lighthearted, mischievous, and teasing manner.",
    # 4. 悲伤与失落
    "sad": "Speak sadly, with restrained emotion and a subdued voice.",
    "mournful": "Speak with profound grief, as if mourning a great loss.",
    "melancholy": "Speak with quiet, reflective sadness and wistful longing.",
    "disappointed": "Speak with subdued disappointment and unmet expectations.",
    # 5. 愤怒与对抗
    "annoyed": "Speak with irritation and restrained impatience.",
    "angry": "Speak angrily, with sharp emphasis and strong emotional intensity.",
    "furious": "Speak with explosive rage and barely contained anger.",
    "scornful": "Speak with contempt and disdain.",
    "sarcastic": "Speak with biting irony and a mocking, sarcastic undertone.",
    # 6. 恐惧与紧张
    "anxious": "Speak with nervous worry and apprehension.",
    "frightened": "Speak with clear fear and dread, with a slightly shaky voice.",
    "panicked": "Speak rapidly and breathlessly, conveying intense panic and alarm.",
    "tense": "Speak in a tight, strained voice, conveying pressure and suspense.",
    # 7. 惊讶与思考
    "surprised": "Speak with a sudden lift in tone, as if caught off guard.",
    "amazed": "Speak with astonishment and wonder at something extraordinary.",
    "curious": "Speak with genuine curiosity and an inquisitive tone.",
    "thoughtful": "Speak reflectively and pensively, as if carefully considering an idea.",
    # 8. 严肃与坚定
    "serious": "Speak in a serious, composed, and measured manner.",
    "resolute": "Speak with firm determination and unwavering resolve.",
    "authoritative": "Speak with calm authority, confidence, and control.",
    # 9. 疲惫与冷淡
    "weary": "Speak with low energy and deep physical or emotional fatigue.",
    "indifferent": "Speak in a flat, emotionally detached tone, with little concern.",
    # 10. 神秘与戏剧性
    "mysterious": "Speak in a low, enigmatic tone, creating a sense of mystery.",
}

_DIALECT_INSTRUCTIONS = {
    "chongqing": "Speak in Chongqing dialect (重庆话).",
    "sichuan": "Speak in Sichuan dialect (四川话).",
    "beijing": "Speak with a Beijing accent (北京腔).",
    "dongbei": "Speak with a Northeastern accent (东北话).",
    "cantonese": "Speak in Cantonese (粤语).",
    "shanghai": "Speak with a Shanghai accent (上海话).",
    "tianjin": "Speak in Tianjin dialect (天津话).",
    "henan": "Speak in Henan dialect (河南话).",
    "shaanxi": "Speak in Shaanxi dialect (陕西话).",
    "shandong": "Speak in Shandong dialect (山东话).",
}


class QwenTTSProvider(TTSProvider):
    """Generate one audio file per script segment using the DashScope SDK."""

    def __init__(self, config: TTSConfig):
        super().__init__(config)
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise RuntimeError(
                "DASHSCOPE_API_KEY is not set. Configure your Alibaba Cloud Model Studio API key."
            )

        try:
            import dashscope
        except ImportError as exc:
            raise RuntimeError("Install project dependencies with `uv sync --dev`.") from exc

        self.client = dashscope.Client(
            api_key=api_key,
        )

    def synthesize(self, segment: Segment, character: Character, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        instruction = self._build_instruction(segment)
        parameters = {"instruction": instruction} if instruction else None

        connect_kwargs = {
            "model": self.config.model,
            "voice": character.voice,
            "format": self.config.format,
            "sample_rate": self.config.sample_rate,
        }
        if parameters:
            connect_kwargs["parameters"] = parameters

        try:
            with (
                destination.open("wb") as audio_file,
                self.client.audio.tts.connect(**connect_kwargs) as session,
            ):
                session.send_text(segment.text)
                session.flush()
                session.stop()
                for chunk in session.audio_chunks():
                    audio_file.write(chunk)
        except Exception as exc:
            destination.unlink(missing_ok=True)
            # Provide a clearer hint when the voice is incompatible with the model.
            if (
                ("InvalidParameter" in str(exc) or "411" in str(exc))
                and self.config.model == "qwen-audio-3.1-tts-flash"
                and character.voice not in _KNOWN_VOICES_31
            ):
                raise RuntimeError(
                    f"Voice '{character.voice}' is not compatible with model '{self.config.model}'. "
                    f"Use a _v3.1 voice (e.g. {', '.join(sorted(_KNOWN_VOICES_31))})."
                ) from exc
            raise

        if not destination.exists() or destination.stat().st_size == 0:
            destination.unlink(missing_ok=True)
            raise RuntimeError(
                f"Qwen returned no audio for segment '{segment.id}'. "
                "Check the model, voice, region, API key, and model permissions."
            )

    @staticmethod
    def _build_instruction(segment: Segment) -> str:
        parts = [_EMOTION_INSTRUCTIONS.get(segment.emotion, _EMOTION_INSTRUCTIONS["neutral"])]

        if segment.dialect and segment.dialect in _DIALECT_INSTRUCTIONS:
            parts.append(_DIALECT_INSTRUCTIONS[segment.dialect])

        if segment.rate < 0.95:
            parts.append("Speak at a slower pace.")
        elif segment.rate > 1.05:
            parts.append("Speak at a faster pace.")
        else:
            parts.append("Use a natural speaking pace.")

        return " ".join(parts)
