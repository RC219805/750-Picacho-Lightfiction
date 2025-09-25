"""
Core image manipulation functions using PIL (Pillow).
Handles loading, saving, and resizing of images.
"""

from PIL import Image
import os
import sys

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))
from config import DCI_4K_RESOLUTION


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


def resize_image(image, target_size=DCI_4K_RESOLUTION, resample=Image.LANCZOS):
    """
    Resize an image to the target size.
    
    Args:
        image (PIL.Image): The image to resize
        target_size (tuple): Target size as (width, height)
        resample: Resampling algorithm (default: LANCZOS for high quality)
        
    Returns:
        PIL.Image: The resized image
    """
    return image.resize(target_size, resample)


def process_image(input_path, output_path, target_size=DCI_4K_RESOLUTION):
    """
    Complete image processing workflow: load, resize, and save.
    
    Args:
        input_path (str): Path to the input image
        output_path (str): Path for the output image
        target_size (tuple): Target size for resizing
        
    Returns:
        bool: True if processing was successful, False otherwise
    """
    try:
        # Load the image
        image = load_image(input_path)
        
        # Resize to target resolution
        processed_image = resize_image(image, target_size)
        
        # Save the processed image
        save_image(processed_image, output_path)
        
        return True
    except Exception as e:
        print(f"Error processing image {input_path}: {str(e)}")
        return False