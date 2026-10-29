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
    "neutral": "Read naturally and clearly.",
    "gentle": "Speak gently and warmly.",
    "sad": "Speak sadly, with restrained emotion.",
    "amazed": "Speak with surprise and wonder, as if astonished.",
    "deep_and_loud_shouting": "Shout deeply and loudly with full force.",
    "trembling": "Speak with a trembling, shaky voice.",
    "angry": "Speak angrily with strong emotion.",
    "excited": "Speak with excitement and energy.",
    "sarcastic": "Speak with a mocking, sarcastic tone.",
    "curious": "Sound curious and inquisitive.",
    "like_dracula": "Speak in a dark, eerie, theatrical vampire-like tone.",
    "bored": "Speak in a flat, bored, uninterested tone.",
    "tired": "Speak wearily, with low energy and fatigue.",
    "scornful": "Speak with contempt and disdain.",
    "shouting": "Speak loudly, as if shouting to be heard.",
    "asmr": "Speak very softly and close, in an intimate ASMR whisper.",
    "panicked": "Speak rapidly with panic and alarm.",
    "mischievously": "Speak in a playful, mischievous, teasing tone.",
    "empathetic": "Speak with warmth, care, and deep empathy.",
    "whispers": "Speak in a soft whisper.",
    "reluctantly": "Speak hesitantly and unwillingly, with reluctance.",
    "crying": "Speak while crying, with a tearful, breaking voice.",
    "serious": "Speak in a serious and composed manner.",
    "very_slowly": "Speak very slowly, with long pauses and clear articulation.",
    "very_fast": "Speak very fast, with rapid pacing.",
    "nostalgic": "Speak with wistful longing, as if recalling a distant memory.",
    "somber": "Speak in a grave, gloomy, and solemn tone.",
    "subdued": "Speak in a quiet, restrained, and understated tone.",
    "expectant": "Speak with eager anticipation, as if waiting for something to happen.",
    "longing": "Speak with deep yearning and ache, as if reaching for something out of grasp.",
    "thoughtful": "Speak in a reflective, pensive tone, as if lost in thought.",
    "hopeful": "Speak with bright optimism and belief that things will turn out well.",
    "earnest": "Speak sincerely and earnestly, with genuine conviction and heartfelt honesty.",
    "warm": "Speak warmly and affectionately, with a kind and welcoming tone.",
    "dreamy": "Speak in a soft, hazy, dreamlike tone, as if half-awake or lost in a reverie.",
    "cheerful": "Speak brightly and cheerfully, with a light, upbeat, and smiling tone.",
    "vivid": "Speak vividly and expressively, with lively color and dynamic emphasis.",
    "elated": "Speak with soaring joy and triumphant delight, as if lifted by great happiness.",
    "descriptive": "Speak in an even, narrative tone that paints a clear picture, with steady pacing and careful emphasis on details.",
    "narrator": "Speak in a steady, engaging storytelling tone, guiding the listener through the narrative with clear pacing and balanced emotion.",
    "eager": "Speak with keen enthusiasm and impatience, as if rushing forward to do or say more.",
    "dismissive": "Speak in a curt, offhand tone, waving the matter away as unimportant.",
    "aggrieved": "Speak with a wounded, resentful tone, as if unfairly wronged.",
    "humorous": "Speak in a light, witty, and playful tone, with a smile in the voice.",
    "exasperated": "Speak with irritated frustration, as if at the end of one's patience.",
    "tense": "Speak in a tight, strained tone, with controlled breath and a sense of mounting pressure.",
    "uneasy": "Speak with quiet discomfort and nervous uncertainty, as if something is not quite right.",
    "confused": "Speak with puzzled uncertainty, with hesitant pauses as if trying to make sense of things.",
    "shaky": "Speak in an unsteady, wavering voice, with tremors and uncertain control.",
    "alarmed": "Speak with sudden alarm and urgency, as if startled by a warning or danger.",
    "agitated": "Speak in a restless, unsettled manner, with nervous energy and uneven pacing.",
    "anxious": "Speak with nervous worry and apprehension, as if dreading what may come.",
    "frightened": "Speak with clear fear and dread, with a shaky, shrinking voice.",
    "heartbeat": "Speak in a hushed, pulse-pounding tone, as if the words are timed to a racing heartbeat.",
    "nervous": "Speak with jittery unease and self-conscious hesitation, as if worried about how it will come out.",
    "polite": "Speak in a courteous, well-mannered tone, with measured warmth and restraint.",
    "timid": "Speak in a shy, hesitant, small voice, as if afraid to draw attention.",
    "cold": "Speak in a cool, detached, and unfeeling tone, with flat affect and little warmth.",
    "indifferent": "Speak in a flat, uncaring tone, as if the matter does not matter at all.",
    "horrified": "Speak with intense shock and horror, as if recoiling from something terrible.",
    "choked": "Speak with a tight, constricted throat, words breaking up as if holding back tears or emotion.",
    "hushed": "Speak in a low, quiet tone, as if in a place where sound must be kept down.",
    "numb": "Speak in a hollow, drained tone, with flat affect as if feeling nothing at all.",
    "stunned": "Speak in a dazed, halting manner, with pauses as if too shocked to react.",
    "resolute": "Speak with firm determination and unwavering resolve, steady and unshakable.",
    "daze": "Speak in a foggy, absent-minded tone, as if only half-aware of what is being said.",
    "miserable": "Speak in a deeply wretched, sorrowful tone, weighed down by unhappiness.",
    "anger": "Speak with intense anger, with sharp edges and rising force.",
    "furious": "Speak with explosive rage, fierce and barely contained.",
    "agitated": "Speak in a restless, unsettled manner, with nervous energy and uneven pacing.",
    "quiet": "Speak softly and calmly, with low volume and gentle restraint.",
    "tender": "Speak with soft affection and delicate care, as if handling something precious.",
    "humble": "Speak in a modest, unassuming tone, with no trace of pride or self-importance.",
    "sorrowful": "Speak with deep, quiet grief, full of sadness and loss.",
    "grateful": "Speak with heartfelt thanks and warm appreciation, sincere and touched.",
    "melancholy": "Speak with a soft, pensive sadness, tinged with wistful reflection.",
    "surprised": "Speak with a sudden lift of surprise, as if caught off guard by something unexpected.",
    "firm": "Speak in a steady, decisive tone, with clear conviction and no wavering.",
    "upright": "Speak with moral conviction and dignified integrity, honest and principled.",
    "heavy": "Speak in a weighted, burdened tone, as if each word carries a great weight.",
    "desolate": "Speak in a bleak, empty tone, as if surrounded by loneliness and ruin.",
    "wistful": "Speak with a gentle, bittersweet longing, as if remembering something dear and lost.",
    "mournful": "Speak in a grieving, sorrowful tone, as if in mourning for someone or something lost.",
    "decisive": "Speak with clear determination and resolve, without hesitation.",
    "hush": "Speak in a low, quiet tone, as if trying not to be overheard.",
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
            with destination.open("wb") as audio_file:
                with self.client.audio.tts.connect(**connect_kwargs) as session:
                    session.send_text(segment.text)
                    session.flush()
                    session.stop()
                    for chunk in session.audio_chunks():
                        audio_file.write(chunk)
        except Exception as exc:
            destination.unlink(missing_ok=True)
            # Provide a clearer hint when the voice is incompatible with the model.
            if "InvalidParameter" in str(exc) or "411" in str(exc):
                if self.config.model == "qwen-audio-3.1-tts-flash" and character.voice not in _KNOWN_VOICES_31:
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
