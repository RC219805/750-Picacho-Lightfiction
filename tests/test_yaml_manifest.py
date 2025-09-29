"""Tests for the YAML manifest processing system."""

import subprocess
import sys
from pathlib import Path

import yaml
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.main import load_yaml_manifest, iterate_tasks


def test_cli_processes_yaml_manifest_and_creates_variants(tmp_path):
    """The CLI loads a YAML manifest and emits the declared output variants."""

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


def test_load_yaml_manifest_validates_structure():
    """The YAML loader validates required manifest structure."""
    
    # Valid manifest
    valid_manifest = {
        "renders": [
            {
                "source": "test.jpg",
                "variants": [
                    {
                        "filename": "test_output.jpg",
                        "operations": []
                    }
                ]
            }
        ]
    }
    
    with open("/tmp/valid.yml", "w") as f:
        yaml.safe_dump(valid_manifest, f)
    
    manifest = load_yaml_manifest(Path("/tmp/valid.yml"))
    assert "renders" in manifest
    assert len(manifest["renders"]) == 1
    
    # Invalid manifest - no renders
    invalid_manifest = {"other": "data"}
    
    with open("/tmp/invalid.yml", "w") as f:
        yaml.safe_dump(invalid_manifest, f)
    
    try:
        load_yaml_manifest(Path("/tmp/invalid.yml"))
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "non-empty 'renders' list" in str(e)


def test_iterate_tasks_generates_correct_tasks():
    """Task generation handles source paths and operations correctly."""
    
    manifest = {
        "renders": [
            {
                "source": "image1.jpg",
                "variants": [
                    {
                        "filename": "output1.jpg",
                        "operations": [{"type": "resize", "width": 100, "height": 100}]
                    },
                    {
                        "filename": "output2.jpg",
                        "operations": [{"type": "grade", "exposure": 0.1}]
                    }
                ]
            }
        ]
    }
    
    input_dir = Path("/tmp/input")
    output_dir = Path("/tmp/output")
    
    tasks = list(iterate_tasks(manifest, input_dir, output_dir))
    
    assert len(tasks) == 2
    assert tasks[0]["source"] == input_dir / "image1.jpg"
    assert tasks[0]["output"] == output_dir / "output1.jpg"
    assert tasks[0]["operations"] == [{"type": "resize", "width": 100, "height": 100}]
    
    assert tasks[1]["source"] == input_dir / "image1.jpg"
    assert tasks[1]["output"] == output_dir / "output2.jpg"
    assert tasks[1]["operations"] == [{"type": "grade", "exposure": 0.1}]