"""Project-wide configuration constants for the rendering pipeline."""

from pathlib import Path


# 4K DCI (Digital Cinema Initiative) resolution
DCI_4K_WIDTH = 4096
DCI_4K_HEIGHT = 2160
DCI_4K_RESOLUTION = (DCI_4K_WIDTH, DCI_4K_HEIGHT)

# Directory paths
# Updated default directories for pipeline IO locations.
# Use nested folders so that raw assets and render outputs live alongside
# other project data without cluttering the repository root.
INPUT_DIR = "data/new_input"
OUTPUT_DIR = "results/new_output"

# Default manifest describing rendering tasks
DEFAULT_MANIFEST_PATH = Path("config") / "view_selects.yml"


# Common aspect ratio presets that can be referenced from the manifest.
ASPECT_RATIO_PRESETS = {
    "dci_4k": DCI_4K_RESOLUTION,
    "square_1080": (1080, 1080),
    "vertical_story": (1080, 1920),
    "ultrawide": (5120, 2160),
}