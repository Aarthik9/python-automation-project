"""
tests/test_subtitle_generator.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Unit tests for src.subtitle_generator.SubtitleGenerator.
"""

import os
import pytest

from src.subtitle_generator import SubtitleGenerator, _format_srt_time


class TestFormatSrtTime:
    def test_zero(self):
        assert _format_srt_time(0.0) == "00:00:00,000"

    def test_one_second(self):
        assert _format_srt_time(1.0) == "00:00:01,000"

    def test_one_minute(self):
        assert _format_srt_time(60.0) == "00:01:00,000"

    def test_one_hour(self):
        assert _format_srt_time(3600.0) == "01:00:00,000"

    def test_millis(self):
        assert _format_srt_time(1.5) == "00:00:01,500"

    def test_large_value(self):
        # 1h 2m 3.456s
        assert _format_srt_time(3723.456) == "01:02:03,456"


@pytest.fixture
def gen(tmp_path):
    return SubtitleGenerator(output_dir=str(tmp_path / "subtitles"))


class TestGenerate:
    def test_creates_srt_file(self, gen):
        path = gen.generate(slide_id=1, text="Hello world.", start_time=0.0, duration=5.0)
        assert os.path.exists(path)
        assert path.endswith(".srt")

    def test_raises_on_empty_text(self, gen):
        with pytest.raises(ValueError, match="subtitle text must not be empty"):
            gen.generate(slide_id=1, text="", start_time=0.0, duration=5.0)

    def test_srt_content_has_timestamps(self, gen):
        path = gen.generate(slide_id=1, text="Hello world.", start_time=0.0, duration=5.0)
        content = open(path).read()
        assert "-->" in content

    def test_srt_content_contains_text(self, gen):
        path = gen.generate(slide_id=2, text="AI is amazing.", start_time=10.0, duration=4.0)
        content = open(path).read()
        assert "AI is amazing" in content

    def test_multiple_sentences(self, gen):
        text = "First sentence. Second sentence. Third sentence."
        path = gen.generate(slide_id=3, text=text, start_time=0.0, duration=15.0)
        content = open(path).read()
        assert "First sentence" in content
        assert "Second sentence" in content
        assert "Third sentence" in content


class TestGenerateAll:
    def test_creates_combined_srt(self, gen):
        slides = [
            {"id": 1, "speaker_notes": "First slide narration."},
            {"id": 2, "speaker_notes": "Second slide narration."},
        ]
        audio_info = [
            {"slide_id": 1, "duration": 5.0},
            {"slide_id": 2, "duration": 6.0},
        ]
        path = gen.generate_all(slides, audio_info)
        assert os.path.exists(path)
        assert path.endswith("presentation.srt")

    def test_skips_slides_without_notes(self, gen):
        slides = [
            {"id": 1, "speaker_notes": ""},
            {"id": 2, "speaker_notes": "Valid narration."},
        ]
        audio_info = [{"slide_id": 2, "duration": 4.0}]
        path = gen.generate_all(slides, audio_info)
        content = open(path).read()
        assert "Valid narration" in content

    def test_second_slide_starts_after_first(self, gen):
        slides = [
            {"id": 1, "speaker_notes": "Slide one."},
            {"id": 2, "speaker_notes": "Slide two."},
        ]
        audio_info = [
            {"slide_id": 1, "duration": 10.0},
            {"slide_id": 2, "duration": 10.0},
        ]
        path = gen.generate_all(slides, audio_info)
        content = open(path).read()
        # Parse all --> timestamps and verify at least one starts at or after 10 s.
        import re
        from src.subtitle_generator import _format_srt_time

        timestamps = re.findall(r"(\d{2}:\d{2}:\d{2},\d{3}) -->", content)
        # Convert "HH:MM:SS,mmm" to seconds for comparison
        def to_seconds(ts: str) -> float:
            h, m, rest = ts.split(":")
            s, ms = rest.split(",")
            return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000

        start_times = [to_seconds(t) for t in timestamps]
        assert any(t >= 10.0 for t in start_times), (
            f"Expected a subtitle starting at ≥ 10 s; found: {start_times}"
        )


class TestSplitIntoSentences:
    def test_splits_on_period(self):
        sentences = SubtitleGenerator._split_into_sentences("Hello. World.")
        assert len(sentences) == 2

    def test_wraps_long_sentence(self):
        long_sentence = "word " * 30  # 150 chars, well over MAX_LINE_LENGTH
        sentences = SubtitleGenerator._split_into_sentences(long_sentence.strip())
        # Should be split into multiple chunks
        assert len(sentences) > 1

    def test_single_short_sentence(self):
        sentences = SubtitleGenerator._split_into_sentences("Hello.")
        assert sentences == ["Hello."]
