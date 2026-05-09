"""
utils.py
~~~~~~~~
Shared utility functions used across the presentation generator pipeline.
"""

import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------

def load_json(file_path: str) -> dict:
    """Load and return JSON data from *file_path*.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    ValueError
        If the file is not valid JSON.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as fh:
        try:
            return json.load(fh)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {file_path}: {exc}") from exc


def validate_input(data: dict) -> None:
    """Validate that *data* contains the required top-level keys.

    Raises
    ------
    ValueError
        If any required key or slide field is missing / invalid.
    """
    if "slides" not in data:
        raise ValueError("Input JSON must contain a 'slides' key.")

    slides = data["slides"]
    if not isinstance(slides, list) or len(slides) == 0:
        raise ValueError("'slides' must be a non-empty list.")

    required_slide_keys = {"id", "type", "title"}
    for i, slide in enumerate(slides):
        missing = required_slide_keys - slide.keys()
        if missing:
            raise ValueError(
                f"Slide at index {i} is missing required keys: {missing}"
            )
        if not isinstance(slide["id"], int):
            raise ValueError(f"Slide {i}: 'id' must be an integer.")


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logger with a human-readable format."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


# ---------------------------------------------------------------------------
# File helpers
# ---------------------------------------------------------------------------

def ensure_dir(path: str) -> str:
    """Create *path* (and parents) if it does not exist; return *path*."""
    os.makedirs(path, exist_ok=True)
    return path


def safe_filename(name: str) -> str:
    """Strip characters that are unsafe in file names and return the result.

    Consecutive unsafe characters are collapsed into a single underscore.
    """
    import re

    return re.sub(r"[^\w\-_ .]+", "_", name).strip()


def write_placeholder_png(file_path: str, width: int = 1280, height: int = 720) -> None:
    """Write a minimal white PNG placeholder image to *file_path*.

    Uses Pillow when available for efficiency; falls back to a hand-crafted
    minimal PNG otherwise.
    """
    try:
        from PIL import Image  # type: ignore

        img = Image.new("RGB", (width, height), color=(255, 255, 255))
        img.save(file_path, "PNG")
        return
    except ImportError:
        pass

    # Fallback: write a tiny 4×4 all-white PNG (minimal valid file).
    import struct
    import zlib

    w, h = 4, 4

    def _chunk(name: bytes, data: bytes) -> bytes:
        c = struct.pack(">I", len(data)) + name + data
        return c + struct.pack(">I", zlib.crc32(name + data) & 0xFFFFFFFF)

    # Each row: filter byte (0) + RGB white pixels
    row = b"\x00" + b"\xff\xff\xff" * w
    raw = row * h
    png = (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
        + _chunk(b"IDAT", zlib.compress(raw))
        + _chunk(b"IEND", b"")
    )
    with open(file_path, "wb") as fh:
        fh.write(png)


# ---------------------------------------------------------------------------
# Progress display
# ---------------------------------------------------------------------------

def print_banner(title: str, width: int = 60) -> None:
    """Print a formatted section banner to stdout."""
    border = "=" * width
    print(f"\n{border}")
    print(f"  {title}")
    print(f"{border}\n")


def print_step(step: int, total: int, description: str) -> None:
    """Print a pipeline step indicator."""
    print(f"  [{step}/{total}] {description} ...")

