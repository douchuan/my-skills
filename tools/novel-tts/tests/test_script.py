"""Tests for YAML script validation."""

from pathlib import Path

import pytest

from novel_tts.script import ScriptError, load_script


def write_script(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "script.yaml"
    path.write_text(content, encoding="utf-8")
    return path


def test_load_valid_script(tmp_path):
    path = write_script(
        tmp_path,
        """
title: Test
tts:
  provider: qwen
characters:
  narrator:
    name: Narrator
    voice: longanhuan_v3.1
segments:
  - id: one
    speaker: narrator
    text: Hello world.
""",
    )
    script = load_script(path)
    assert script.title == "Test"
    assert script.tts.provider == "qwen"
    assert script.segments[0].id == "one"


def test_unknown_speaker_is_rejected(tmp_path):
    path = write_script(
        tmp_path,
        """
title: Test
characters:
  narrator:
    voice: longanhuan_v3.1
segments:
  - speaker: missing
    text: Hello.
""",
    )
    with pytest.raises(ScriptError, match="unknown speaker"):
        load_script(path)


def test_invalid_rate_is_rejected(tmp_path):
    path = write_script(
        tmp_path,
        """
title: Test
characters:
  narrator:
    voice: longanhuan_v3.1
segments:
  - speaker: narrator
    text: Hello.
    rate: 2
""",
    )
    with pytest.raises(ScriptError, match="rate"):
        load_script(path)


def test_duplicate_ids_are_rejected(tmp_path):
    path = write_script(
        tmp_path,
        """
title: Test
characters:
  narrator:
    voice: longanhuan_v3.1
segments:
  - id: same
    speaker: narrator
    text: One.
  - id: same
    speaker: narrator
    text: Two.
""",
    )
    with pytest.raises(ScriptError, match="Duplicate"):
        load_script(path)
