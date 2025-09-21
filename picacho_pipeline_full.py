"""
Main rendering pipeline for transforming spatially precise renderings
into photorealistic luxury contemporary estate renderings for Picacho Lane, Montecito
"""

import cv2
import numpy as np
import os
from typing import Optional, Dict, Any
import argparse

from spatial_analyzer import SpatialAnalyzer
from material_system import MaterialMapper
from photorealistic_enhancer import PhotorealisticProcessor
import config

class PicachoRenderingPipeline:
    """Main pipeline for Picacho Lane luxury estate rendering transformation"""
    
    def __init__(self):
        self.spatial_analyzer = SpatialAnalyzer()
        self.material_mapper = MaterialMapper()
        self.photorealistic_processor = PhotorealisticProcessor()
        
    def transform_rendering(self, input_path: str, output_path: str, 
                          time_of_day: str = 'midday', 
                          quality_preset: str = 'ultra') -> Dict[str, Any]:
        """
        Transform a spatially precise rendering into a photorealistic luxury estate rendering
        
        Args:
            input_path: Path to input spatially precise rendering
            output_path: Path for output photorealistic rendering
            time_of_day: Lighting preference ('golden_hour', 'midday', 'evening')
            quality_preset: Quality level ('draft', 'high', 'ultra')
            
        Returns:
            Dictionary with processing statistics and metadata
        """
        # Load input image
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        image = cv2.imread(input_path)
        if image is None:
            raise ValueError(f"Could not load image from: {input_path}")
        
        print(f"Processing {input_path}...")
        print(f"Original image size: {image.shape}")
        
        # Step 1: Spatial Analysis
        print("Step 1: Analyzing spatial structure...")
        elements = self.spatial_analyzer.analyze_rendering(image)
        print(f"Detected {len(elements)} architectural elements:")
        for element in elements:
            print(f"  - {element.element_type}: {element.bounds} (confidence: {element.confidence:.2f})")
        
        # Step 2: Material Application
        print("Step 2: Applying luxury materials...")
        materialized_image = self.material_mapper.apply_materials(image, elements)
        
        # Step 3: Photorealistic Enhancement
        print("Step 3: Applying photorealistic enhancements...")
        final_image = self.photorealistic_processor.enhance_rendering(
            materialized_image, elements, time_of_day
        )
        
        # Step 4: Quality optimization based on preset
        print(f"Step 4: Applying {quality_preset} quality optimization...")
        final_image = self._apply_quality_preset(final_image, quality_preset)
        
        # Ensure output is at 4K DCI resolution
        if final_image.shape[:2] != (config.DCI_4K_HEIGHT, config.DCI_4K_WIDTH):
            print(f"Resizing to 4K DCI resolution: {config.TARGET_RESOLUTION}")
            final_image = cv2.resize(final_image, config.TARGET_RESOLUTION, 
                                   interpolation=cv2.INTER_LANCZOS4)
        
        # Save result
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        success = cv2.imwrite(output_path, final_image)
        
        if not success:
            raise RuntimeError(f"Failed to save output image to: {output_path}")
        
        print(f"Successfully saved photorealistic rendering to: {output_path}")
        
        # Return processing metadata
        return {
            'input_path': input_path,
            'output_path': output_path,
            'input_resolution': image.shape,
            'output_resolution': final_image.shape,
            'elements_detected': len(elements),
            'time_of_day': time_of_day,
            'quality_preset': quality_preset,
            'elements_summary': {element.element_type: element.confidence 
                               for element in elements}
        }
    
    def _apply_quality_preset(self, image: np.ndarray, preset: str) -> np.ndarray:
        """Apply quality-specific processing"""
        if preset == 'draft':
            # Faster processing with reduced quality
            return image
        elif preset == 'high':
            # Enhanced processing
            return self._enhance_details(image, strength=0.5)
        elif preset == 'ultra':
            # Maximum quality processing
            enhanced = self._enhance_details(image, strength=0.8)
            return self._apply_noise_reduction(enhanced)
        else:
            return image
    
    def _enhance_details(self, image: np.ndarray, strength: float = 0.5) -> np.ndarray:
        """Enhance fine details in the rendering"""
        # Unsharp mask for detail enhancement
        gaussian = cv2.GaussianBlur(image, (9, 9), 2.0)
        unsharp_mask = cv2.addWeighted(image, 1.0 + strength, gaussian, -strength, 0)
        return unsharp_mask
    
    def _apply_noise_reduction(self, image: np.ndarray) -> np.ndarray:
        """Apply sophisticated noise reduction for ultra quality"""
        # Non-local means denoising for highest quality
        return cv2.fastNlMeansDenoisingColored(image, None, 3, 3, 7, 21)

