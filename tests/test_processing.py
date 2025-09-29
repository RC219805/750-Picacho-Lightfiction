"""Tests for the image processing utilities and CLI integration."""

import subprocess
import sys
from pathlib import Path

import yaml
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


def test_cli_processes_manifest_and_creates_variants(tmp_path):
    """The CLI loads a manifest and emits the declared output variants."""

    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()

    base_image = Image.new("RGB", (800, 600), color=(100, 100, 100))
    source_path = input_dir / "test_render.jpg"
    base_image.save(source_path)

    manifest = {
        "renders": [
            {
                "source": "test_render.jpg",
                "variants": [
                    {
                        "filename": "test_render_square.jpg",
                        "operations": [
                            {"type": "grade", "exposure": 0.2},
                            {"type": "resize", "preset": "square_1080"},
                        ],
                    },
                    {
                        "filename": "test_render_custom.jpg",
                        "operations": [
                            {"type": "resize", "width": 640, "height": 360},
                            {"type": "grade", "contrast": 0.5},
                        ],
                    },
                ],
            }
        ]
    }

    manifest_path = tmp_path / "manifest.yml"
    manifest_path.write_text(yaml.safe_dump(manifest))

    # Exercise the CLI entry point using a subprocess to mimic real usage.
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.main",
            "--manifest",
            str(manifest_path),
            "--input-dir",
            str(input_dir),
            "--output-dir",
            str(output_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    square_output = output_dir / "test_render_square.jpg"
    custom_output = output_dir / "test_render_custom.jpg"

    assert square_output.exists(), completed.stdout
    assert custom_output.exists(), completed.stdout

    square_image = Image.open(square_output)
    assert square_image.size == (1080, 1080)

    # The center pixel should be brightened compared to the source (100 -> 120).
    center_pixel = square_image.getpixel((square_image.width // 2, square_image.height // 2))
    assert center_pixel[0] >= 118

    custom_image = Image.open(custom_output)
    assert custom_image.size == (640, 360)
