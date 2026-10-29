"""Load and validate YAML narration scripts."""

from pathlib import Path
from typing import Any

import yaml

from novel_tts.models import Character, Script, Segment, TTSConfig


class ScriptError(ValueError):
    """Raised when a narration script is invalid."""


def load_script(path: str | Path) -> Script:
    source_path = Path(path).expanduser().resolve()
    try:
        raw = yaml.safe_load(source_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ScriptError(f"Could not read script: {source_path}") from exc
    except yaml.YAMLError as exc:
        raise ScriptError(f"Invalid YAML: {exc}") from exc

    if not isinstance(raw, dict):
        raise ScriptError("The YAML document must be a mapping.")

    title = raw.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ScriptError("'title' must be a non-empty string.")

    tts_raw = raw.get("tts", {})
    if not isinstance(tts_raw, dict):
        raise ScriptError("'tts' must be a mapping.")
    tts = TTSConfig(
        provider=str(tts_raw.get("provider", "qwen")).lower(),
        model=str(tts_raw.get("model", "qwen-audio-3.1-tts-flash")),
        region=str(tts_raw.get("region", "cn-beijing")),
        format=str(tts_raw.get("format", "mp3")).lower(),
        sample_rate=int(tts_raw.get("sample_rate", 24000)),
    )
    if tts.provider not in {"qwen", "azure"}:
        raise ScriptError("'tts.provider' must be 'qwen' or 'azure'.")
    if tts.format not in {"mp3", "wav", "pcm"}:
        raise ScriptError("'tts.format' must be mp3, wav, or pcm.")
    if tts.sample_rate <= 0:
        raise ScriptError("'tts.sample_rate' must be positive.")

    chars_raw = raw.get("characters")
    if not isinstance(chars_raw, dict) or not chars_raw:
        raise ScriptError("'characters' must define at least one character.")
    characters: dict[str, Character] = {}
    for key, value in chars_raw.items():
        if not isinstance(value, dict):
            raise ScriptError(f"Character '{key}' must be a mapping.")
        name = value.get("name", key)
        voice = value.get("voice")
        if not isinstance(voice, str) or not voice.strip():
            raise ScriptError(f"Character '{key}' must define a non-empty 'voice'.")
        characters[str(key)] = Character(name=str(name), voice=voice)

    segments_raw = raw.get("segments")
    if not isinstance(segments_raw, list) or not segments_raw:
        raise ScriptError("'segments' must be a non-empty list.")
    segments: list[Segment] = []
    seen_ids: set[str] = set()
    for index, item in enumerate(segments_raw, start=1):
        if not isinstance(item, dict):
            raise ScriptError(f"Segment {index} must be a mapping.")
        segment_id = str(item.get("id", f"segment-{index:04d}"))
        speaker = item.get("speaker")
        text = item.get("text")
        if segment_id in seen_ids:
            raise ScriptError(f"Duplicate segment id: '{segment_id}'.")
        seen_ids.add(segment_id)
        if speaker not in characters:
            raise ScriptError(f"Segment '{segment_id}' uses unknown speaker '{speaker}'.")
        if not isinstance(text, str) or not text.strip():
            raise ScriptError(f"Segment '{segment_id}' must have non-empty text.")
        rate = float(item.get("rate", 1.0))
        pause_after = float(item.get("pause_after", 0.0))
        if not 0.7 <= rate <= 1.3:
            raise ScriptError(f"Segment '{segment_id}' rate must be between 0.7 and 1.3.")
        if not 0 <= pause_after <= 30:
            raise ScriptError(f"Segment '{segment_id}' pause_after must be between 0 and 30.")
        segments.append(
            Segment(
                id=segment_id,
                speaker=str(speaker),
                text=text.strip(),
                emotion=str(item.get("emotion", "neutral")).lower(),
                rate=rate,
                pause_after=pause_after,
            )
        )

    output_name = str(raw.get("output_dir", f"output/{source_path.stem}"))
    output_dir = Path(output_name)
    if not output_dir.is_absolute():
        output_dir = (source_path.parent / output_dir).resolve()

    return Script(
        title=title.strip(),
        tts=tts,
        characters=characters,
        segments=segments,
        output_dir=output_dir,
        source_path=source_path,
        raw=raw,
    )
