"""
Photorealistic enhancement system for luxury estate rendering
Implements advanced lighting, shadows, reflections, and atmospheric effects
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
from scipy import ndimage
import config

class LightingSimulator:
    """Simulates natural Montecito lighting conditions"""
    
    def __init__(self):
        self.lighting_config = config.MONTECITO_LIGHTING
    
    def apply_natural_lighting(self, image: np.ndarray, time_of_day: str = 'midday') -> np.ndarray:
        """
        Apply natural lighting characteristics specific to Montecito/Santa Barbara
        
        Args:
            image: Input image
            time_of_day: 'golden_hour', 'midday', or 'evening'
        """
        result = image.copy().astype(np.float32) / 255.0
        
        if time_of_day == 'golden_hour':
            # Warm, golden lighting
            temp_kelvin = self.lighting_config['golden_hour_temp']
            warmth_factor = self._kelvin_to_rgb_factor(temp_kelvin)
            result = self._apply_color_temperature(result, warmth_factor)
            
            # Increase contrast and saturation for golden hour
            result = self._adjust_contrast_saturation(result, contrast=1.2, saturation=1.3)
            
        elif time_of_day == 'midday':
            # Neutral, bright lighting
            temp_kelvin = self.lighting_config['midday_temp']
            neutral_factor = self._kelvin_to_rgb_factor(temp_kelvin)
            result = self._apply_color_temperature(result, neutral_factor)
            
            # High contrast for bright midday sun
            result = self._adjust_contrast_saturation(result, contrast=1.4, saturation=1.1)
        
        # Apply coastal atmospheric effects
        result = self._apply_coastal_atmosphere(result)
        
        return np.clip(result * 255, 0, 255).astype(np.uint8)
    
    def _kelvin_to_rgb_factor(self, kelvin: int) -> Tuple[float, float, float]:
        """Convert color temperature in Kelvin to RGB multipliers"""
        # Simplified conversion for architectural rendering
        if kelvin < 3500:  # Warm
            return (1.0, 0.9, 0.7)
        elif kelvin < 5000:  # Neutral warm
            return (1.0, 0.95, 0.85)
        elif kelvin < 6500:  # Neutral
            return (0.95, 1.0, 1.0)
        else:  # Cool
            return (0.9, 0.95, 1.0)
    
    def _apply_color_temperature(self, image: np.ndarray, rgb_factor: Tuple[float, float, float]) -> np.ndarray:
        """Apply color temperature adjustment"""
        result = image.copy()
        result[:, :, 0] *= rgb_factor[2]  # Blue channel (BGR format)
        result[:, :, 1] *= rgb_factor[1]  # Green channel
        result[:, :, 2] *= rgb_factor[0]  # Red channel
        return result
    
    def _adjust_contrast_saturation(self, image: np.ndarray, contrast: float, saturation: float) -> np.ndarray:
        """Adjust contrast and saturation"""
        # Convert to HSV for saturation adjustment
        hsv = cv2.cvtColor((image * 255).astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32) / 255.0
        
        # Adjust saturation
        hsv[:, :, 1] *= saturation
        hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 1)
        
        # Convert back to BGR
        result = cv2.cvtColor((hsv * 255).astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32) / 255.0
        
        # Adjust contrast
        result = (result - 0.5) * contrast + 0.5
        
        return np.clip(result, 0, 1)
    
    def _apply_coastal_atmosphere(self, image: np.ndarray) -> np.ndarray:
        """Apply subtle coastal atmospheric effects (slight haze)"""
        haze_factor = self.lighting_config['coastal_haze_factor']
        
        # Create subtle haze overlay
        haze_color = np.array([0.9, 0.95, 1.0])  # Slight blue tint
        haze_overlay = np.ones_like(image) * haze_color
        
        # Apply distance-based haze (stronger towards background)
        height, width = image.shape[:2]
        distance_mask = np.linspace(0, 1, height).reshape(-1, 1)
        distance_mask = np.tile(distance_mask, (1, width))
        
        # Blend haze based on distance
        haze_strength = distance_mask * haze_factor
        haze_strength = np.expand_dims(haze_strength, axis=2)
        
        result = image * (1 - haze_strength) + haze_overlay * haze_strength
        return result

class ShadowRenderer:
    """Renders realistic shadows and reflections"""
    
    def add_environmental_shadows(self, image: np.ndarray, elements: List) -> np.ndarray:
        """Add realistic environmental shadows"""
        result = image.copy()
        
        # Simulate sun angle for Montecito (approximately 34°N latitude)
        sun_angle = 45  # Simplified midday angle
        shadow_length_factor = 1.0 / np.tan(np.radians(sun_angle))
        
        # Create shadow overlay
        shadow_overlay = np.zeros_like(image, dtype=np.float32)
        
        # For each architectural element, calculate shadow
        for element in elements:
            if element.element_type in ['wall', 'door']:
                shadow_mask = self._create_shadow_mask(element, shadow_length_factor, image.shape)
                shadow_overlay += shadow_mask
        
        # Apply shadows
        shadow_overlay = np.clip(shadow_overlay, 0, 0.4)  # Limit shadow intensity
        result = result.astype(np.float32)
        result = result * (1 - shadow_overlay) + result * shadow_overlay * 0.3
        
        return np.clip(result, 0, 255).astype(np.uint8)
    
    def _create_shadow_mask(self, element, shadow_length_factor: float, image_shape: Tuple[int, int]) -> np.ndarray:
        """Create shadow mask for an architectural element"""
        mask = np.zeros(image_shape[:2], dtype=np.float32)
        
        x, y, w, h = element.bounds
        
        # Calculate shadow projection
        shadow_offset_x = int(h * shadow_length_factor * 0.5)
        shadow_offset_y = int(h * 0.2)  # Ground shadow
        
        # Create shadow region
        shadow_x = min(x + shadow_offset_x, image_shape[1] - 1)
        shadow_y = min(y + h, image_shape[0] - 1)
        shadow_w = min(w, image_shape[1] - shadow_x)
        shadow_h = min(shadow_offset_y, image_shape[0] - shadow_y)
        
        if shadow_w > 0 and shadow_h > 0:
            # Create gradient shadow
            for i in range(shadow_h):
                intensity = 1.0 - (i / shadow_h)  # Fade shadow
                mask[shadow_y + i:shadow_y + i + 1, shadow_x:shadow_x + shadow_w] = intensity * 0.3
        
        return np.expand_dims(mask, axis=2)

class ReflectionRenderer:
    """Renders reflections for glass and metallic surfaces"""
    
    def add_environmental_reflections(self, image: np.ndarray, elements: List) -> np.ndarray:
        """Add realistic reflections to glass and metallic surfaces"""
        result = image.copy()
        
        for element in elements:
            if element.element_type == 'window' or (hasattr(element, 'material_hint') and 
                                                   element.material_hint in ['glass', 'steel']):
                result = self._add_reflection_to_element(result, element)
        
        return result
    
    def _add_reflection_to_element(self, image: np.ndarray, element) -> np.ndarray:
        """Add reflection effect to a specific element"""
        x, y, w, h = element.bounds
        
        # Ensure bounds are valid
        x = max(0, min(x, image.shape[1] - w))
        y = max(0, min(y, image.shape[0] - h))
        w = min(w, image.shape[1] - x)
        h = min(h, image.shape[0] - y)
        
        if w <= 0 or h <= 0:
            return image
        
        # Create sky reflection (simplified)
        sky_color = np.array([220, 240, 255], dtype=np.uint8)  # Light blue sky
        
        # Create gradient reflection
        reflection = np.zeros((h, w, 3), dtype=np.uint8)
        for i in range(h):
            intensity = 1.0 - (i / h)  # Stronger reflection at top
            reflection[i, :] = sky_color * intensity + image[y + i, x:x + w] * (1 - intensity * 0.3)
        
        # Apply reflection with some transparency
        alpha = 0.4 if element.element_type == 'window' else 0.6
        image[y:y+h, x:x+w] = cv2.addWeighted(
            image[y:y+h, x:x+w], 1-alpha,
            reflection, alpha,
            0
        )
        
        return image

class PhotorealisticProcessor:
    """Main processor for photorealistic enhancement"""
    
    def __init__(self):
        self.lighting_simulator = LightingSimulator()
        self.shadow_renderer = ShadowRenderer()
        self.reflection_renderer = ReflectionRenderer()
    
    def enhance_rendering(self, image: np.ndarray, elements: List, 
                         time_of_day: str = 'midday') -> np.ndarray:
        """
        Apply complete photorealistic enhancement pipeline
        
        Args:
            image: Input image with materials applied
            elements: Detected architectural elements
            time_of_day: Lighting time preference
            
        Returns:
            Photorealistic enhanced rendering
        """
        # Step 1: Apply natural lighting
        result = self.lighting_simulator.apply_natural_lighting(image, time_of_day)
        
        # Step 2: Add environmental shadows
        result = self.shadow_renderer.add_environmental_shadows(result, elements)
        
        # Step 3: Add reflections
        result = self.reflection_renderer.add_environmental_reflections(result, elements)
        
        # Step 4: Final post-processing
        result = self._apply_final_postprocessing(result)
        
        return result
    
    def _apply_final_postprocessing(self, image: np.ndarray) -> np.ndarray:
        """Apply final post-processing for maximum photorealism"""
        result = image.copy()
        
        # Slight gaussian blur for softer look
        result = cv2.GaussianBlur(result, (3, 3), 0.5)
        
        # Enhance micro-contrast
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(result, -1, kernel)
        result = cv2.addWeighted(result, 0.8, sharpened, 0.2, 0)
        
        # Color grading for luxury aesthetic
        result = self._apply_luxury_color_grading(result)
        
        return result
    
    def _apply_luxury_color_grading(self, image: np.ndarray) -> np.ndarray:
        """Apply color grading for luxury aesthetic"""
        # Convert to float for precise manipulation
        result = image.astype(np.float32) / 255.0
        
        # Slightly warm the shadows, cool the highlights
        # This is a simplified color grading approach
        luminance = 0.299 * result[:,:,2] + 0.587 * result[:,:,1] + 0.114 * result[:,:,0]
        
        # Create masks for shadows and highlights
        shadows_mask = (luminance < 0.3).astype(np.float32)
        highlights_mask = (luminance > 0.7).astype(np.float32)
        
        # Apply subtle color shifts
        result[:,:,2] += shadows_mask * 0.02  # Warm shadows (more red)
        result[:,:,0] += highlights_mask * 0.02  # Cool highlights (more blue)
        
        # Increase overall richness
        result = np.power(result, 0.95)  # Slight gamma adjustment
        
        return np.clip(result * 255, 0, 255).astype(np.uint8)