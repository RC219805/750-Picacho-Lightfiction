"""Core image manipulation functions using PIL (Pillow).

Handles loading, saving, and resizing of images while preserving image
integrity and aspect ratios.
"""

from PIL import Image, ImageOps
import os
import sys
from typing import Dict, Iterable, Optional

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))
from config import DCI_4K_RESOLUTION
from adjustments import apply_crop_preset


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


def process_image(
    input_path,
    output_path,
    target_size=DCI_4K_RESOLUTION,
    *,
    variant: Optional[Dict] = None,
):
    """
    Complete image processing workflow: load, adjust, resize, and save.

    Args:
        input_path (str): Path to the input image
        output_path (str): Path for the output image
        target_size (tuple): Target size for resizing
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

        # Apply variant-driven cropping before resizing so padding occurs only
        # after the target aspect ratio has been satisfied.
        image = _apply_variant_crop(image, variant_config)

        if "size" in variant_config:
            target_size = tuple(variant_config["size"])

        # Resize to target resolution
        processed_image = resize_image(image, target_size)
        
        # Save the processed image
        save_image(processed_image, output_path)
        
        return True
    except Exception as e:
        print(f"Error processing image {input_path}: {str(e)}")
        return False
