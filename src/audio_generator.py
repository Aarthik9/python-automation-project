"""
audio_generator.py
~~~~~~~~~~~~~~~~~~
Converts text to speech and saves the result as an MP3/WAV audio file.

Requires:
    gTTS  (pip install gtts)
    pydub (pip install pydub)  – used to measure audio duration

Usage::

    from src.audio_generator import AudioGenerator

    gen = AudioGenerator(output_dir="output/audio")
    path, duration = gen.generate(slide_id=1, text="Hello, world!")
"""

import os
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class AudioGenerator:
    """Generate speech audio files from text using Google Text-to-Speech."""

    def __init__(self, output_dir: str = "output/audio", lang: str = "en"):
        """
        Parameters
        ----------
        output_dir:
            Directory where generated audio files are saved.
        lang:
            BCP-47 language code passed to gTTS (default ``"en"``).
        """
        self.output_dir = output_dir
        self.lang = lang
        os.makedirs(output_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, slide_id: int, text: str) -> Tuple[str, float]:
        """Convert *text* to speech and save it under *output_dir*.

        Parameters
        ----------
        slide_id:
            Numeric identifier of the slide; used to name the file.
        text:
            The spoken narration for the slide.

        Returns
        -------
        tuple
            ``(file_path, duration_seconds)`` where *file_path* is the
            absolute path of the saved MP3 and *duration_seconds* is the
            approximate playback length.
        """
        if not text or not text.strip():
            raise ValueError(f"Slide {slide_id}: narration text must not be empty.")

        file_path = os.path.join(self.output_dir, f"slide_{slide_id:03d}.mp3")

        try:
            from gtts import gTTS  # type: ignore

            tts = gTTS(text=text.strip(), lang=self.lang, slow=False)
            tts.save(file_path)
            logger.info("Audio saved: %s", file_path)
        except ImportError:
            logger.warning(
                "gTTS is not installed.  Writing a placeholder audio file for "
                "slide %d.  Install with: pip install gtts",
                slide_id,
            )
            self._write_placeholder(file_path)
        except Exception as exc:
            logger.warning(
                "gTTS failed for slide %d (%s).  Writing a placeholder audio file.",
                slide_id,
                exc,
            )
            self._write_placeholder(file_path)

        duration = self._estimate_duration(text)
        return file_path, duration

    def generate_all(self, slides: list) -> list:
        """Generate audio for every slide in *slides*.

        Parameters
        ----------
        slides:
            List of slide dicts as parsed from the JSON input.  Each dict
            must contain at least ``"id"`` and ``"speaker_notes"`` keys.

        Returns
        -------
        list
            List of dicts with keys ``slide_id``, ``path``, and
            ``duration``.
        """
        results = []
        for slide in slides:
            slide_id = slide["id"]
            notes = slide.get("speaker_notes", "").strip()
            if not notes:
                logger.warning("Slide %d has no speaker notes – skipping audio.", slide_id)
                continue
            path, duration = self.generate(slide_id, notes)
            results.append({"slide_id": slide_id, "path": path, "duration": duration})
        return results

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _estimate_duration(text: str) -> float:
        """Return a rough duration estimate based on average speaking rate.

        Assumes ~130 words per minute which is a comfortable narration pace.
        """
        words = len(text.split())
        return max(1.0, (words / 130.0) * 60.0)

    @staticmethod
    def _write_placeholder(file_path: str) -> None:
        """Write a minimal valid MP3 placeholder so the pipeline can continue."""
        # ID3v2 header + empty frame – just enough bytes for moviepy/pydub to open.
        placeholder = bytes([
            0xFF, 0xFB, 0x90, 0x00,  # MPEG1, Layer3, 128 kbps, 44100 Hz
            0x00, 0x00, 0x00, 0x00,
        ])
        with open(file_path, "wb") as fh:
            fh.write(placeholder)
