"""Image grading and cropping helpers for the rendering pipeline."""

from __future__ import annotations

from typing import Dict, Iterable, Optional, Tuple

import numpy as np
from PIL import Image, ImageFilter


def _ensure_rgb(image: Image.Image) -> Image.Image:
    """Return a copy of *image* in RGB mode, preserving alpha if present."""

    if image.mode == "RGB":
        return image.copy()

    if image.mode == "RGBA":
        return image.copy()

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


def _resolve_enhance_factor(value: float) -> float:
    """Return a Pillow enhancement factor honoring legacy additive inputs."""

    factor = float(value)

    if -1.0 <= factor <= 1.0:
        # Legacy manifests treated ``0.2`` as ``1.2``. Preserve that behavior.
        factor = 1.0 + factor
    elif factor < 0.0:
        # Pillow expects non-negative enhancement factors.
        factor = 0.0

    return factor


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
    """Apply grading primitives in a predictable order.
    
    Supports both advanced grading parameters (temperature_shift, shadow_lift, 
    highlight_lift, micro_contrast/local_contrast) and simple parameters 
    (exposure, contrast, saturation) for compatibility with YAML manifests.
    """

    if not grading:
        return image.copy()

    result = image.copy()

    # Handle simple grading parameters first (for YAML manifest compatibility)
    exposure = grading.get("exposure")
    if exposure is not None:
        from PIL import ImageEnhance
        result = ImageEnhance.Brightness(result).enhance(1 + float(exposure))

    contrast = grading.get("contrast")
    if contrast is not None:
        from PIL import ImageEnhance
        result = ImageEnhance.Contrast(result).enhance(_resolve_enhance_factor(contrast))

    saturation = grading.get("saturation")
    if saturation is not None:
        from PIL import ImageEnhance
        result = ImageEnhance.Color(result).enhance(_resolve_enhance_factor(saturation))

    # Handle advanced grading parameters
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


# Crop presets for architectural renderings

# Public mapping of preset names to their target aspect ratios.
CROP_PRESETS: Dict[str, Tuple[int, int]] = {
    "hero_21x9": (21, 9),
    "card_4x3": (4, 3),
    "web_16x9": (16, 9),
    "square_1x1": (1, 1),
}


def _clamp(value: float, minimum: float, maximum: float) -> float:
    """Clamp *value* between *minimum* and *maximum*."""

    return max(minimum, min(maximum, value))


def _normalize_offset(offset: Iterable[float] | None) -> Tuple[float, float]:
    """Return a validated ``(x, y)`` focal offset in the range ``[-1, 1]``."""

    if offset is None:
        return (0.0, 0.0)

    x, y = offset
    return (_clamp(float(x), -1.0, 1.0), _clamp(float(y), -1.0, 1.0))


def _crop_box(
    original: Tuple[int, int],
    target_ratio: float,
    offset: Tuple[float, float],
) -> Tuple[int, int, int, int]:
    """Compute a crop box for *original* dimensions and *target_ratio*.

    The offset is expressed in the normalized range ``[-1, 1]`` where ``0`` is
    center, ``-1`` biases towards the top/left edge, and ``+1`` biases towards
    the bottom/right edge.
    """

    width, height = original
    if width == 0 or height == 0:
        return (0, 0, width, height)

    current_ratio = width / height

    if abs(current_ratio - target_ratio) < 1e-6:
        return (0, 0, width, height)

    if current_ratio > target_ratio:
        # Image is too wide -> trim the sides.
        new_width = int(round(height * target_ratio))
        new_height = height
        available = width - new_width
        offset_x = (offset[0] + 1.0) / 2.0
        left = int(round(available * offset_x))
        left = max(0, min(width - new_width, left))
        return (left, 0, left + new_width, new_height)

    # Image is too tall -> trim top/bottom.
    new_width = width
    new_height = int(round(width / target_ratio))
    available = height - new_height
    offset_y = (offset[1] + 1.0) / 2.0
    top = int(round(available * offset_y))
    top = max(0, min(height - new_height, top))
    return (0, top, new_width, top + new_height)


def crop_to_aspect(
    image: Image.Image, aspect: Tuple[int, int], offset: Iterable[float] | None = None
) -> Image.Image:
    """Crop *image* to the supplied aspect ratio.

    Args:
        image: Source PIL image to crop.
        aspect: ``(width, height)`` tuple describing the target ratio.
        offset: Optional ``(x, y)`` focal offset within ``[-1, 1]`` to bias the
            crop window. ``(-1, -1)`` keeps the top-left corner, ``(1, 1)`` keeps
            the bottom-right corner. Values outside the valid range are clamped.

    Returns:
        ``Image.Image``: A new image cropped to the requested aspect ratio.
    """

    target_ratio = aspect[0] / aspect[1]
    normalized_offset = _normalize_offset(offset)
    left, top, right, bottom = _crop_box(image.size, target_ratio, normalized_offset)
    return image.crop((left, top, right, bottom))


def apply_crop_preset(
    image: Image.Image,
    preset: str,
    *,
    offset: Iterable[float] | None = None,
) -> Image.Image:
    """Apply the named crop *preset* to *image*.

    Args:
        image: Source image to crop.
        preset: Key from :data:`CROP_PRESETS` (e.g., ``"hero_21x9"``).
        offset: Optional ``(x, y)`` focal offset.

    Raises:
        KeyError: If the preset name is not recognized.
    """

    if preset not in CROP_PRESETS:
        raise KeyError(f"Unknown crop preset: {preset}")

    return crop_to_aspect(image, CROP_PRESETS[preset], offset=offset)


def hero_21x9(image: Image.Image, offset: Iterable[float] | None = None) -> Image.Image:
    """Crop *image* to a cinematic 21:9 hero frame."""

    return crop_to_aspect(image, CROP_PRESETS["hero_21x9"], offset=offset)


def card_4x3(image: Image.Image, offset: Iterable[float] | None = None) -> Image.Image:
    """Crop *image* to a 4:3 ratio suitable for gallery cards."""

    return crop_to_aspect(image, CROP_PRESETS["card_4x3"], offset=offset)


def web_16x9(image: Image.Image, offset: Iterable[float] | None = None) -> Image.Image:
    """Crop *image* to the ubiquitous 16:9 web-safe aspect."""

    return crop_to_aspect(image, CROP_PRESETS["web_16x9"], offset=offset)
