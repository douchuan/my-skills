"""Command-line interface."""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from novel_tts.audio import play_script, render_script
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
        paths = render_script(loaded, force=force)
    except Exception as exc:
        console.print(f"[red]Rendering failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    console.print(f"[green]Rendered {len(paths)} segments to {loaded.output_dir}[/green]")


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
        paths = render_script(loaded, force=True, segment_ids=set(segment_ids))
    except Exception as exc:
        console.print(f"[red]Rendering failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    console.print(f"[green]Re-rendered {len(paths)} segments to {loaded.output_dir}[/green]")


@app.command()
def play(script: Path):
    """Play rendered segments in script order."""
    loaded = _load(script)
    try:
        play_script(loaded)
    except Exception as exc:
        console.print(f"[red]Playback failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc
