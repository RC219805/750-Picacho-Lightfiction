"""
Main pipeline for processing architectural renderings.
Iterates through images in the input directory, applies processing,
and saves results to the output directory.
"""

import os
import sys
from pathlib import Path

# Add src directory to path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__)))

from processing import process_image
from config import INPUT_DIR, OUTPUT_DIR, DCI_4K_RESOLUTION


def get_image_files(directory):
    """
    Get list of image files from the specified directory.
    
    Args:
        directory (str): Directory path to scan for images
        
    Returns:
        list: List of image file paths
    """
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    image_files = []
    
    if not os.path.exists(directory):
        print(f"Input directory '{directory}' does not exist.")
        return image_files
    
    for file in os.listdir(directory):
        if any(file.lower().endswith(ext) for ext in image_extensions):
            image_files.append(os.path.join(directory, file))
    
    return sorted(image_files)


def main():
    """
    Main pipeline execution.
    Processes all images in the input directory and saves them to the output directory.
    """
    print("Starting rendering pipeline...")
    print(f"Target resolution: {DCI_4K_RESOLUTION[0]}x{DCI_4K_RESOLUTION[1]} (4K DCI)")
    
    # Get all image files from input directory
    input_files = get_image_files(INPUT_DIR)
    
    if not input_files:
        print(f"No image files found in '{INPUT_DIR}' directory.")
        print("Please add some images to process.")
        return
    
    print(f"Found {len(input_files)} image(s) to process:")
    for file in input_files:
        print(f"  - {os.path.basename(file)}")
    
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Process each image
    processed_count = 0
    failed_count = 0
    
    for input_file in input_files:
        filename = os.path.basename(input_file)
        name, ext = os.path.splitext(filename)
        output_file = os.path.join(OUTPUT_DIR, f"{name}_processed{ext}")
        
        print(f"Processing: {filename}...")
        
        success = process_image(input_file, output_file)
        
        if success:
            processed_count += 1
            print(f"  ✓ Saved to: {os.path.basename(output_file)}")
        else:
            failed_count += 1
            print(f"  ✗ Failed to process: {filename}")
    
    print(f"\nPipeline completed!")
    print(f"Successfully processed: {processed_count} images")
    if failed_count > 0:
        print(f"Failed to process: {failed_count} images")
    
    print(f"Results saved in '{OUTPUT_DIR}' directory.")


if __name__ == "__main__":
    main()