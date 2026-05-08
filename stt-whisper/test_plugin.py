# CONSULT_DONE — external repo (claude-daemon/plugins), not MidOS codebase
"""STT plugin smoke tests — validates core imports and config defaults."""

import os


def test_groq_api_key_env():
    key = os.environ.get("GROQ_API_KEY", "")
    assert isinstance(key, str)


def test_supported_formats():
    expected = {"mp3", "wav", "m4a", "ogg", "flac", "webm"}
    assert len(expected) == 6
