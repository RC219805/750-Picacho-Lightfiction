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
├── data/new_input/     # Drop source renderings here
├── results/new_output/ # Processed images are written here
├── src/
│   ├── adjustments.py  # Image grading and crop presets
│   ├── config.py       # Central configuration (input/output paths, target resolution)
│   ├── main.py         # Entry point for batch processing
│   └── processing.py   # Image processing utilities
└── tests/
    └── test_processing.py  # Unit tests
```

## Usage

1. Place the architectural rendering images you want to process into the `data/new_input/` directory.
2. Run the pipeline:

   ```bash
   python -m src.main
   ```

3. Processed files will be saved in the `results/new_output/` directory with the suffix `_processed`.

To quickly process a different folder without editing configuration files, you can
pass the directories as positional arguments. The first path overrides the input
directory and an optional second path overrides the output directory:

```bash
python -m src.main /path/to/input /path/to/output
```

When using the legacy JSON pipeline, combine the positional overrides with the
`--legacy` flag:

```bash
python -m src.main --legacy /path/to/input /path/to/output
```

### YAML Manifest Processing

For advanced workflows, you can use YAML manifests to define multiple variants and operations:

```bash
python -m src.main --manifest config/view_selects.yml --input-dir data/new_input --output-dir results/new_output
```

The YAML manifest allows you to specify:
- Multiple output variants per source image
- Crop operations using preset aspect ratios with focal offsets
- Resize operations with aspect ratio presets
- Color grading operations (exposure, contrast, saturation, temperature_shift, shadow_lift, highlight_lift, micro_contrast)
- Mask-driven inpainting to remove furnishings or signage (`type: inpaint`)
- Material enrichment operations to emphasize texture and surface clarity (`type: material_enhance`)
- Custom output filenames and directories

Contrast and saturation grading entries accept either multiplier-style values
(`1.35` increases contrast by 35%) or legacy additive deltas in the range
`[-1.0, 1.0]` which are converted to multipliers internally (for example,
`0.2` becomes `1.2`). Use values greater than `1.0` to take direct control over
the enhancement factor in new manifests while continuing to support older
configurations.

Example YAML manifest with crop and advanced grading:

```yaml
renders:
  - source: lobby_daylight.jpg
    variants:
      - filename: lobby_daylight_hero.jpg
        operations:
          - type: crop
            preset: hero_21x9
            offset: [0, -0.2]  # Bias crop slightly upward
          - type: resize  
            preset: dci_4k
          - type: grade
            temperature_shift: 15  # Warm the image
            micro_contrast: 1.1    # Enhance local contrast
      - filename: lobby_daylight_clean.jpg
        operations:
          - type: inpaint
            mask: masks/lobby_daylight_furniture.png  # remove stools and accent tables
            blur_radius: 18
            feather_radius: 6
          - type: material_enhance
            clarity: 1.25
            micro_contrast: 1.3
            depth: 1.1
            sheen: 1.05
```

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

Crop presets can be used in two ways:

**1. Through YAML manifests (recommended):**
```yaml
operations:
  - type: crop
    preset: hero_21x9
    offset: [0, -0.5]  # Optional focal offset
```

**2. Directly in Python code:**

```python
from src.processing import process_image

process_image(
    "data/new_input/render.png",
    "results/new_output/render_hero.png",
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

- If the script reports that no images were found, double-check that files exist in the `data/new_input/` directory and that they use supported extensions (`.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`, `.tif`).
- When running inside a virtual environment or CI pipeline, ensure the working directory is the project root so that the `data/new_input/` and `results/new_output/` folders are correctly resolved.

