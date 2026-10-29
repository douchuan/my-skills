# novel-tts

A YAML-driven command-line tool for turning scripted novels into multi-character narrated audio. It supports per-segment speakers, delivery instructions, speaking rate, pauses, and cached audio output.

The project includes an Alibaba Cloud Model Studio Qwen TTS provider. An Azure Speech provider can be added as an optional dependency; the Qwen provider is the primary implementation in this version.

## Features

- Define the narration script in YAML.
- Assign a separate voice to the narrator and each character.
- Set delivery intent, speaking rate, and pauses per segment.
- Render each segment to an individual audio file and reuse cached output.
- Join segments for playback in script order.
- Keep provider-specific behavior behind a small provider interface.

## Requirements

- Python 3.12
- [uv](https://docs.astral.sh/uv/)
- An Alibaba Cloud Model Studio account and a DashScope API key for Qwen TTS

## Installation

```bash
uv python install 3.12
uv sync --dev
```

## Configure Qwen TTS

Create or retrieve an API key in the [Alibaba](https://bailian.console.aliyun.com/), then set it in your `.env` file.

## Validate and render

```bash
uv run novel-tts validate examples/dream-of-red-chamber.yaml
uv run novel-tts render examples/dream-of-red-chamber.yaml
uv run novel-tts play examples/dream-of-red-chamber.yaml
```

Use `--force` to regenerate cached segment audio:

```bash
uv run novel-tts render examples/dream-of-red-chamber.yaml --force
```

Re-render specific segments by ID, leaving other cached audio untouched:

```bash
uv run novel-tts regenerate examples/my-uncle-jules.yaml opening-meet-beggar joseph-intro-story
```

## Choose the provider and model

The script defines a provider in its `tts` section:

```yaml
tts:
  provider: qwen
  model: qwen-audio-3.1-tts-flash
  region: cn-beijing
  format: mp3
  sample_rate: 24000
```

Each character's voice is configured separately:

```yaml
characters:
  narrator:
    name: Narrator
    voice: longanhuan_v3.1
  baoyu:
    name: Baoyu
    voice: longanhuan_v3.1
```

Use voice IDs supported by the selected model. Voice availability and model compatibility can vary. The default example uses a Qwen-Audio-TTS 3.1 model and a documented system voice.

## Emotions and delivery instructions

The script uses a provider-neutral `emotion` field. For Qwen, the provider converts this intent into a natural-language `instruction`. For example, `sad` becomes a request to speak sadly, and `slow` requests a slower delivery.

The instruction is a hint to the model, not a strict guarantee. Model capabilities and accepted parameters vary by model version. The provider also includes the requested rate in the instruction. The `rate` value is a multiplier from `0.7` to `1.3`.

## Audio output

Generated audio is stored under `output/<script-name>/`. Each script segment is rendered to its own audio file. A manifest records the expected order. The `play` command concatenates audio files in script order when `ffplay` is installed, or plays them individually using the platform's available player.

Pause durations are represented as separate silence WAV files. If a script uses MP3 output, pauses are inserted by playback between segments rather than merged into the MP3 stream.

## Commands

```text
novel-tts validate SCRIPT.yaml
novel-tts voices SCRIPT.yaml
novel-tts render SCRIPT.yaml [--force]
novel-tts regenerate SCRIPT.yaml SEGMENT_ID [SEGMENT_ID ...]
novel-tts play SCRIPT.yaml
```

`voices` prints the configured speaker-to-voice mapping. It does not make a remote API request.

`regenerate` re-renders only the named segments, ignoring any cached audio. Use it to fix a single mis-rendered line without re-synthesizing the entire script.

## Development

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

## Notes

- This project calls a cloud TTS service; audio generation incurs usage and may require billing activation.
- Keep API keys out of source control. Do not commit `.env` files or paste credentials into issue reports.