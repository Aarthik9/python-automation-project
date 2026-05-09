"""
tests/test_image_generator.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Unit tests for src.image_generator.ImageGenerator.
"""

import os
import pytest
from unittest.mock import patch, MagicMock

from src.image_generator import ImageGenerator, _hex_to_rgb


class TestHexToRgb:
    def test_black(self):
        assert _hex_to_rgb("#000000") == (0, 0, 0)

    def test_white(self):
        assert _hex_to_rgb("#ffffff") == (255, 255, 255)

    def test_red(self):
        assert _hex_to_rgb("#ff0000") == (255, 0, 0)

    def test_no_hash(self):
        assert _hex_to_rgb("00ff00") == (0, 255, 0)

    def test_custom_color(self):
        assert _hex_to_rgb("#1a1a2e") == (26, 26, 46)


@pytest.fixture
def gen(tmp_path):
    return ImageGenerator(output_dir=str(tmp_path / "images"))


TITLE_SLIDE = {
    "id": 1,
    "type": "title",
    "title": "Test Title",
    "subtitle": "Test Subtitle",
}

CONTENT_SLIDE = {
    "id": 2,
    "type": "content",
    "title": "Content Slide",
    "content": ["Bullet one", "Bullet two", "Bullet three"],
}

DIAGRAM_SLIDE = {
    "id": 3,
    "type": "diagram",
    "title": "Diagram",
    "diagram": {"type": "bar", "labels": ["A"], "values": [10]},
}


class TestGenerateWithPillow:
    """Tests that exercise the real Pillow path (skipped if Pillow absent)."""

    pytest.importorskip("PIL", reason="Pillow not installed")

    def test_title_slide_creates_png(self, gen):
        path = gen.generate(TITLE_SLIDE)
        assert os.path.exists(path)
        assert path.endswith(".png")

    def test_content_slide_creates_png(self, gen):
        path = gen.generate(CONTENT_SLIDE)
        assert os.path.exists(path)
        assert path.endswith(".png")

    def test_output_in_correct_directory(self, gen):
        path = gen.generate(TITLE_SLIDE)
        assert gen.output_dir in path


class TestGenerateAll:
    def test_skips_diagram_slides_with_diagram_key(self, gen):
        slides = [TITLE_SLIDE, CONTENT_SLIDE, DIAGRAM_SLIDE]
        results = gen.generate_all(slides)
        ids = [r["slide_id"] for r in results]
        assert 3 not in ids   # diagram slide should be skipped
        assert 1 in ids
        assert 2 in ids

    def test_diagram_slide_without_diagram_key_not_skipped(self, gen):
        slide_no_diagram = {
            "id": 4,
            "type": "diagram",
            "title": "No Diagram Key",
            "content": ["Some text"],
        }
        results = gen.generate_all([slide_no_diagram])
        ids = [r["slide_id"] for r in results]
        assert 4 in ids


class TestTheme:
    def test_custom_theme_applied(self, tmp_path):
        custom_theme = {"background_color": "#ffffff", "title_color": "#000000",
                        "text_color": "#333333", "accent_color": "#999999"}
        gen = ImageGenerator(output_dir=str(tmp_path / "images"), theme=custom_theme)
        assert gen.theme["background_color"] == "#ffffff"
        assert gen.theme["title_color"] == "#000000"

    def test_default_theme_used_when_none(self, tmp_path):
        gen = ImageGenerator(output_dir=str(tmp_path / "images"))
        assert gen.theme["background_color"] == "#1a1a2e"
