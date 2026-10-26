"""nspeak - speak text aloud with Microsoft neural voices, without managing audio files.

Audio is synthesized to a temporary MP3, played through the system player, and deleted.
Requires: pip install edge-tts   (network access to the Microsoft speech endpoint)

Usage:
    nspeak "There's a phone call for you."
    nspeak -f notes.txt
    nspeak --voice en-GB-SoniaNeural --rate=-10% "Slower, British."
    nspeak -o hello.mp3 "keep this one"      # writes a file instead of playing
    nspeak --list-voices
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_VOICE = os.environ.get("NSAY_VOICE", "en-US-AvaNeural")
DEFAULT_RATE = "-6%"
DEFAULT_PITCH = "+0Hz"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="nspeak",
        description="Speak text aloud with a neural voice. Temporary audio is deleted after playback.",
    )
    p.add_argument("text", nargs="*", help="text to speak")
    p.add_argument("-f", "--file", help="read the text to speak from this file (UTF-8)")
    p.add_argument(
        "-v",
        "--voice",
        default=DEFAULT_VOICE,
        help=f"voice name (default: {DEFAULT_VOICE})",
    )
    p.add_argument(
        "-r",
        "--rate",
        default=DEFAULT_RATE,
        help="speaking rate, e.g. -10%% or +0%% (default: %(default)s)",
    )
    p.add_argument(
        "-p",
        "--pitch",
        default=DEFAULT_PITCH,
        help=f"pitch, e.g. +0Hz or -20Hz (default: {DEFAULT_PITCH})",
    )
    p.add_argument("-o", "--output", help="save the MP3 here instead of playing it")
    p.add_argument("--player", help="player command to use instead of auto-detection")
    p.add_argument(
        "--list-voices", action="store_true", help="list available voices and exit"
    )
    return p


def read_text(args: argparse.Namespace) -> str:
    if args.file:
        try:
            return Path(args.file).expanduser().read_text(encoding="utf-8")
        except OSError as exc:
            sys.exit(f"nspeak: cannot read {args.file}: {exc}")
    return " ".join(args.text)


def list_voices() -> None:
    import edge_tts

    voices = asyncio.run(edge_tts.list_voices())
    print("English voices (pass any ShortName to --voice):", file=sys.stderr)
    for v in sorted(voices, key=lambda v: (v["Locale"], v["ShortName"])):
        if v["Locale"].startswith("en-"):
            print(f"{v['ShortName']:<28} {v['Gender']:<7} {v['Locale']}")
    print(
        "Other languages: remove the en- filter in list_voices() to see all of them.",
        file=sys.stderr,
    )


async def synthesize(text: str, voice: str, rate: str, pitch: str, out: Path) -> None:
    import edge_tts

    await edge_tts.Communicate(text, voice, rate=rate, pitch=pitch).save(str(out))


def detect_player() -> list[str]:
    """Return the command prefix that plays an audio file on this machine."""
    if platform.system() == "Darwin" and shutil.which("afplay"):
        return ["afplay"]
    for candidate, extra in (
        ("ffplay", ["-nodisp", "-autoexit", "-loglevel", "quiet"]),
        ("mpv", ["--no-video", "--really-quiet"]),
        ("mpg123", ["-q"]),
        ("play", []),
    ):
        if shutil.which(candidate):
            return [candidate, *extra]
    if platform.system() == "Windows":
        return [
            "powershell",
            "-NoProfile",
            "-Command",
            "Add-Type -AssemblyName presentationCore;",
            "$p=New-Object System.Windows.Media.MediaPlayer;",
            "$p.Open([uri]$args[0]);$p.Play();Start-Sleep -s 6",
        ]
    sys.exit("nspeak: no audio player found (install ffplay or pass --player)")


def play(path: Path, player: list[str]) -> None:
    subprocess.run([*player, str(path)], check=False)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.list_voices:
        list_voices()
        return 0

    text = read_text(args).strip()
    if not text:
        sys.exit("nspeak: no text to speak (pass words as arguments or use -f FILE)")

    keep = Path(args.output).expanduser() if args.output else None
    if keep:
        out = keep
    else:
        cache_dir = Path("/tmp/nspeak")
        cache_dir.mkdir(parents=True, exist_ok=True)
        key = hashlib.sha256(
            f"{text}|{args.voice}|{args.rate}|{args.pitch}".encode()
        ).hexdigest()
        out = cache_dir / f"{key}.mp3"
        cached = out.exists()

    try:
        if not keep and not cached:
            asyncio.run(synthesize(text, args.voice, args.rate, args.pitch, out))
        if not keep and out.stat().st_size == 0:
            sys.exit("nspeak: synthesis produced no audio")
        if keep:
            asyncio.run(synthesize(text, args.voice, args.rate, args.pitch, out))
            print(f"nspeak: wrote {keep}")
            return 0
        play(out, [args.player] if args.player else detect_player())
        return 0
    except KeyboardInterrupt:
        return 130
    finally:
        pass  # cache files are kept for reuse
