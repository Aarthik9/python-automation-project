# AI Presentation Video Generator

> **python · automation · internship-project · python-scripts · workflow-automation**

An end-to-end Python automation pipeline that takes a structured **JSON input file** and automatically produces a complete **presentation video** with narrated audio, subtitles, slide images, and data-driven diagrams.

---

## ✨ Features

| Step | Module | What it does |
|------|--------|--------------|
| 1 | `src/audio_generator.py` | Converts speaker-note text to MP3 speech via **gTTS** |
| 2 | `src/subtitle_generator.py` | Produces a timed **SRT** subtitle file |
| 3 | `src/image_generator.py` | Renders **slide images** (title & bullet-point layouts) using **Pillow** |
| 4 | `src/diagram_generator.py` | Renders **bar / line / pie charts** using **matplotlib** |
| 5 | `src/video_creator.py` | Assembles audio + images into an **MP4 video** via **MoviePy** |

All modules degrade gracefully: if a dependency (e.g. `gTTS`, `moviepy`) is unavailable or a network call fails, the pipeline writes a placeholder/manifest and continues.

---

## 📁 Project Structure

```
python-automation-project/
│
├── main.py                   # CLI entry point – runs the full pipeline
│
├── src/
│   ├── __init__.py
│   ├── audio_generator.py    # Text-to-speech (gTTS)
│   ├── subtitle_generator.py # SRT subtitle creation
│   ├── image_generator.py    # Slide image rendering (Pillow)
│   ├── diagram_generator.py  # Chart rendering (matplotlib)
│   ├── video_creator.py      # Video assembly (MoviePy / ffmpeg)
│   └── utils.py              # Shared helpers (JSON loading, logging, …)
│
├── data/
│   └── sample_input.json     # Example 7-slide AI presentation
│
├── output/                   # Generated artefacts (git-ignored)
│   ├── audio/                # slide_001.mp3 … slide_NNN.mp3
│   ├── images/               # slide_001.png … slide_NNN.png
│   ├── subtitles/            # presentation.srt
│   └── presentation.mp4      # Final video
│
├── tests/
│   ├── test_audio_generator.py
│   ├── test_subtitle_generator.py
│   ├── test_image_generator.py
│   ├── test_diagram_generator.py
│   ├── test_video_creator.py
│   └── test_utils.py
│
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start

### 1 – Clone & install dependencies

```bash
git clone https://github.com/Aarthik9/python-automation-project.git
cd python-automation-project
pip install -r requirements.txt
```

> **ffmpeg** is also required for video assembly:
> ```bash
> # Ubuntu / Debian
> sudo apt install ffmpeg
> # macOS
> brew install ffmpeg
> ```

### 2 – Run the pipeline

```bash
# Use the bundled sample presentation
python main.py

# Specify your own JSON input
python main.py path/to/my_slides.json

# Custom output path and verbose logging
python main.py data/sample_input.json -o output/my_video.mp4 --verbose
```

### 3 – View outputs

```
output/
├── audio/        ← MP3 narration per slide
├── images/       ← PNG slide images
├── subtitles/    ← presentation.srt
└── presentation.mp4
```

---

## 📄 JSON Input Format

```json
{
  "title": "My Presentation",
  "author": "Jane Doe",
  "theme": {
    "background_color": "#1a1a2e",
    "title_color": "#e94560",
    "text_color": "#ffffff",
    "accent_color": "#0f3460"
  },
  "slides": [
    {
      "id": 1,
      "type": "title",
      "title": "My Presentation",
      "subtitle": "A subtitle",
      "speaker_notes": "Text read aloud for this slide."
    },
    {
      "id": 2,
      "type": "content",
      "title": "Key Points",
      "content": ["Point one", "Point two", "Point three"],
      "speaker_notes": "Narration for the content slide."
    },
    {
      "id": 3,
      "type": "diagram",
      "title": "Sales by Region",
      "speaker_notes": "This chart shows regional sales data.",
      "diagram": {
        "type": "bar",
        "title": "2024 Sales",
        "labels": ["North", "South", "East", "West"],
        "values": [120, 95, 140, 110],
        "xlabel": "Region",
        "ylabel": "Units Sold",
        "color": "#e94560"
      }
    }
  ]
}
```

### Slide types

| `type`     | Required keys                         | Optional keys           |
|------------|---------------------------------------|-------------------------|
| `title`    | `id`, `type`, `title`                 | `subtitle`, `speaker_notes` |
| `content`  | `id`, `type`, `title`                 | `content[]`, `speaker_notes` |
| `diagram`  | `id`, `type`, `title`, `diagram`      | `speaker_notes`         |

### Diagram types (`diagram.type`)

| Value   | Description      |
|---------|-----------------|
| `bar`   | Vertical bar chart |
| `line`  | Line chart with markers |
| `pie`   | Pie chart       |

---

## ⚙️ CLI Options

```
usage: main.py [-h] [-o OUTPUT] [--output-dir OUTPUT_DIR]
               [--lang LANG] [--fps FPS] [-v]
               [input]

positional arguments:
  input                Path to JSON input (default: data/sample_input.json)

options:
  -o, --output         Output video filename
  --output-dir         Root output directory (default: output/)
  --lang               BCP-47 language code for TTS (default: en)
  --fps                Video frames per second (default: 24)
  -v, --verbose        Enable debug logging
```

---

## 🧪 Running Tests

```bash
pip install pytest pytest-mock
pytest tests/ -v
```

72 tests covering all modules, including graceful-fallback scenarios.

---

## 🏗 Architecture

```
JSON Input
    │
    ▼
┌─────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   utils.py  │───▶│ audio_generator  │───▶│  slide_NNN.mp3  │
│  load+valid │    └──────────────────┘    └─────────────────┘
└─────────────┘    ┌──────────────────┐    ┌─────────────────┐
                   │subtitle_generator│───▶│ presentation.srt│
                   └──────────────────┘    └─────────────────┘
                   ┌──────────────────┐    ┌─────────────────┐
                   │ image_generator  │───▶│  slide_NNN.png  │
                   └──────────────────┘    └─────────────────┘
                   ┌──────────────────┐    ┌─────────────────┐
                   │diagram_generator │───▶│  slide_NNN.png  │
                   └──────────────────┘    └─────────────────┘
                            │
                            ▼
                   ┌──────────────────┐
                   │  video_creator   │───▶ presentation.mp4
                   └──────────────────┘
```

---

## 📦 Dependencies

| Package      | Purpose                    | Min version |
|-------------|----------------------------|-------------|
| `gtts`       | Text-to-speech             | 2.5.0       |
| `Pillow`     | Slide image rendering      | 10.0.0      |
| `matplotlib` | Chart / diagram rendering  | 3.7.0       |
| `numpy`      | Numerical arrays           | 1.24.0      |
| `moviepy`    | Video assembly             | 1.0.3       |
| `pytest`     | Test framework             | 7.4.0       |
| `pytest-mock`| Mocking in tests           | 3.11.0      |

---

## 📝 License

MIT – see repository root for details.
