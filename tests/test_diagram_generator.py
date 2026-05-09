"""
tests/test_diagram_generator.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Unit tests for src.diagram_generator.DiagramGenerator.
"""

import os
import pytest
from unittest.mock import patch, MagicMock

from src.diagram_generator import DiagramGenerator, _hex_to_rgb_float


class TestHexToRgbFloat:
    def test_black(self):
        result = _hex_to_rgb_float("#000000")
        assert result == (0.0, 0.0, 0.0)

    def test_white(self):
        r, g, b = _hex_to_rgb_float("#ffffff")
        assert abs(r - 1.0) < 1e-9
        assert abs(g - 1.0) < 1e-9
        assert abs(b - 1.0) < 1e-9

    def test_red(self):
        r, g, b = _hex_to_rgb_float("#ff0000")
        assert abs(r - 1.0) < 1e-9
        assert g == 0.0
        assert b == 0.0

    def test_custom_color(self):
        r, g, b = _hex_to_rgb_float("#1a1a2e")
        assert 0 <= r <= 1
        assert 0 <= g <= 1
        assert 0 <= b <= 1


@pytest.fixture
def gen(tmp_path):
    return DiagramGenerator(output_dir=str(tmp_path / "images"))


BAR_SLIDE = {
    "id": 3,
    "type": "diagram",
    "title": "Bar Chart",
    "diagram": {
        "type": "bar",
        "title": "Test Bar",
        "labels": ["A", "B", "C"],
        "values": [10, 20, 30],
        "xlabel": "Category",
        "ylabel": "Value",
        "color": "#e94560",
    },
}

LINE_SLIDE = {
    "id": 5,
    "type": "diagram",
    "title": "Line Chart",
    "diagram": {
        "type": "line",
        "title": "Test Line",
        "labels": ["2020", "2021", "2022"],
        "values": [50, 70, 90],
        "xlabel": "Year",
        "ylabel": "Score",
        "color": "#0f3460",
    },
}

PIE_SLIDE = {
    "id": 6,
    "type": "diagram",
    "title": "Pie Chart",
    "diagram": {
        "type": "pie",
        "title": "Test Pie",
        "labels": ["X", "Y", "Z"],
        "values": [30, 40, 30],
    },
}


class TestGenerateWithMatplotlib:
    """Real matplotlib rendering tests – skipped if matplotlib is absent."""

    pytest.importorskip("matplotlib", reason="matplotlib not installed")

    def test_bar_chart_creates_png(self, gen):
        path = gen.generate(BAR_SLIDE)
        assert os.path.exists(path)
        assert path.endswith(".png")

    def test_line_chart_creates_png(self, gen):
        path = gen.generate(LINE_SLIDE)
        assert os.path.exists(path)
        assert path.endswith(".png")

    def test_pie_chart_creates_png(self, gen):
        path = gen.generate(PIE_SLIDE)
        assert os.path.exists(path)
        assert path.endswith(".png")

    def test_unknown_type_falls_back_to_bar(self, gen):
        slide = {**BAR_SLIDE, "id": 99}
        slide["diagram"] = {**BAR_SLIDE["diagram"], "type": "unknown_chart_type"}
        path = gen.generate(slide)
        assert os.path.exists(path)

    def test_output_in_correct_directory(self, gen):
        path = gen.generate(BAR_SLIDE)
        assert gen.output_dir in path


class TestGenerateAll:
    def test_only_processes_diagram_slides(self, gen):
        slides = [
            {"id": 1, "type": "title", "title": "Title"},
            BAR_SLIDE,
            {"id": 4, "type": "content", "title": "Content", "content": []},
        ]
        pytest.importorskip("matplotlib", reason="matplotlib not installed")
        results = gen.generate_all(slides)
        ids = [r["slide_id"] for r in results]
        assert 3 in ids
        assert 1 not in ids
        assert 4 not in ids

    def test_returns_empty_for_no_diagram_slides(self, gen):
        slides = [
            {"id": 1, "type": "title", "title": "Title"},
            {"id": 2, "type": "content", "title": "Content", "content": []},
        ]
        results = gen.generate_all(slides)
        assert results == []


class TestFallbackWhenMatplotlibMissing:
    def test_writes_placeholder_png(self, gen):
        with patch.dict("sys.modules", {"matplotlib": None, "matplotlib.pyplot": None}):
            path = gen.generate(BAR_SLIDE)
        assert os.path.exists(path)
        assert path.endswith(".png")
