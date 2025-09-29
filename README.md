# 750-Picacho-Lightfiction

Tools for spatially-aware application of materials and textures to architectural renderings at DCI 4K resolution.

## Prerequisites

- Python 3.10 or newer (the project is tested on Python 3.12)
- pip for installing Python dependencies

## Installation

1. (Optional) Create and activate a virtual environment.
2. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

## Project Structure

```
.
├── input/          # Drop source renderings here
├── output/         # Processed images are written here
├── src/
│   ├── adjustments.py  # Crop presets and focal-aware helpers
│   ├── config.py       # Central configuration (input/output paths, target resolution)
│   ├── main.py         # Entry point for batch processing
│   └── processing.py   # Image processing utilities
└── tests/
    └── test_processing.py  # Unit tests
```

## Usage

1. Place the architectural rendering images you want to process into the `input/` directory.
2. Run the pipeline:

   ```bash
   python -m src.main
   ```

3. Processed files will be saved in the `output/` directory with the suffix `_processed`.

### Crop Presets

The `src/adjustments.py` module provides reusable crop helpers that normalize an
image to a specific aspect ratio before resizing. Each preset accepts an
optional focal-point offset `(x, y)` in the range `[-1, 1]` to bias the crop
window towards the top/left (`-1`) or bottom/right (`+1`).

| Preset        | Aspect | Usage notes                                   |
| ------------- | ------ | --------------------------------------------- |
| `hero_21x9`   | 21:9   | Wide cinematic hero frames and marquee shots. |
| `web_16x9`    | 16:9   | General web embeds and responsive hero areas. |
| `card_4x3`    | 4:3    | Gallery cards and compact thumbnails.         |
| `square_1x1`  | 1:1    | Balanced social and avatar crops.            |

To incorporate a crop into the processing pipeline, pass a `variant` mapping to
`process_image`:

```python
from src.processing import process_image

process_image(
    "input/render.png",
    "output/render_hero.png",
    target_size=(1600, 900),
    variant={
        "crop": {"preset": "hero_21x9", "offset": (0, -0.5)},
        "size": (1600, 900),
    },
)
```

Cropping occurs before letterboxing so the focal composition is maintained while
still matching the requested output resolution.

## Running Tests

Execute the automated tests with:

```bash
pytest
```

## Troubleshooting

- If the script reports that no images were found, double-check that files exist in the `input/` directory and that they use supported extensions (`.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`, `.tif`).
- When running inside a virtual environment or CI pipeline, ensure the working directory is the project root so that the `input/` and `output/` folders are correctly resolved.

