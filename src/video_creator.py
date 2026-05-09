"""
video_creator.py
~~~~~~~~~~~~~~~~
Assembles slide images, audio files, and subtitles into a final MP4
presentation video using MoviePy.

Requires:
    moviepy  (pip install moviepy)
    ffmpeg   (system package – apt install ffmpeg / brew install ffmpeg)

Usage::

    from src.video_creator import VideoCreator

    creator = VideoCreator(output_dir="output")
    path = creator.create(slides, image_info, audio_info, subtitle_path)
"""

import os
import logging
from typing import List

logger = logging.getLogger(__name__)

# Default slide duration when no audio info is available (seconds).
DEFAULT_SLIDE_DURATION = 5.0


class VideoCreator:
    """Assemble a presentation video from images, audio and subtitles."""

    def __init__(self, output_dir: str = "output", fps: int = 24):
        """
        Parameters
        ----------
        output_dir:
            Directory where the final video is written.
        fps:
            Frames per second for the output video.
        """
        self.output_dir = output_dir
        self.fps = fps
        os.makedirs(output_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create(
        self,
        slides: list,
        image_info: list,
        audio_info: list,
        subtitle_path: str | None = None,
        output_filename: str = "presentation.mp4",
    ) -> str:
        """Assemble the final video and return its file path.

        Parameters
        ----------
        slides:
            Original slide dicts from the JSON input (used for ordering).
        image_info:
            List of ``{"slide_id": int, "path": str}`` dicts produced by
            :class:`~src.image_generator.ImageGenerator` and
            :class:`~src.diagram_generator.DiagramGenerator`.
        audio_info:
            List of ``{"slide_id": int, "path": str, "duration": float}``
            dicts produced by
            :class:`~src.audio_generator.AudioGenerator`.
        subtitle_path:
            Optional path to the combined ``.srt`` file.
        output_filename:
            Name of the output video file (inside *output_dir*).

        Returns
        -------
        str
            Path of the rendered MP4 file.
        """
        try:
            from moviepy import ImageClip, AudioFileClip, concatenate_videoclips  # type: ignore
        except ImportError:
            try:
                from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips  # type: ignore
            except ImportError:
                logger.warning(
                    "moviepy is not installed – writing a placeholder video manifest instead. "
                    "Install with: pip install moviepy"
                )
                return self._write_manifest(slides, image_info, audio_info, output_filename)

        image_map = {info["slide_id"]: info["path"] for info in image_info}
        audio_map = {info["slide_id"]: info for info in audio_info}

        if subtitle_path:
            logger.info(
                "Subtitle file available at %s. "
                "Subtitle burning requires ffmpeg post-processing outside this pipeline.",
                subtitle_path,
            )

        clips: List = []
        for slide in slides:
            sid = slide["id"]
            img_path = image_map.get(sid)
            if not img_path or not os.path.exists(img_path):
                logger.warning("No image found for slide %d – skipping.", sid)
                continue

            audio_data = audio_map.get(sid)
            duration = audio_data["duration"] if audio_data else DEFAULT_SLIDE_DURATION

            clip = ImageClip(img_path).with_duration(duration)  # type: ignore[attr-defined]

            if audio_data and os.path.exists(audio_data["path"]):
                try:
                    audio_clip = AudioFileClip(audio_data["path"])
                    clip = clip.with_audio(audio_clip)  # type: ignore[attr-defined]
                except Exception as exc:
                    logger.warning("Could not attach audio for slide %d: %s", sid, exc)

            clips.append(clip)

        if not clips:
            logger.error("No clips were created – aborting video assembly.")
            return ""

        final = concatenate_videoclips(clips, method="compose")

        output_path = os.path.join(self.output_dir, output_filename)
        final.write_videofile(
            output_path,
            fps=self.fps,
            codec="libx264",
            audio_codec="aac",
            logger=None,
        )
        logger.info("Video saved: %s", output_path)
        return output_path

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _write_manifest(
        self,
        slides: list,
        image_info: list,
        audio_info: list,
        output_filename: str,
    ) -> str:
        """Write a JSON manifest describing the video structure."""
        import json

        image_map = {info["slide_id"]: info["path"] for info in image_info}
        audio_map = {info["slide_id"]: info for info in audio_info}

        manifest = {
            "output_file": output_filename,
            "slides": [],
        }
        for slide in slides:
            sid = slide["id"]
            entry = {
                "slide_id": sid,
                "image": image_map.get(sid),
                "audio": audio_map.get(sid, {}).get("path"),
                "duration": audio_map.get(sid, {}).get("duration", DEFAULT_SLIDE_DURATION),
            }
            manifest["slides"].append(entry)

        manifest_path = os.path.join(self.output_dir, output_filename.replace(".mp4", "_manifest.json"))
        with open(manifest_path, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=2)
        logger.info("Video manifest saved: %s", manifest_path)
        return manifest_path
