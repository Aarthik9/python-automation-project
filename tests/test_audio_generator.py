"""
tests/test_audio_generator.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Unit tests for src.audio_generator.AudioGenerator.
"""

import os
import pytest
from unittest.mock import MagicMock, patch

from src.audio_generator import AudioGenerator


@pytest.fixture
def audio_gen(tmp_path):
    return AudioGenerator(output_dir=str(tmp_path / "audio"))


class TestEstimateDuration:
    def test_short_text(self):
        # 13 words ÷ 130 wpm × 60 = 6 seconds
        text = "This is a short sentence with thirteen words in total here now."
        duration = AudioGenerator._estimate_duration(text)
        assert duration > 1.0

    def test_empty_text_returns_one(self):
        assert AudioGenerator._estimate_duration("") == 1.0

    def test_longer_text_longer_duration(self):
        short = "Hello world."
        long_text = " ".join(["word"] * 260)  # 260 words → 2 minutes
        assert AudioGenerator._estimate_duration(long_text) > AudioGenerator._estimate_duration(short)


class TestWritePlaceholder:
    def test_creates_file(self, tmp_path):
        path = str(tmp_path / "test.mp3")
        AudioGenerator._write_placeholder(path)
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0


class TestGenerate:
    def test_raises_on_empty_text(self, audio_gen):
        with pytest.raises(ValueError, match="narration text must not be empty"):
            audio_gen.generate(slide_id=1, text="")

    def test_raises_on_whitespace_only_text(self, audio_gen):
        with pytest.raises(ValueError, match="narration text must not be empty"):
            audio_gen.generate(slide_id=1, text="   ")

    def test_returns_path_and_duration_with_gtts_mocked(self, audio_gen):
        mock_tts_instance = MagicMock()
        mock_tts_instance.save.side_effect = lambda p: open(p, "wb").close()
        mock_tts_class = MagicMock(return_value=mock_tts_instance)
        # gTTS is imported inside the function body, so patch the class in its home module.
        with patch("gtts.gTTS", mock_tts_class):
            path, duration = audio_gen.generate(slide_id=1, text="Hello world this is a test.")
        assert path.endswith("slide_001.mp3")
        assert duration > 0.0

    def test_falls_back_to_placeholder_when_gtts_missing(self, audio_gen):
        with patch.dict("sys.modules", {"gtts": None}):
            path, duration = audio_gen.generate(slide_id=2, text="Fallback test sentence.")
        assert os.path.exists(path)
        assert duration > 0.0


class TestGenerateAll:
    def test_skips_slides_without_notes(self, audio_gen):
        slides = [
            {"id": 1, "speaker_notes": ""},
            {"id": 2, "speaker_notes": "Valid narration text here."},
        ]
        with patch.dict("sys.modules", {"gtts": None}):
            results = audio_gen.generate_all(slides)
        # Only slide 2 has notes
        assert len(results) == 1
        assert results[0]["slide_id"] == 2

    def test_returns_all_when_notes_present(self, audio_gen):
        slides = [
            {"id": 1, "speaker_notes": "First slide narration."},
            {"id": 2, "speaker_notes": "Second slide narration."},
        ]
        with patch.dict("sys.modules", {"gtts": None}):
            results = audio_gen.generate_all(slides)
        assert len(results) == 2
