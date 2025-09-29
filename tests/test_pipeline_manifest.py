"""End-to-end test for manifest driven pipeline."""

from pathlib import Path
import json
import sys

import numpy as np
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.main import run_pipeline


def test_pipeline_applies_crop_and_grading(tmp_path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()

    base = np.zeros((20, 40, 3), dtype=np.uint8)
    base[:, :20] = (30, 60, 180)
    base[:, 20:] = (180, 90, 30)
    image = Image.fromarray(base, mode="RGB")
    source_path = input_dir / "scene.png"
    image.save(source_path)

    manifest = {
        "images": [
            {
                "file": "scene.png",
                "crop": [20, 0, 40, 20],
                "warm_shift": "+6_mireds",
                "shadow_lift": 0.25,
                "micro_contrast": 1.1,
            }
        ]
    }
    manifest_path = input_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest))

    run_pipeline(
        input_dir=input_dir,
        output_dir=output_dir,
        target_size=(20, 20),
        manifest_path=manifest_path,
    )

    output_path = output_dir / "scene_processed.png"
    assert output_path.exists()

    processed = Image.open(output_path)
    arr = np.asarray(processed.convert("RGB"), dtype=np.float32)

    mean_channels = arr.mean(axis=(0, 1))

    # Cropping should remove the cool half, leaving a warm average
    assert mean_channels[0] > mean_channels[2]
    # Shadow lift combined with resizing should raise overall brightness
    assert mean_channels.mean() > base[:, 20:, :].mean()