def create_sample_input():
    """Create a sample spatially precise rendering for testing"""
    # Create a simple architectural wireframe
    sample = np.ones((config.DCI_4K_HEIGHT, config.DCI_4K_WIDTH, 3), dtype=np.uint8) * 240
    
    # Draw basic architectural elements
    # Floor line
    cv2.line(sample, (0, int(config.DCI_4K_HEIGHT * 0.8)), 
             (config.DCI_4K_WIDTH, int(config.DCI_4K_HEIGHT * 0.8)), (100, 100, 100), 3)
    
    # Ceiling line
    cv2.line(sample, (0, int(config.DCI_4K_HEIGHT * 0.2)), 
             (config.DCI_4K_WIDTH, int(config.DCI_4K_HEIGHT * 0.2)), (100, 100, 100), 3)
    
    # Wall lines
    cv2.line(sample, (int(config.DCI_4K_WIDTH * 0.1), int(config.DCI_4K_HEIGHT * 0.2)), 
             (int(config.DCI_4K_WIDTH * 0.1), int(config.DCI_4K_HEIGHT * 0.8)), (100, 100, 100), 3)
    cv2.line(sample, (int(config.DCI_4K_WIDTH * 0.9), int(config.DCI_4K_HEIGHT * 0.2)), 
             (int(config.DCI_4K_WIDTH * 0.9), int(config.DCI_4K_HEIGHT * 0.8)), (100, 100, 100), 3)
    
    # Window rectangles
    cv2.rectangle(sample, (int(config.DCI_4K_WIDTH * 0.3), int(config.DCI_4K_HEIGHT * 0.3)), 
                  (int(config.DCI_4K_WIDTH * 0.5), int(config.DCI_4K_HEIGHT * 0.6)), (80, 80, 80), 2)
    cv2.rectangle(sample, (int(config.DCI_4K_WIDTH * 0.6), int(config.DCI_4K_HEIGHT * 0.3)), 
                  (int(config.DCI_4K_WIDTH * 0.8), int(config.DCI_4K_HEIGHT * 0.6)), (80, 80, 80), 2)
    
    # Door rectangle
    cv2.rectangle(sample, (int(config.DCI_4K_WIDTH * 0.45), int(config.DCI_4K_HEIGHT * 0.5)), 
                  (int(config.DCI_4K_WIDTH * 0.55), int(config.DCI_4K_HEIGHT * 0.8)), (60, 60, 60), 2)
    
    return sample

def main():
    """Command line interface for the rendering pipeline"""
    parser = argparse.ArgumentParser(description='Picacho Lane Luxury Estate Rendering Pipeline')
    parser.add_argument('input', nargs='?', help='Input spatially precise rendering path')
    parser.add_argument('-o', '--output', help='Output path for photorealistic rendering')
    parser.add_argument('-t', '--time', choices=['golden_hour', 'midday', 'evening'], 
                       default='midday', help='Time of day for lighting')
    parser.add_argument('-q', '--quality', choices=['draft', 'high', 'ultra'], 
                       default='ultra', help='Quality preset')
    parser.add_argument('--create-sample', action='store_true', 
                       help='Create a sample input for testing')
    
    args = parser.parse_args()
    
    # Create sample if requested
    if args.create_sample:
        sample_path = 'sample_input.jpg'
        sample = create_sample_input()
        cv2.imwrite(sample_path, sample)
        print(f"Created sample input: {sample_path}")
        
        if not args.input:
            args.input = sample_path
    
    if not args.input:
        print("Error: Input file required. Use --create-sample to generate a test image.")
        return
    
    # Set default output path if not provided
    if not args.output:
        base_name = os.path.splitext(os.path.basename(args.input))[0]
        args.output = f"{base_name}_picacho_luxury_{args.time}_{args.quality}.jpg"
    
    # Initialize and run pipeline
    pipeline = PicachoRenderingPipeline()
    
    try:
        result = pipeline.transform_rendering(
            args.input, 
            args.output, 
            args.time, 
            args.quality
        )
        
        print("\n=== Processing Complete ===")
        print(f"Input: {result['input_path']}")
        print(f"Output: {result['output_path']}")
        print(f"Input Resolution: {result['input_resolution']}")
        print(f"Output Resolution: {result['output_resolution']}")
        print(f"Elements Detected: {result['elements_detected']}")
        print(f"Time of Day: {result['time_of_day']}")
        print(f"Quality Preset: {result['quality_preset']}")
        
        if result['elements_summary']:
            print("\nDetected Elements:")
            for element_type, confidence in result['elements_summary'].items():
                print(f"  {element_type}: {confidence:.2f}")
        
    except Exception as e:
        print(f"Error processing rendering: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())