"""Audio output helpers."""

import shutil
import subprocess
import sys
import wave
from pathlib import Path


def render_script(script, force: bool = False, segment_ids: set[str] | None = None) -> list[Path]:
    from novel_tts.providers import create_provider

    provider = create_provider(
        script.tts.provider,
        config=script.tts,
    )
    script.output_dir.mkdir(parents=True, exist_ok=True)
    rendered: list[Path] = []
    manifest_lines = []
    for segment in script.segments:
        extension = "wav" if script.tts.format == "wav" else script.tts.format
        destination = script.output_dir / f"{segment.id}.{extension}"
        # Skip existing files only if not forced and not in the selective set
        force_this = force or (segment_ids is not None and segment.id in segment_ids)
        if destination.exists() and destination.stat().st_size > 0 and not force_this:
            rendered.append(destination)
            manifest_lines.append(f"{segment.id}\t{destination.name}\t{segment.pause_after}")
            continue
        character = script.characters[segment.speaker]
        provider.synthesize(segment, character, destination)
        rendered.append(destination)
        manifest_lines.append(f"{segment.id}\t{destination.name}\t{segment.pause_after}")
    (script.output_dir / "manifest.tsv").write_text(
        "segment_id\tfile\tpause_after_seconds\n" + "\n".join(manifest_lines) + "\n",
        encoding="utf-8",
    )
    return rendered


def _make_silence(path: Path, duration: float, sample_rate: int = 24000) -> None:
    frames = int(duration * sample_rate)
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(b"\x00\x00" * frames)


def play_script(script) -> None:
    player = shutil.which("ffplay")
    if player:
        playlist = []
        for index, segment in enumerate(script.segments):
            extension = "wav" if script.tts.format == "wav" else script.tts.format
            path = script.output_dir / f"{segment.id}.{extension}"
            if not path.exists():
                raise FileNotFoundError(f"Audio file missing: {path}. Run render first.")
            playlist.append(path)
            if segment.pause_after > 0:
                silence = script.output_dir / f".pause-{index}.wav"
                _make_silence(silence, segment.pause_after, script.tts.sample_rate)
                playlist.append(silence)
        concat_file = script.output_dir / "playback-list.txt"
        concat_file.write_text(
            "".join(f"file '{p.as_posix()}'\n" for p in playlist), encoding="utf-8"
        )
        subprocess.run(
            [player, "-nodisp", "-autoexit", "-f", "concat", "-safe", "0", "-i", str(concat_file)],
            check=False,
        )
        return

    if sys.platform == "darwin" and shutil.which("afplay"):
        for segment in script.segments:
            extension = "wav" if script.tts.format == "wav" else script.tts.format
            path = script.output_dir / f"{segment.id}.{extension}"
            subprocess.run(["afplay", str(path)], check=False)
        return

    raise RuntimeError("Install ffplay (recommended) or use a platform audio player manually.")
