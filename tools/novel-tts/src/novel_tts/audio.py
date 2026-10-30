"""Audio output helpers."""

import shutil
import subprocess
import sys
import time
import wave
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RenderResult:
    """Result of rendering a script."""

    paths: list[Path]  # all segment audio files (cached + new)
    new_count: int  # how many were actually rendered this call


def _render_one(
    provider, segment, character, destination, pause_after
) -> tuple[Path, Exception | None, str | None]:
    """Render a single segment with retry on rate limits. Returns (destination, error_or_None, manifest_entry_or_None)."""
    max_retries = 3
    last_error = None
    for attempt in range(max_retries):
        try:
            provider.synthesize(segment, character, destination)
            entry = f"{segment.id}\t{destination.name}\t{pause_after}"
            print(entry)
            return destination, None, entry
        except RuntimeError as exc:
            last_error = exc
            # Retry on rate limit errors with backoff
            if (
                "RateLimitError" in type(exc).__name__ or "Throttling" in str(exc)
            ) and attempt < max_retries - 1:
                time.sleep(2**attempt)
                continue
            break
    return destination, last_error, None


def render_script(
    script, force: bool = False, segment_ids: set[str] | None = None, max_workers: int = 2
) -> RenderResult:
    from novel_tts.providers import create_provider

    provider = create_provider(
        script.tts.provider,
        config=script.tts,
    )
    script.output_dir.mkdir(parents=True, exist_ok=True)

    # First pass: collect which segments need rendering vs already cached
    to_render: list[tuple] = []
    rendered: list[Path] = []
    manifest_entries: dict[str, str] = {}

    for segment in script.segments:
        extension = "wav" if script.tts.format == "wav" else script.tts.format
        destination = script.output_dir / f"{segment.id}.{extension}"
        force_this = segment.id in segment_ids if segment_ids is not None else force
        entry = f"{segment.id}\t{destination.name}\t{segment.pause_after}"
        if destination.exists() and destination.stat().st_size > 0 and not force_this:
            rendered.append(destination)
            manifest_entries[segment.id] = entry
        else:
            character = script.characters[segment.speaker]
            to_render.append((segment, character, destination))

    # Second pass: render remaining segments concurrently
    if to_render:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(_render_one, provider, seg, char, dest, seg.pause_after): dest
                for seg, char, dest in to_render
            }
            for future in as_completed(futures):
                dest, error, entry = future.result()
                if error:
                    raise error
                rendered.append(dest)
                manifest_entries[dest.stem] = entry

    # Write manifest in original segment order
    manifest_lines = []
    for segment in script.segments:
        if segment.id in manifest_entries:
            manifest_lines.append(manifest_entries[segment.id])
    (script.output_dir / "manifest.tsv").write_text(
        "segment_id\tfile\tpause_after_seconds\n" + "\n".join(manifest_lines) + "\n",
        encoding="utf-8",
    )
    return RenderResult(paths=rendered, new_count=len(to_render))


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
