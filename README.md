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
│   ├── config.py   # Central configuration (input/output paths, target resolution)
│   ├── main.py     # Entry point for batch processing
│   └── processing.py  # Image processing utilities
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

## Running Tests

Execute the automated tests with:

```bash
pytest
```

## Troubleshooting

- If the script reports that no images were found, double-check that files exist in the `input/` directory and that they use supported extensions (`.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`, `.tif`).
- When running inside a virtual environment or CI pipeline, ensure the working directory is the project root so that the `input/` and `output/` folders are correctly resolved.

