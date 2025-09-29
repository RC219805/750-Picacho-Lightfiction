"""Image adjustment helpers for cropping architectural renderings.

Provides a set of named crop presets (``hero_21x9``, ``card_4x3``,
``web_16x9``) that normalize an image to a desired aspect ratio while
optionally biasing the crop around a focal point.  The presets can be used
individually or looked up dynamically via :func:`apply_crop_preset`.
"""

from __future__ import annotations

from typing import Dict, Iterable, Tuple

from PIL import Image

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


__all__ = [
    "CROP_PRESETS",
    "apply_crop_preset",
    "card_4x3",
    "crop_to_aspect",
    "hero_21x9",
    "web_16x9",
]
