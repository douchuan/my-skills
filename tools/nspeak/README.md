# nspeak

Speak text aloud from the command line using Microsoft's neural TTS voices — no audio file to name, manage, or clean up.

`nspeak` synthesizes speech to a temporary MP3, plays it through your system's default player, and deletes the file the moment playback ends. You type the sentence; it handles the rest.

```console
$ nspeak "There's a phone call for you."
$ nspeak -f notes.txt
$ nspeak --voice en-GB-SoniaNeural --rate=-10% "Slower, and British."
```

## Install

```console
pip install edge-tts
curl -O https://raw.githubusercontent.com/<you>/nspeak/main/nspeak.py
chmod +x nspeak.py
mv nspeak.py ~/.local/bin/nspeak        # anything on PATH
```

Requires Python 3.9+ and network access to the Microsoft speech endpoint.

## Options

| Flag | Meaning |
| --- | --- |
| `text` | words to speak (quote them) |
| `-f, --file FILE` | read the text from a UTF-8 file instead |
| `-v, --voice NAME` | voice, default `en-US-AvaNeural` |
| `-r, --rate RATE` | speaking rate, e.g. `-10%`, default `-6%` |
| `-p, --pitch PITCH` | pitch, e.g. `-20Hz`, default `+0Hz` |
| `-o, --output FILE` | save the MP3 instead of playing it |
| `--player CMD` | use this player command instead of auto-detection |
| `--list-voices` | list the English voices and exit |

Voice can also come from the environment: `NSAY_VOICE=en-US-AndrewNeural nspeak "text"`.

## How it works

- `edge_tts.Communicate(text, voice, rate, pitch).save(path)` streams the audio to a file; the
  library only writes to disk, it does not play.
- The file goes to `tempfile.mkstemp(prefix="nspeak-", suffix=".mp3")` and is unlinked in a
  `finally` block, so Ctrl-C does not leave anything behind.
- Playback is `afplay` on macOS, then `ffplay` / `mpv` / `mpg123` on Linux, with a PowerShell
  `MediaPlayer` fallback on Windows. `--player` overrides the choice.

## Voices worth trying

`en-US-AvaNeural` (warm, neutral), `en-US-AndrewNeural` (calmer, male), `en-US-AriaNeural`
(brighter), `en-GB-SoniaNeural` (British), `en-AU-NatashaNeural` (Australian).

## Notes

- Writing the text well matters as much as the voice: short sentences, normal punctuation, and
  spelled-out numbers and abbreviations read better than the opposite.
- `-6%` rate is the default because the stock rate sounds rushed for language practice; `0%` is
  brisker.
- This wraps [`edge-tts`](https://github.com/rany2/edge-tts) (MIT), an unofficial client for the
  read-aloud endpoint of Microsoft Edge. It needs network access, and it is not affiliated with or
  endorsed by Microsoft — check their terms before relying on it commercially.

## License

MIT, if you want the same terms as the dependency. Change this section if you pick another.
