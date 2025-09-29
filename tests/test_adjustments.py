"""Tests for grading primitives."""

from pathlib import Path
import sys

import numpy as np
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.adjustments import (
    apply_grading,
    apply_local_contrast,
    apply_shadow_lift,
    apply_temperature_shift,
)


def _mean_channels(image: Image.Image):
    arr = np.asarray(image.convert("RGB"), dtype=np.float32)
    return arr.mean(axis=(0, 1))


def test_temperature_shift_warm_increases_red_channel():
    original = Image.new("RGB", (32, 32), color=(110, 120, 160))

    warmed = apply_temperature_shift(original, 8.0)

    orig_mean = _mean_channels(original)
    warm_mean = _mean_channels(warmed)

    assert warm_mean[0] > orig_mean[0]
    assert warm_mean[2] < orig_mean[2]


def test_shadow_lift_brightens_dark_pixels_more_than_midtones():
    arr = np.zeros((4, 4, 3), dtype=np.uint8)
    arr[:, :2] = 30
    arr[:, 2:] = 120
    image = Image.fromarray(arr, mode="RGB")

    lifted = apply_shadow_lift(image, 0.4)
    lifted_arr = np.asarray(lifted, dtype=np.uint8)

    assert lifted_arr[:, :2].mean() > arr[:, :2].mean()
    assert lifted_arr[:, :2].mean() - arr[:, :2].mean() > (
        lifted_arr[:, 2:].mean() - arr[:, 2:].mean()
    )


def test_local_contrast_increase_raises_standard_deviation():
    gradient = np.array([
        [40, 80, 120, 80, 40],
        [40, 80, 120, 80, 40],
        [40, 80, 120, 80, 40],
        [40, 80, 120, 80, 40],
        [40, 80, 120, 80, 40],
    ], dtype=np.uint8)
    image = Image.fromarray(gradient, mode="L").convert("RGB")

    boosted = apply_local_contrast(image, 1.2)

    orig_std = np.asarray(image.convert("L"), dtype=np.float32).std()
    boosted_std = np.asarray(boosted.convert("L"), dtype=np.float32).std()

    assert boosted_std > orig_std


def test_apply_grading_runs_in_order():
    base = Image.fromarray(np.full((4, 4, 3), 90, dtype=np.uint8), mode="RGB")

    graded = apply_grading(
        base,
        {
            "temperature_shift": 5.0,
            "shadow_lift": 0.2,
            "highlight_lift": 0.1,
            "micro_contrast": 1.1,
        },
    )

    graded_mean = _mean_channels(graded)
    base_mean = _mean_channels(base)

    assert graded_mean[0] >= base_mean[0]
    assert graded_mean.mean() >= base_mean.mean()
