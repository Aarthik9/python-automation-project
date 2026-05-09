"""
subtitle_generator.py
~~~~~~~~~~~~~~~~~~~~~
Generates SRT subtitle files from timed slide narration text.

No external dependencies beyond the Python standard library.

Usage::

    from src.subtitle_generator import SubtitleGenerator

    gen = SubtitleGenerator(output_dir="output/subtitles")
    path = gen.generate(slide_id=1, text="Hello world.", start_time=0.0, duration=3.5)
"""

import os
import logging
from typing import List

logger = logging.getLogger(__name__)

# Gap in seconds between consecutive subtitle entries.
SUBTITLE_GAP_SECONDS = 0.05


def _format_srt_time(seconds: float) -> str:
    """Convert floating-point *seconds* to ``HH:MM:SS,mmm`` SRT timestamp."""
    millis = int(round(seconds * 1000))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1_000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


class SubtitleGenerator:
    """Create SRT subtitle files from slide narration text."""

    # Maximum number of characters per subtitle line before wrapping.
    MAX_LINE_LENGTH = 80

    def __init__(self, output_dir: str = "output/subtitles"):
        """
        Parameters
        ----------
        output_dir:
            Directory where ``.srt`` files are written.
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        slide_id: int,
        text: str,
        start_time: float,
        duration: float,
    ) -> str:
        """Write an SRT file for a single slide.

        Parameters
        ----------
        slide_id:
            Numeric slide identifier used in the filename.
        text:
            Full narration text for the slide.
        start_time:
            Absolute start time of the slide in seconds (within the final
            video timeline).
        duration:
            How long (seconds) the slide is displayed / audio plays.

        Returns
        -------
        str
            Path of the written ``.srt`` file.
        """
        if not text or not text.strip():
            raise ValueError(f"Slide {slide_id}: subtitle text must not be empty.")

        sentences = self._split_into_sentences(text.strip())
        entries = self._distribute_sentences(sentences, start_time, duration)
        srt_content = self._build_srt(entries)

        file_path = os.path.join(self.output_dir, f"slide_{slide_id:03d}.srt")
        with open(file_path, "w", encoding="utf-8") as fh:
            fh.write(srt_content)

        logger.info("Subtitles saved: %s", file_path)
        return file_path

    def generate_all(self, slides: list, audio_info: list) -> str:
        """Generate a single combined SRT file for the entire presentation.

        Parameters
        ----------
        slides:
            Slide dicts from the JSON input (must have ``id`` and
            ``speaker_notes``).
        audio_info:
            List of dicts returned by
            :meth:`~src.audio_generator.AudioGenerator.generate_all`,
            each containing ``slide_id`` and ``duration``.

        Returns
        -------
        str
            Path of the combined ``presentation.srt`` file.
        """
        duration_map = {info["slide_id"]: info["duration"] for info in audio_info}

        all_entries: List[dict] = []
        counter = 1
        cursor = 0.0

        for slide in slides:
            slide_id = slide["id"]
            text = slide.get("speaker_notes", "").strip()
            if not text:
                continue
            duration = duration_map.get(slide_id, self._estimate_duration(text))
            sentences = self._split_into_sentences(text)
            entries = self._distribute_sentences(sentences, cursor, duration, start_index=counter)
            all_entries.extend(entries)
            counter += len(entries)
            cursor += duration

        srt_content = self._build_srt(all_entries)
        file_path = os.path.join(self.output_dir, "presentation.srt")
        with open(file_path, "w", encoding="utf-8") as fh:
            fh.write(srt_content)

        logger.info("Combined subtitles saved: %s", file_path)
        return file_path

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _split_into_sentences(text: str) -> List[str]:
        """Naively split *text* into sentences at punctuation boundaries."""
        import re

        raw = re.split(r"(?<=[.!?])\s+", text)
        sentences = []
        for sentence in raw:
            sentence = sentence.strip()
            if not sentence:
                continue
            # Wrap long sentences at MAX_LINE_LENGTH characters.
            if len(sentence) > SubtitleGenerator.MAX_LINE_LENGTH:
                words = sentence.split()
                line, chunks = [], []
                for word in words:
                    if len(" ".join(line + [word])) > SubtitleGenerator.MAX_LINE_LENGTH:
                        chunks.append(" ".join(line))
                        line = [word]
                    else:
                        line.append(word)
                if line:
                    chunks.append(" ".join(line))
                sentences.extend(chunks)
            else:
                sentences.append(sentence)
        return sentences or [text]

    @staticmethod
    def _distribute_sentences(
        sentences: List[str],
        start_time: float,
        total_duration: float,
        start_index: int = 1,
    ) -> List[dict]:
        """Evenly distribute *sentences* across *total_duration* seconds."""
        if not sentences:
            return []
        per = total_duration / len(sentences)
        entries = []
        for i, sentence in enumerate(sentences):
            t_start = start_time + i * per
            t_end = t_start + per - SUBTITLE_GAP_SECONDS  # small gap between subtitles
            entries.append(
                {
                    "index": start_index + i,
                    "start": t_start,
                    "end": t_end,
                    "text": sentence,
                }
            )
        return entries

    @staticmethod
    def _build_srt(entries: List[dict]) -> str:
        """Render a list of subtitle entry dicts as an SRT string."""
        lines = []
        for entry in entries:
            lines.append(str(entry["index"]))
            lines.append(
                f"{_format_srt_time(entry['start'])} --> {_format_srt_time(entry['end'])}"
            )
            lines.append(entry["text"])
            lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _estimate_duration(text: str) -> float:
        """Estimate duration from word count (130 wpm)."""
        return max(1.0, (len(text.split()) / 130.0) * 60.0)
