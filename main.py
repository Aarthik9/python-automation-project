#!/usr/bin/env python3
"""
main.py
~~~~~~~
Command-line entry point for the AI Presentation Video Generator.

Usage::

    python main.py                            # use default sample input
    python main.py data/sample_input.json     # specify input file
    python main.py data/sample_input.json -o output/my_video.mp4
    python main.py --help

The script runs the full pipeline:

    1. Parse & validate JSON input
    2. Generate audio (gTTS)
    3. Generate subtitle file (SRT)
    4. Generate slide images (Pillow)
    5. Generate diagram images (matplotlib)
    6. Assemble final video (MoviePy)
"""

import argparse
import logging
import os
import sys

from src.audio_generator import AudioGenerator
from src.diagram_generator import DiagramGenerator
from src.image_generator import ImageGenerator
from src.subtitle_generator import SubtitleGenerator
from src.utils import (
    ensure_dir,
    load_json,
    print_banner,
    print_step,
    setup_logging,
    validate_input,
)
from src.video_creator import VideoCreator

# Default paths
DEFAULT_INPUT = os.path.join(os.path.dirname(__file__), "data", "sample_input.json")
DEFAULT_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

TOTAL_STEPS = 6


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate an AI-based presentation video from a JSON input file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "input",
        nargs="?",
        default=DEFAULT_INPUT,
        help="Path to the JSON input file (default: data/sample_input.json)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output video filename (default: output/presentation.mp4)",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help="Root output directory (default: output/)",
    )
    parser.add_argument(
        "--lang",
        default="en",
        help="BCP-47 language code for TTS audio (default: en)",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=24,
        help="Video frames per second (default: 24)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose/debug logging",
    )
    return parser.parse_args()


def run_pipeline(args: argparse.Namespace) -> int:
    """Execute the full generation pipeline.  Returns exit code (0 = success)."""

    setup_logging(logging.DEBUG if args.verbose else logging.INFO)
    logger = logging.getLogger(__name__)

    print_banner("AI Presentation Video Generator")

    # -----------------------------------------------------------------------
    # Step 1 – Load & validate input
    # -----------------------------------------------------------------------
    print_step(1, TOTAL_STEPS, f"Loading input: {args.input}")
    try:
        data = load_json(args.input)
        validate_input(data)
    except (FileNotFoundError, ValueError) as exc:
        logger.error("Input error: %s", exc)
        return 1

    slides = data["slides"]
    theme = data.get("theme")
    presentation_title = data.get("title", "presentation")

    # Resolve output paths
    output_dir = args.output_dir
    audio_dir = os.path.join(output_dir, "audio")
    subtitle_dir = os.path.join(output_dir, "subtitles")
    image_dir = os.path.join(output_dir, "images")

    for d in (output_dir, audio_dir, subtitle_dir, image_dir):
        ensure_dir(d)

    output_filename = (
        args.output
        if args.output
        else os.path.join(output_dir, "presentation.mp4")
    )
    # If only a filename was given (no directory), place it inside output_dir.
    if not os.path.dirname(output_filename):
        output_filename = os.path.join(output_dir, output_filename)

    logger.info("Presentation: %s  |  %d slides", presentation_title, len(slides))

    # -----------------------------------------------------------------------
    # Step 2 – Audio generation
    # -----------------------------------------------------------------------
    print_step(2, TOTAL_STEPS, "Generating audio narration")
    audio_gen = AudioGenerator(output_dir=audio_dir, lang=args.lang)
    audio_info = audio_gen.generate_all(slides)
    logger.info("Generated audio for %d slides.", len(audio_info))

    # -----------------------------------------------------------------------
    # Step 3 – Subtitle generation
    # -----------------------------------------------------------------------
    print_step(3, TOTAL_STEPS, "Generating subtitles")
    subtitle_gen = SubtitleGenerator(output_dir=subtitle_dir)
    subtitle_path = subtitle_gen.generate_all(slides, audio_info)
    logger.info("Subtitle file: %s", subtitle_path)

    # -----------------------------------------------------------------------
    # Step 4 – Slide image generation
    # -----------------------------------------------------------------------
    print_step(4, TOTAL_STEPS, "Rendering slide images")
    image_gen = ImageGenerator(output_dir=image_dir, theme=theme)
    image_info = image_gen.generate_all(slides)
    logger.info("Generated %d slide images.", len(image_info))

    # -----------------------------------------------------------------------
    # Step 5 – Diagram generation
    # -----------------------------------------------------------------------
    print_step(5, TOTAL_STEPS, "Rendering diagrams")
    diagram_gen = DiagramGenerator(output_dir=image_dir, theme=theme)
    diagram_info = diagram_gen.generate_all(slides)
    logger.info("Generated %d diagrams.", len(diagram_info))

    # Merge image lists (diagrams override slide images for diagram slides)
    all_image_info = {entry["slide_id"]: entry for entry in image_info}
    for entry in diagram_info:
        all_image_info[entry["slide_id"]] = entry
    merged_images = list(all_image_info.values())

    # -----------------------------------------------------------------------
    # Step 6 – Video assembly
    # -----------------------------------------------------------------------
    print_step(6, TOTAL_STEPS, "Assembling video")
    creator = VideoCreator(output_dir=output_dir, fps=args.fps)
    result_path = creator.create(
        slides=slides,
        image_info=merged_images,
        audio_info=audio_info,
        subtitle_path=subtitle_path,
        output_filename=os.path.basename(output_filename),
    )

    if result_path:
        print_banner(f"Done!  Output: {result_path}")
        return 0
    else:
        logger.error("Video assembly failed.")
        return 1


def main() -> None:
    args = parse_args()
    sys.exit(run_pipeline(args))


if __name__ == "__main__":
    main()
