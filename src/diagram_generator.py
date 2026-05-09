"""
diagram_generator.py
~~~~~~~~~~~~~~~~~~~~
Renders bar and line chart images from slide diagram metadata using
matplotlib.

Supported chart types (``diagram.type``):
    ``"bar"``  – vertical bar chart
    ``"line"`` – line chart with markers
    ``"pie"``  – pie chart

Requires:
    matplotlib (pip install matplotlib)

Usage::

    from src.diagram_generator import DiagramGenerator

    gen = DiagramGenerator(output_dir="output/images")
    path = gen.generate(slide)
"""

import os
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# Proportional vertical offset for bar value labels (relative to max bar height).
LABEL_OFFSET_RATIO = 0.01


def _hex_to_rgb_float(hex_color: str) -> Tuple[float, float, float]:
    """Return an (R, G, B) tuple with values in [0, 1]."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) / 255.0 for i in (0, 2, 4))  # type: ignore[return-value]


class DiagramGenerator:
    """Generate chart / diagram images using matplotlib."""

    def __init__(self, output_dir: str = "output/images", theme: dict | None = None):
        """
        Parameters
        ----------
        output_dir:
            Directory where diagram PNG files are saved.
        theme:
            Optional colour theme dict from the JSON ``theme`` key.
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        defaults = {
            "background_color": "#1a1a2e",
            "title_color": "#e94560",
            "text_color": "#ffffff",
            "accent_color": "#0f3460",
        }
        self.theme = {**defaults, **(theme or {})}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, slide: dict) -> str:
        """Render a diagram for *slide* and return its image file path.

        Parameters
        ----------
        slide:
            A slide dict that must contain a ``"diagram"`` sub-dict with at
            least ``"type"``, ``"labels"``, and ``"values"`` keys.

        Returns
        -------
        str
            Path of the saved PNG file.
        """
        diagram = slide.get("diagram", {})
        chart_type = diagram.get("type", "bar")

        try:
            import matplotlib  # type: ignore
            matplotlib.use("Agg")  # non-interactive backend
            import matplotlib.pyplot as plt  # type: ignore
        except ImportError:
            logger.warning(
                "matplotlib is not installed – skipping diagram for slide %d. "
                "Install with: pip install matplotlib",
                slide["id"],
            )
            return self._write_placeholder(slide["id"])

        fig = self._create_figure()

        if chart_type == "bar":
            ax = self._plot_bar(fig, diagram)
        elif chart_type == "line":
            ax = self._plot_line(fig, diagram)
        elif chart_type == "pie":
            ax = self._plot_pie(fig, diagram)
        else:
            logger.warning("Unknown diagram type '%s' – falling back to bar.", chart_type)
            ax = self._plot_bar(fig, diagram)

        self._style_axes(ax, diagram, chart_type)

        slide_id = slide["id"]
        file_path = os.path.join(self.output_dir, f"slide_{slide_id:03d}.png")
        fig.savefig(file_path, bbox_inches="tight", dpi=150)
        plt.close(fig)
        logger.info("Diagram saved: %s", file_path)
        return file_path

    def generate_all(self, slides: list) -> list:
        """Generate diagrams for every slide that contains a ``diagram`` key.

        Returns
        -------
        list
            List of dicts with ``slide_id`` and ``path``.
        """
        results = []
        for slide in slides:
            if slide.get("type") == "diagram" and "diagram" in slide:
                path = self.generate(slide)
                results.append({"slide_id": slide["id"], "path": path})
        return results

    # ------------------------------------------------------------------
    # Private rendering helpers
    # ------------------------------------------------------------------

    def _create_figure(self):
        """Create a styled matplotlib Figure."""
        import matplotlib.pyplot as plt  # type: ignore

        bg = _hex_to_rgb_float(self.theme["background_color"])
        accent = _hex_to_rgb_float(self.theme["accent_color"])

        fig = plt.figure(figsize=(12.8, 7.2), facecolor=bg)
        return fig

    def _plot_bar(self, fig, diagram: dict):
        """Add a bar chart to *fig* and return the Axes object."""
        import numpy as np  # type: ignore

        ax = fig.add_subplot(111)
        labels = diagram.get("labels", [])
        values = diagram.get("values", [])
        color = diagram.get("color", self.theme["title_color"])

        x = np.arange(len(labels))
        bars = ax.bar(x, values, color=color, width=0.6, zorder=3)

        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=12)

        # Value labels on top of each bar
        for bar, value in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(values) * LABEL_OFFSET_RATIO,
                str(value),
                ha="center",
                va="bottom",
                fontsize=11,
                color=self.theme["text_color"],
            )
        return ax

    def _plot_line(self, fig, diagram: dict):
        """Add a line chart to *fig* and return the Axes object."""
        ax = fig.add_subplot(111)
        labels = diagram.get("labels", [])
        values = diagram.get("values", [])
        color = diagram.get("color", self.theme["accent_color"])

        ax.plot(labels, values, color=color, linewidth=2.5, marker="o",
                markersize=8, zorder=3)
        ax.fill_between(range(len(labels)), values, alpha=0.15, color=color)
        return ax

    def _plot_pie(self, fig, diagram: dict):
        """Add a pie chart to *fig* and return the Axes object."""
        import matplotlib.pyplot as plt  # type: ignore

        ax = fig.add_subplot(111)
        labels = diagram.get("labels", [])
        values = diagram.get("values", [])

        ax.pie(
            values,
            labels=labels,
            autopct="%1.1f%%",
            startangle=140,
            textprops={"color": self.theme["text_color"]},
        )
        return ax

    def _style_axes(self, ax, diagram: dict, chart_type: str) -> None:
        """Apply common styling to *ax*."""
        bg = _hex_to_rgb_float(self.theme["background_color"])
        text_color = self.theme["text_color"]
        title_color = self.theme["title_color"]

        ax.set_facecolor(bg)
        ax.tick_params(colors=text_color)
        ax.spines[:].set_color(text_color)

        chart_title = diagram.get("title", "")
        if chart_title:
            ax.set_title(chart_title, color=title_color, fontsize=16, pad=15, fontweight="bold")

        if chart_type != "pie":
            xlabel = diagram.get("xlabel", "")
            ylabel = diagram.get("ylabel", "")
            if xlabel:
                ax.set_xlabel(xlabel, color=text_color, fontsize=13)
            if ylabel:
                ax.set_ylabel(ylabel, color=text_color, fontsize=13)
            ax.yaxis.label.set_color(text_color)
            ax.xaxis.label.set_color(text_color)
            ax.tick_params(axis="both", colors=text_color)
            ax.grid(axis="y", linestyle="--", alpha=0.3, color=text_color, zorder=0)

    def _write_placeholder(self, slide_id: int) -> str:
        """Write a placeholder PNG and return its path."""
        from src.utils import write_placeholder_png  # avoid circular at module level

        file_path = os.path.join(self.output_dir, f"slide_{slide_id:03d}.png")
        write_placeholder_png(file_path)
        return file_path
