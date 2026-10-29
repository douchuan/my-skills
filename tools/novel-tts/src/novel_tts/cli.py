"""Command-line interface."""

import shutil
import subprocess
import tempfile
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from novel_tts.audio import _make_silence, play_script, render_script
from novel_tts.script import ScriptError, load_script

app = typer.Typer(no_args_is_help=True, help="Render YAML scripts into multi-character narration.")
console = Console()


def _load(path: Path):
    try:
        return load_script(path)
    except ScriptError as exc:
        raise typer.BadParameter(str(exc)) from exc


@app.command()
def validate(script: Path):
    """Validate a YAML narration script without calling a TTS service."""
    loaded = _load(script)
    console.print(
        f"[green]Valid[/green] — {len(loaded.segments)} segments, "
        f"{len(loaded.characters)} characters, provider={loaded.tts.provider}"
    )


@app.command()
def voices(script: Path):
    """Show the speaker-to-voice mapping configured in a script."""
    loaded = _load(script)
    table = Table("Speaker ID", "Display name", "Voice")
    for key, character in loaded.characters.items():
        table.add_row(key, character.name, character.voice)
    console.print(table)


@app.command()
def render(
    script: Path,
    force: bool = typer.Option(False, "--force", help="Regenerate existing audio files."),
):
    """Render all segments to individual audio files."""
    loaded = _load(script)
    try:
        result = render_script(loaded, force=force)
    except Exception as exc:
        console.print(f"[red]Rendering failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    if result.new_count > 0:
        console.print(f"[green]Rendered {result.new_count} new segments to {loaded.output_dir}[/green]")
    else:
        console.print(f"[green]All {len(result.paths)} segments already cached.[/green]")


@app.command()
def regenerate(
    script: Path,
    segment_ids: list[str] = typer.Argument(..., help="Segment IDs to re-render."),
):
    """Re-render specific segments by their IDs, ignoring cached audio."""
    loaded = _load(script)
    valid_ids = {s.id for s in loaded.segments}
    missing = [sid for sid in segment_ids if sid not in valid_ids]
    if missing:
        console.print(f"[red]Unknown segment IDs: {', '.join(missing)}[/red]")
        raise typer.Exit(code=1)
    try:
        result = render_script(loaded, force=True, segment_ids=set(segment_ids))
    except Exception as exc:
        console.print(f"[red]Rendering failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    console.print(f"[green]Re-rendered {result.new_count} segment(s) to {loaded.output_dir}[/green]")


@app.command()
def play(script: Path):
    """Play rendered segments in script order."""
    loaded = _load(script)
    try:
        play_script(loaded)
    except Exception as exc:
        console.print(f"[red]Playback failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc


@app.command(name="assemble")
def assemble(
    script: Path,
    force: bool = typer.Option(False, "--force", help="Regenerate missing segments before assembling."),
    output: str | None = typer.Option(None, "--output", "-o", help="Override output filename."),
):
    """Assemble rendered segments into a single audio file named after the script."""
    loaded = _load(script)

    # Render any missing segments first
    render_result = render_script(loaded, force=force)
    if render_result.new_count > 0:
        console.print(f"[green]Rendered {render_result.new_count} new segments.[/green]")

    extension = "wav" if loaded.tts.format == "wav" else loaded.tts.format
    missing = []
    for segment in loaded.segments:
        seg_path = loaded.output_dir / f"{segment.id}.{extension}"
        if not seg_path.exists():
            missing.append(segment.id)
    if missing:
        console.print(f"[red]Missing audio for segments: {', '.join(missing)}. Run render first.[/red]")
        raise typer.Exit(code=1)

    # Build the ordered playlist with silence for pauses
    playlist: list[Path] = []
    for index, segment in enumerate(loaded.segments):
        seg_path = loaded.output_dir / f"{segment.id}.{extension}"
        playlist.append(seg_path)
        if segment.pause_after > 0:
            silence = loaded.output_dir / f".assemble-pause-{index}.wav"
            _make_silence(silence, segment.pause_after, loaded.tts.sample_rate)
            playlist.append(silence)

    # Determine output path: same name as source YAML, matching audio format
    if output:
        out_path = Path(output)
        if not out_path.is_absolute():
            out_path = script.parent / out_path
    else:
        out_path = script.parent / f"{script.stem}.{extension}"

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        console.print("[red]ffmpeg is required to assemble audio files.[/red]")
        raise typer.Exit(code=1)

    # Convert all files to a uniform WAV format for reliable concatenation
    with tempfile.TemporaryDirectory(prefix="novel-tts-assemble-") as tmpdir:
        tmp_dir = Path(tmpdir)
        wav_files: list[Path] = []
        for idx, p in enumerate(playlist):
            wav_out = tmp_dir / f"{idx:04d}.wav"
            subprocess.run(
                [ffmpeg, "-y", "-i", str(p), "-ar", str(loaded.tts.sample_rate), "-ac", "1", str(wav_out)],
                check=True,
                capture_output=True,
            )
            wav_files.append(wav_out)

        concat_file = tmp_dir / "list.txt"
        concat_file.write_text(
            "".join(f"file '{p.as_posix()}'\n" for p in wav_files),
            encoding="utf-8",
        )

        # Encode to the target format (not just copy)
        if extension == "wav":
            codec_args = ["-c", "copy"]
        elif extension == "mp3":
            codec_args = ["-c:a", "libmp3lame", "-q:a", "2"]
        else:
            codec_args = ["-c:a", "pcm_s16le"]

        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_file),
                *codec_args,
                str(out_path),
            ],
            check=True,
            capture_output=True,
        )

    # Clean up temporary silence files
    for index, segment in enumerate(loaded.segments):
        if segment.pause_after > 0:
            silence = loaded.output_dir / f".assemble-pause-{index}.wav"
            if silence.exists():
                silence.unlink()

    console.print(f"[green]Assembled {len(loaded.segments)} segments → {out_path}[/green]")
