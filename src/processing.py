"""Core image manipulation functions using PIL (Pillow).

Handles loading, saving, resizing, cropping, and grading operations for images
while preserving image integrity and aspect ratios.
"""

from typing import Dict, Iterable, Optional
from PIL import Image, ImageEnhance, ImageOps
import os
import sys

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))
from config import ASPECT_RATIO_PRESETS, DCI_4K_RESOLUTION
from adjustments import (
    apply_crop_preset,
    apply_grading,
    enhance_material_definition,
    inpaint_with_mask,
)


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


def _resolve_mask(mask_reference, base_image_path: str) -> Image.Image:
    """Return a mask image for the supplied reference."""

    if isinstance(mask_reference, Image.Image):
        return mask_reference.convert("L")

    if not isinstance(mask_reference, str):
        raise TypeError("Mask reference must be a path or PIL image.")

    mask_path = mask_reference
    if not os.path.isabs(mask_path):
        mask_path = os.path.join(os.path.dirname(base_image_path), mask_path)

    if not os.path.exists(mask_path):
        raise FileNotFoundError(f"Mask file not found: {mask_path}")

    with Image.open(mask_path) as mask_image:
        return mask_image.convert("L")


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


# Note: Grading functionality is now handled by apply_grading() from adjustments.py
# which provides more advanced grading operations including temperature shift,
# shadow/highlight lift, and local contrast adjustments.


def _normalize_variant(variant: Optional[Dict]) -> Dict:
    """Return a normalized variant configuration dict."""

    if variant is None:
        return {}

    return dict(variant)


def _apply_variant_crop(image: Image.Image, variant: Dict) -> Image.Image:
    """Apply any configured crop to *image* and return the result."""

    crop_config = variant.get("crop")
    if not crop_config:
        return image

    if isinstance(crop_config, str):
        offset: Optional[Iterable[float]] = variant.get("crop_offset")
        return apply_crop_preset(image, crop_config, offset=offset)

    if isinstance(crop_config, dict):
        preset = crop_config.get("preset")
        if not preset:
            raise ValueError("Variant crop dictionaries must include a 'preset' key.")
        if "offset" in crop_config:
            local_offset = crop_config["offset"]
        else:
            local_offset = variant.get("crop_offset")
        return apply_crop_preset(image, preset, offset=local_offset)

    raise TypeError(
        "Variant crop configuration must be a preset name or mapping with a 'preset' key."
    )


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
            elif op_type == "crop":
                # Support crop operations in YAML manifests
                preset = operation.get("preset")
                if not preset:
                    raise ValueError("Crop operation must include a 'preset' key.")
                offset = operation.get("offset")
                image = apply_crop_preset(image, preset, offset=offset)
            elif op_type == "grade":
                params = {k: v for k, v in operation.items() if k != "type"}
                # Use the advanced grading from adjustments.py instead of the simple one
                image = apply_grading(image, params)
            elif op_type == "inpaint":
                mask_ref = operation.get("mask")
                if mask_ref is None:
                    raise ValueError("Inpaint operation requires a 'mask' entry.")

                mask_image = _resolve_mask(mask_ref, input_path)
                blur_radius = float(operation.get("blur_radius", 25.0))
                feather_radius = float(operation.get("feather_radius", 8.0))
                strength = float(operation.get("strength", 1.0))

                image = inpaint_with_mask(
                    image,
                    mask_image,
                    blur_radius=blur_radius,
                    feather_radius=feather_radius,
                    strength=strength,
                )
            elif op_type in {"material_enhance", "enhance_materials"}:
                params = {k: v for k, v in operation.items() if k != "type"}
                image = enhance_material_definition(
                    image,
                    clarity=float(params.get("clarity", 1.2)),
                    micro_contrast=float(params.get("micro_contrast", params.get("texture", 1.15))),
                    depth=float(params.get("depth", params.get("contrast", 1.05))),
                    sheen=float(params.get("sheen", params.get("saturation", 1.05))),
                )
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


def process_image(
    input_path,
    output_path,
    target_size=DCI_4K_RESOLUTION,
    crop_box=None,
    grading=None,
    *,
    variant: Optional[Dict] = None,
):
    """
    Complete image processing workflow: load, adjust, resize, and save.
    
    Args:
        input_path (str): Path to the input image
        output_path (str): Path for the output image
        target_size (tuple): Target size for resizing
        crop_box (tuple, optional): Manual crop box (left, top, right, bottom)
        grading (dict, optional): Grading parameters for color adjustments
        variant (dict, optional): Additional directives for this render variant.
            Supported keys include:
            ``"crop"`` (preset name or ``{"preset": name, "offset": (x, y)}``),
            ``"crop_offset"`` (fallback offset tuple), and ``"size"`` to override
            the target resolution.
        
    Returns:
        bool: True if processing was successful, False otherwise
    """
    try:
        # Load the image
        image = load_image(input_path)

        variant_config = _normalize_variant(variant)

        # Apply manual crop box if specified (for backward compatibility)
        if crop_box is not None:
            image = image.crop(tuple(crop_box))

        # Apply variant-driven cropping before resizing so padding occurs only
        # after the target aspect ratio has been satisfied.
        image = _apply_variant_crop(image, variant_config)

        if "size" in variant_config:
            target_size = tuple(variant_config["size"])

        # Resize to target resolution when requested
        processed_image = (
            resize_image(image, target_size) if target_size is not None else image.copy()
        )

        if grading:
            processed_image = apply_grading(processed_image, grading)

        # Save the processed image
        save_image(processed_image, output_path)
        
        return True
    except Exception as e:
        print(f"Error processing image {input_path}: {str(e)}")
        return False
