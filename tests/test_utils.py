"""
tests/test_utils.py
~~~~~~~~~~~~~~~~~~~~
Unit tests for src.utils helper functions.
"""

import json
import os
import pytest

import src.utils as utils_module


class TestLoadJson:
    def test_loads_valid_json(self, tmp_path):
        data = {"title": "Test", "slides": [{"id": 1, "type": "title", "title": "T"}]}
        p = tmp_path / "input.json"
        p.write_text(json.dumps(data))
        result = utils_module.load_json(str(p))
        assert result["title"] == "Test"

    def test_raises_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            utils_module.load_json("/nonexistent/path/file.json")

    def test_raises_on_invalid_json(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("{ not valid json }")
        with pytest.raises(ValueError, match="Invalid JSON"):
            utils_module.load_json(str(p))


class TestValidateInput:
    def test_valid_input_passes(self):
        data = {
            "slides": [
                {"id": 1, "type": "title", "title": "Hello"},
            ]
        }
        utils_module.validate_input(data)  # should not raise

    def test_missing_slides_key_raises(self):
        with pytest.raises(ValueError, match="'slides' key"):
            utils_module.validate_input({})

    def test_empty_slides_list_raises(self):
        with pytest.raises(ValueError, match="non-empty list"):
            utils_module.validate_input({"slides": []})

    def test_slide_missing_id_raises(self):
        data = {"slides": [{"type": "title", "title": "T"}]}
        with pytest.raises(ValueError, match="missing required keys"):
            utils_module.validate_input(data)

    def test_slide_missing_type_raises(self):
        data = {"slides": [{"id": 1, "title": "T"}]}
        with pytest.raises(ValueError, match="missing required keys"):
            utils_module.validate_input(data)

    def test_slide_missing_title_raises(self):
        data = {"slides": [{"id": 1, "type": "content"}]}
        with pytest.raises(ValueError, match="missing required keys"):
            utils_module.validate_input(data)

    def test_non_integer_id_raises(self):
        data = {"slides": [{"id": "one", "type": "title", "title": "T"}]}
        with pytest.raises(ValueError, match="'id' must be an integer"):
            utils_module.validate_input(data)


class TestEnsureDir:
    def test_creates_directory(self, tmp_path):
        new_dir = str(tmp_path / "a" / "b" / "c")
        result = utils_module.ensure_dir(new_dir)
        assert os.path.isdir(new_dir)
        assert result == new_dir

    def test_idempotent(self, tmp_path):
        d = str(tmp_path / "existing")
        utils_module.ensure_dir(d)
        utils_module.ensure_dir(d)  # should not raise


class TestSafeFilename:
    def test_strips_unsafe_chars(self):
        result = utils_module.safe_filename("Hello:World/Test?")
        assert ":" not in result
        assert "/" not in result
        assert "?" not in result

    def test_preserves_safe_chars(self):
        result = utils_module.safe_filename("hello_world-test.mp4")
        assert result == "hello_world-test.mp4"

    def test_handles_empty_string(self):
        result = utils_module.safe_filename("")
        assert result == ""

    def test_collapses_consecutive_unsafe_chars(self):
        result = utils_module.safe_filename("a::b")
        assert result == "a_b"


class TestWritePlaceholderPng:
    def test_creates_file(self, tmp_path):
        p = str(tmp_path / "placeholder.png")
        utils_module.write_placeholder_png(p)
        assert os.path.exists(p)
        assert os.path.getsize(p) > 0

    def test_custom_dimensions_accepted(self, tmp_path):
        p = str(tmp_path / "small.png")
        utils_module.write_placeholder_png(p, width=4, height=4)
        assert os.path.exists(p)
