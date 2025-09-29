"""Tests for the image processing utilities."""

from pathlib import Path
import sys

import pytest
from PIL import Image, ImageOps

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DCI_4K_RESOLUTION
from src.adjustments import apply_crop_preset, hero_21x9
from src.processing import process_image, resize_image


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


def test_hero_crop_produces_expected_ratio():
    """The 21:9 preset trims the source image while preserving focal offsets."""

    base = Image.new("RGB", (3000, 2000), color=(0, 0, 255))
    warm_band = Image.new("RGB", (3000, 800), color=(255, 0, 0))
    base.paste(warm_band, (0, 0))

    cropped_center = hero_21x9(base)
    cropped_top = hero_21x9(base, offset=(0, -1))
    cropped_bottom = hero_21x9(base, offset=(0, 1))

    assert cropped_center.width / cropped_center.height == pytest.approx(21 / 9, rel=1e-3)
    assert cropped_center.size == cropped_top.size == cropped_bottom.size

    # Focal offsets bias which band remains in frame.
    top_sample = cropped_top.getpixel((cropped_top.width // 2, 10))
    bottom_sample = cropped_bottom.getpixel((cropped_bottom.width // 2, cropped_bottom.height - 10))

    assert top_sample == (255, 0, 0)
    assert bottom_sample == (0, 0, 255)


def test_apply_crop_preset_resolves_mapping():
    """Dictionary-based crop declarations are respected."""

    base = Image.new("RGB", (1600, 1600), color=(100, 100, 100))
    preset_image = apply_crop_preset(base, "web_16x9")

    assert (preset_image.width / preset_image.height) == pytest.approx(16 / 9, rel=1e-3)


def test_process_image_honors_variant_crop(tmp_path):
    """Crops are performed before resizing so padding only happens afterward."""

    source = Image.new("RGB", (2400, 1600), color=(0, 0, 255))
    top_band = Image.new("RGB", (2400, 400), color=(255, 0, 0))
    source.paste(top_band, (0, 0))

    source_path = tmp_path / "source.png"
    output_path = tmp_path / "variant.png"
    source.save(source_path)

    variant = {"crop": {"preset": "web_16x9", "offset": (0, -1)}, "size": (1600, 900)}

    success = process_image(
        str(source_path),
        str(output_path),
        target_size=(1600, 900),
        variant=variant,
    )

    assert success

    processed = Image.open(output_path)
    assert processed.size == (1600, 900)

    # Because the variant biases the crop upward, the warm band should still be visible near the top.
    sample = processed.getpixel((processed.width // 2, 10))
    assert sample == (255, 0, 0)
