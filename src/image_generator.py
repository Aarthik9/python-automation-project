"""
image_generator.py
~~~~~~~~~~~~~~~~~~
Renders slide images (PNG) from slide metadata using Pillow.

Supports two slide types:
    ``"title"``   – centred title + subtitle on a gradient background.
    ``"content"`` – title bar with a bulleted list body.

Requires:
    Pillow (pip install Pillow)

Usage::

    from src.image_generator import ImageGenerator

    gen = ImageGenerator(output_dir="output/images")
    path = gen.generate(slide)
"""

import os
import logging
import textwrap
from typing import Tuple

logger = logging.getLogger(__name__)

# Default slide dimensions (16:9 HD)
SLIDE_WIDTH = 1280
SLIDE_HEIGHT = 720

# Content slide text wrapping width (characters per line)
CONTENT_TEXT_WIDTH = 70

# Gradient intensity factor applied to the accent colour overlay
GRADIENT_INTENSITY = 0.4


def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert a CSS hex color string to an RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


class ImageGenerator:
    """Render slide images using Pillow."""

    def __init__(self, output_dir: str = "output/images", theme: dict | None = None):
        """
        Parameters
        ----------
        output_dir:
            Directory where PNG images are saved.
        theme:
            Optional colour / font theme dict (loaded from JSON ``theme``
            key).  Falls back to built-in defaults when omitted.
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        defaults = {
            "background_color": "#1a1a2e",
            "title_color": "#e94560",
            "text_color": "#ffffff",
            "accent_color": "#0f3460",
            "font": "DejaVuSans",
        }
        self.theme = {**defaults, **(theme or {})}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, slide: dict) -> str:
        """Render *slide* as a PNG image and return its file path.

        Parameters
        ----------
        slide:
            Single slide dict from the parsed JSON input.

        Returns
        -------
        str
            Path of the saved PNG file.
        """
        slide_type = slide.get("type", "content")
        if slide_type == "title":
            img = self._render_title_slide(slide)
        else:
            img = self._render_content_slide(slide)

        slide_id = slide["id"]
        file_path = os.path.join(self.output_dir, f"slide_{slide_id:03d}.png")
        img.save(file_path, "PNG")
        logger.info("Slide image saved: %s", file_path)
        return file_path

    def generate_all(self, slides: list) -> list:
        """Generate images for all slides.

        Returns a list of ``{"slide_id": int, "path": str}`` dicts.
        """
        results = []
        for slide in slides:
            # Diagram slides are handled by DiagramGenerator; skip them here
            # unless there is no diagram key (treat as content fallback).
            if slide.get("type") == "diagram" and "diagram" in slide:
                continue
            path = self.generate(slide)
            results.append({"slide_id": slide["id"], "path": path})
        return results

    # ------------------------------------------------------------------
    # Private rendering helpers
    # ------------------------------------------------------------------

    def _render_title_slide(self, slide: dict):
        """Return a PIL Image for a title slide."""
        try:
            from PIL import Image, ImageDraw, ImageFont  # type: ignore
        except ImportError:
            return self._fallback_image(slide["id"], slide.get("title", ""))

        img = Image.new("RGB", (SLIDE_WIDTH, SLIDE_HEIGHT))
        draw = ImageDraw.Draw(img)

        bg = _hex_to_rgb(self.theme["background_color"])
        accent = _hex_to_rgb(self.theme["accent_color"])

        # Gradient background
        for y in range(SLIDE_HEIGHT):
            ratio = y / SLIDE_HEIGHT
            r = int(bg[0] + (accent[0] - bg[0]) * ratio * GRADIENT_INTENSITY)
            g = int(bg[1] + (accent[1] - bg[1]) * ratio * GRADIENT_INTENSITY)
            b = int(bg[2] + (accent[2] - bg[2]) * ratio * GRADIENT_INTENSITY)
            draw.line([(0, y), (SLIDE_WIDTH, y)], fill=(r, g, b))

        # Decorative accent bar
        bar_h = 8
        draw.rectangle(
            [(0, SLIDE_HEIGHT // 2 - 80), (SLIDE_WIDTH, SLIDE_HEIGHT // 2 - 80 + bar_h)],
            fill=_hex_to_rgb(self.theme["title_color"]),
        )

        title_font = self._load_font(60)
        subtitle_font = self._load_font(32)

        title = slide.get("title", "")
        subtitle = slide.get("subtitle", "")

        draw.text(
            (SLIDE_WIDTH // 2, SLIDE_HEIGHT // 2 - 20),
            title,
            font=title_font,
            fill=_hex_to_rgb(self.theme["title_color"]),
            anchor="mm",
        )
        draw.text(
            (SLIDE_WIDTH // 2, SLIDE_HEIGHT // 2 + 60),
            subtitle,
            font=subtitle_font,
            fill=_hex_to_rgb(self.theme["text_color"]),
            anchor="mm",
        )
        return img

    def _render_content_slide(self, slide: dict):
        """Return a PIL Image for a content / bullet-point slide."""
        try:
            from PIL import Image, ImageDraw  # type: ignore
        except ImportError:
            return self._fallback_image(slide["id"], slide.get("title", ""))

        img = Image.new("RGB", (SLIDE_WIDTH, SLIDE_HEIGHT),
                        color=_hex_to_rgb(self.theme["background_color"]))
        draw = ImageDraw.Draw(img)

        # Header bar
        draw.rectangle(
            [(0, 0), (SLIDE_WIDTH, 100)],
            fill=_hex_to_rgb(self.theme["accent_color"]),
        )
        # Accent line beneath header
        draw.rectangle(
            [(0, 100), (SLIDE_WIDTH, 106)],
            fill=_hex_to_rgb(self.theme["title_color"]),
        )

        title_font = self._load_font(44)
        body_font = self._load_font(28)
        bullet_font = self._load_font(24)

        title = slide.get("title", "")
        draw.text(
            (60, 50),
            title,
            font=title_font,
            fill=_hex_to_rgb(self.theme["title_color"]),
            anchor="lm",
        )

        content = slide.get("content", [])
        y = 150
        bullet = "\u2022"
        for item in content:
            wrapped = textwrap.fill(item, width=CONTENT_TEXT_WIDTH)
            for line in wrapped.split("\n"):
                draw.text(
                    (80, y),
                    f"  {bullet}  {line}",
                    font=bullet_font,
                    fill=_hex_to_rgb(self.theme["text_color"]),
                )
                y += 42
            y += 8  # extra spacing between bullets

        return img

    # ------------------------------------------------------------------
    # Font / fallback helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load_font(size: int):
        """Load a PIL font, falling back to the built-in default if needed."""
        try:
            from PIL import ImageFont  # type: ignore

            try:
                return ImageFont.truetype("DejaVuSans.ttf", size)
            except (OSError, IOError):
                pass
            for path in [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/dejavu/DejaVuSans.ttf",
                "/System/Library/Fonts/Helvetica.ttc",
            ]:
                try:
                    return ImageFont.truetype(path, size)
                except (OSError, IOError):
                    pass
            return ImageFont.load_default()
        except ImportError:
            return None

    def _fallback_image(self, slide_id: int, title: str):
        """Return a minimal white image when Pillow is unavailable."""
        from src.utils import write_placeholder_png  # avoid circular at module level

        logger.warning(
            "Pillow not installed – generating placeholder image for slide %d. "
            "Install with: pip install Pillow",
            slide_id,
        )
        path = os.path.join(self.output_dir, f"slide_{slide_id:03d}_placeholder.png")
        write_placeholder_png(path, width=SLIDE_WIDTH, height=SLIDE_HEIGHT)

        # Return a simple object with a .save() no-op so callers don't crash.
        class _FakeImg:
            def save(self, *a, **kw):
                pass

        return _FakeImg()
