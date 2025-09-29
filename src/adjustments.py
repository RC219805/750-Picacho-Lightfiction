"""Image grading helpers for the rendering pipeline."""

from __future__ import annotations

from typing import Dict, Optional

import numpy as np
from PIL import Image, ImageFilter


def _ensure_rgb(image: Image.Image) -> Image.Image:
    """Return a copy of *image* in RGB mode, preserving alpha if present."""

    if image.mode == "RGB":
        return image.copy()

    if image.mode == "RGBA":
        return image.convert("RGBA")

    return image.convert("RGB")


def _split_alpha(image: Image.Image):
    if image.mode == "RGBA":
        rgb, alpha = image.convert("RGBA"), image.getchannel("A")
        return rgb.convert("RGB"), alpha
    return _ensure_rgb(image), None


def _recombine_alpha(rgb: Image.Image, alpha: Optional[Image.Image], original_mode: str) -> Image.Image:
    if alpha is None:
        if original_mode == "RGB":
            return rgb
        return rgb.convert(original_mode)

    merged = rgb.convert("RGBA")
    merged.putalpha(alpha)
    if original_mode == "RGBA":
        return merged
    return merged.convert(original_mode)


def apply_temperature_shift(image: Image.Image, mired_shift: float) -> Image.Image:
    """Warm (+) or cool (-) an image by adjusting channel gains."""

    if not mired_shift:
        return image.copy()

    base_rgb, alpha = _split_alpha(image)
    arr = np.asarray(base_rgb).astype(np.float32)

    gain = 1.0 + (mired_shift / 100.0)
    gain = max(0.1, min(10.0, gain))

    red_gain = gain
    blue_gain = 1.0 / gain

    gains = np.array([red_gain, 1.0, blue_gain], dtype=np.float32)
    arr *= gains
    np.clip(arr, 0.0, 255.0, out=arr)

    warmed = Image.fromarray(arr.astype(np.uint8), mode="RGB")
    return _recombine_alpha(warmed, alpha, image.mode)


def apply_shadow_lift(image: Image.Image, amount: float) -> Image.Image:
    """Lift the shadows by mixing dark pixels toward mid-tones."""

    if not amount:
        return image.copy()

    amount = max(0.0, min(1.0, float(amount)))

    base_rgb, alpha = _split_alpha(image)
    arr = np.asarray(base_rgb).astype(np.float32) / 255.0

    shadow_mask = 1.0 - np.clip(arr / 0.5, 0.0, 1.0)
    lifted = arr + amount * shadow_mask
    lifted = np.clip(lifted, 0.0, 1.0)

    result = Image.fromarray((lifted * 255.0).astype(np.uint8), mode="RGB")
    return _recombine_alpha(result, alpha, image.mode)


def apply_highlight_lift(image: Image.Image, amount: float) -> Image.Image:
    """Lift highlights toward white without blowing them out."""

    if not amount:
        return image.copy()

    amount = max(0.0, min(1.0, float(amount)))

    base_rgb, alpha = _split_alpha(image)
    arr = np.asarray(base_rgb).astype(np.float32) / 255.0

    highlight_mask = np.clip((arr - 0.5) / 0.5, 0.0, 1.0)
    lifted = arr + amount * highlight_mask * (1.0 - arr)
    lifted = np.clip(lifted, 0.0, 1.0)

    result = Image.fromarray((lifted * 255.0).astype(np.uint8), mode="RGB")
    return _recombine_alpha(result, alpha, image.mode)


def apply_local_contrast(image: Image.Image, amount: float, radius: float = 2.0) -> Image.Image:
    """Adjust local contrast using an unsharp mask style enhancement."""

    if amount is None or amount == 1.0:
        return image.copy()

    amount = float(amount)
    base = image.copy()

    if amount > 1.0:
        percent = min(500, max(0, int((amount - 1.0) * 200)))
        if percent == 0:
            return base
        return base.filter(ImageFilter.UnsharpMask(radius=radius, percent=percent, threshold=0))

    # Reduce local contrast by blending with a blurred version.
    blend_factor = max(0.0, min(1.0, 1.0 - amount))
    blurred = base.filter(ImageFilter.GaussianBlur(radius=radius))
    return Image.blend(base, blurred, blend_factor)


def apply_grading(image: Image.Image, grading: Optional[Dict[str, float]]) -> Image.Image:
    """Apply grading primitives in a predictable order."""

    if not grading:
        return image.copy()

    result = image.copy()

    temp_shift = grading.get("temperature_shift")
    if temp_shift:
        result = apply_temperature_shift(result, temp_shift)

    shadow_lift = grading.get("shadow_lift")
    if shadow_lift:
        result = apply_shadow_lift(result, shadow_lift)

    highlight_lift = grading.get("highlight_lift")
    if highlight_lift:
        result = apply_highlight_lift(result, highlight_lift)

    micro_contrast = grading.get("micro_contrast") if grading.get("micro_contrast") is not None else grading.get("local_contrast")
    if micro_contrast is not None:
        result = apply_local_contrast(result, micro_contrast)

    return result
