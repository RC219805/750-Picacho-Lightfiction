"""Tests for the image processing utilities."""

from pathlib import Path
import sys

from PIL import Image, ImageOps

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DCI_4K_RESOLUTION
from src.processing import resize_image


def test_resize_image_preserves_aspect_ratio_with_padding():
    """Images are resized without distortion and centered with padding."""

    original = Image.new("RGB", (800, 600), color=(255, 0, 0))

    resized = resize_image(original, DCI_4K_RESOLUTION)

    assert resized.size == DCI_4K_RESOLUTION

    expected_scaled = ImageOps.contain(original, DCI_4K_RESOLUTION)
    expected_canvas = Image.new("RGB", DCI_4K_RESOLUTION)

    offset_x = (DCI_4K_RESOLUTION[0] - expected_scaled.size[0]) // 2
    offset_y = (DCI_4K_RESOLUTION[1] - expected_scaled.size[1]) // 2
    expected_canvas.paste(expected_scaled, (offset_x, offset_y))

    assert resized.tobytes() == expected_canvas.tobytes()


def test_resize_image_returns_copy_for_matching_dimensions():
    """Exact matches are returned as copies to avoid side effects."""

    original = Image.new("RGB", DCI_4K_RESOLUTION, color=(10, 20, 30))

    resized = resize_image(original, DCI_4K_RESOLUTION)

    assert resized.size == DCI_4K_RESOLUTION
    assert resized is not original
    assert resized.tobytes() == original.tobytes()
