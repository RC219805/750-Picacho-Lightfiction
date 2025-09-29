"""Core image manipulation functions using PIL (Pillow).

Handles loading, saving, resizing, and grading operations for images while
preserving image integrity and aspect ratios.
"""

from typing import Dict, Iterable, Optional

from PIL import Image, ImageEnhance, ImageOps
import os
import sys

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))
from config import ASPECT_RATIO_PRESETS, DCI_4K_RESOLUTION


def load_image(filepath):
    """
    Load an image from the specified file path.
    
    Args:
        filepath (str): Path to the image file
        
    Returns:
        PIL.Image: The loaded image object
        
    Raises:
        FileNotFoundError: If the image file doesn't exist
        Exception: If the image cannot be opened
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Image file not found: {filepath}")
    
    try:
        image = Image.open(filepath)
        return image
    except Exception as e:
        raise Exception(f"Failed to load image {filepath}: {str(e)}")


def save_image(image, filepath, quality=95):
    """
    Save an image to the specified file path.
    
    Args:
        image (PIL.Image): The image object to save
        filepath (str): Path where the image should be saved
        quality (int): JPEG quality (1-100, default 95)
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Determine format from file extension
    if filepath.lower().endswith('.jpg') or filepath.lower().endswith('.jpeg'):
        image.save(filepath, 'JPEG', quality=quality)
    else:
        image.save(filepath)


def _background_color_for_mode(mode):
    """Return a neutral background color that matches the supplied mode."""

    if mode in ("RGBA", "LA"):
        return tuple([0] * len(mode))

    if mode == "RGB":
        return (0, 0, 0)

    if mode == "L":
        return 0

    # Fall back to black/zero for all other modes (e.g., "CMYK", "P").
    return 0


def resize_image(image, target_size=DCI_4K_RESOLUTION, resample=Image.LANCZOS):
    """Resize *image* to fit within *target_size* without distortion.

    The source image is scaled to fit inside the target dimensions while
    maintaining its aspect ratio. Letterboxing/pillarboxing is applied as
    needed so the returned image always matches ``target_size`` exactly.
    """

    if image.size == target_size:
        return image.copy()

    # Scale while preserving aspect ratio.
    contained = ImageOps.contain(image, target_size, method=resample)

    if contained.size == target_size:
        return contained

    background = Image.new(
        contained.mode, target_size, color=_background_color_for_mode(contained.mode)
    )

    offset_x = (target_size[0] - contained.size[0]) // 2
    offset_y = (target_size[1] - contained.size[1]) // 2

    if contained.mode in ("RGBA", "LA") or (
        contained.mode == "P" and "transparency" in contained.info
    ):
        background.paste(contained, (offset_x, offset_y), contained)
    else:
        background.paste(contained, (offset_x, offset_y))

    return background


def _resolve_resize_target(operation: Dict, presets: Dict[str, tuple]) -> tuple:
    """Return a ``(width, height)`` tuple for a resize operation."""

    if "preset" in operation:
        preset_name = operation["preset"]
        if preset_name not in presets:
            raise ValueError(f"Unknown aspect ratio preset: {preset_name}")
        return presets[preset_name]

    if "width" in operation and "height" in operation:
        return int(operation["width"]), int(operation["height"])

    raise ValueError("Resize operation must include a preset or width/height.")


def _apply_grading(image: Image.Image, grade_params: Dict) -> Image.Image:
    """Apply exposure/contrast/saturation adjustments to ``image``."""

    result = image

    # Exposure is treated as an additive brightness factor: multiplier = 1.0 + exposure_delta (e.g., 0.1 -> 1.1 = 110% brightness)
    exposure_delta = grade_params.get("exposure")
    if exposure_delta is not None:
        result = ImageEnhance.Brightness(result).enhance(1 + float(exposure_delta))

    contrast = grade_params.get("contrast")
    if contrast is not None:
        result = ImageEnhance.Contrast(result).enhance(1 + float(contrast))

    saturation = grade_params.get("saturation")
    if saturation is not None:
        result = ImageEnhance.Color(result).enhance(float(saturation))

    return result


def process_variant(
    input_path: str,
    output_path: str,
    operations: Optional[Iterable[Dict]] = None,
    *,
    presets: Optional[Dict[str, tuple]] = None,
) -> bool:
    """Process ``input_path`` into ``output_path`` using the supplied operations."""

    if presets is None:
        presets = ASPECT_RATIO_PRESETS

    try:
        image = load_image(input_path)
        ops = list(operations or [])

        for operation in ops:
            if not isinstance(operation, dict):
                raise ValueError("Each operation must be a mapping.")

            op_type = operation.get("type")
            if op_type == "resize":
                size = _resolve_resize_target(operation, presets)
                image = resize_image(image, size)
            elif op_type == "grade":
                params = {k: v for k, v in operation.items() if k != "type"}
                image = _apply_grading(image, params)
            else:
                raise ValueError(f"Unsupported operation type: {op_type}")

        save_kwargs = {}
        # Allow quality overrides from final operation via "quality" key
        if ops:
            last_quality = next(
                (op["quality"] for op in reversed(ops) if "quality" in op),
                None,
            )
            if last_quality is not None:
                save_kwargs["quality"] = int(last_quality)

        save_image(image, output_path, **save_kwargs)
        return True
    except Exception as exc:
        print(f"Error processing variant {output_path}: {exc}")
        return False


def process_image(input_path, output_path, target_size=DCI_4K_RESOLUTION):
    """Backward compatible wrapper that resizes to ``target_size`` and saves."""

    return process_variant(
        input_path,
        output_path,
        operations=[{"type": "resize", "width": target_size[0], "height": target_size[1]}],
        presets={"__custom__": target_size},
    )
