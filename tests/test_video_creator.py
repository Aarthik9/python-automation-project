"""
tests/test_video_creator.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Unit tests for src.video_creator.VideoCreator.
"""

import json
import os
import pytest
from unittest.mock import patch, MagicMock

from src.video_creator import VideoCreator, DEFAULT_SLIDE_DURATION


@pytest.fixture
def creator(tmp_path):
    return VideoCreator(output_dir=str(tmp_path / "output"))


SLIDES = [
    {"id": 1, "type": "title", "title": "Title Slide"},
    {"id": 2, "type": "content", "title": "Content Slide"},
]

IMAGE_INFO = [
    {"slide_id": 1, "path": "/fake/slide_001.png"},
    {"slide_id": 2, "path": "/fake/slide_002.png"},
]

AUDIO_INFO = [
    {"slide_id": 1, "path": "/fake/slide_001.mp3", "duration": 5.0},
    {"slide_id": 2, "path": "/fake/slide_002.mp3", "duration": 7.0},
]


class TestWriteManifest:
    """VideoCreator._write_manifest – always available without moviepy."""

    def test_creates_manifest_json(self, creator):
        path = creator._write_manifest(SLIDES, IMAGE_INFO, AUDIO_INFO, "presentation.mp4")
        assert os.path.exists(path)
        assert path.endswith("_manifest.json")

    def test_manifest_contains_all_slides(self, creator):
        path = creator._write_manifest(SLIDES, IMAGE_INFO, AUDIO_INFO, "presentation.mp4")
        data = json.loads(open(path).read())
        ids = [s["slide_id"] for s in data["slides"]]
        assert 1 in ids
        assert 2 in ids

    def test_manifest_contains_image_paths(self, creator):
        path = creator._write_manifest(SLIDES, IMAGE_INFO, AUDIO_INFO, "presentation.mp4")
        data = json.loads(open(path).read())
        for slide in data["slides"]:
            if slide["slide_id"] == 1:
                assert slide["image"] == "/fake/slide_001.png"

    def test_manifest_contains_duration(self, creator):
        path = creator._write_manifest(SLIDES, IMAGE_INFO, AUDIO_INFO, "presentation.mp4")
        data = json.loads(open(path).read())
        durations = {s["slide_id"]: s["duration"] for s in data["slides"]}
        assert durations[1] == 5.0
        assert durations[2] == 7.0

    def test_slide_without_audio_uses_default_duration(self, creator):
        path = creator._write_manifest(SLIDES, IMAGE_INFO, [], "presentation.mp4")
        data = json.loads(open(path).read())
        for slide in data["slides"]:
            assert slide["duration"] == DEFAULT_SLIDE_DURATION


class TestCreate:
    """VideoCreator.create – falls back to manifest when moviepy absent."""

    def test_falls_back_to_manifest_when_moviepy_missing(self, creator):
        with patch.dict(
            "sys.modules",
            {
                "moviepy": None,
                "moviepy.editor": None,
            },
        ):
            path = creator.create(
                slides=SLIDES,
                image_info=IMAGE_INFO,
                audio_info=AUDIO_INFO,
                output_filename="presentation.mp4",
            )
        assert os.path.exists(path)
        assert path.endswith("_manifest.json")
