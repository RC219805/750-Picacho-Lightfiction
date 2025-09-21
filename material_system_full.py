"""
Material and texture application system for luxury contemporary estate rendering
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import config
from spatial_analyzer import ArchitecturalElement

@dataclass
class MaterialProperties:
    """Represents PBR material properties"""
    base_color: Tuple[float, float, float]
    roughness: float
    metallic: float
    specular: float
    transparency: float = 0.0
    normal_strength: float = 1.0

class MaterialLibrary:
    """Library of luxury materials for contemporary estates"""
    
    def __init__(self):
        self.materials = self._initialize_materials()
        
    def _initialize_materials(self) -> Dict[str, MaterialProperties]:
        """Initialize the material library with luxury contemporary materials"""
        materials = {}
        
        # Convert config materials to MaterialProperties objects
        for name, props in config.LUXURY_MATERIALS.items():
            materials[name] = MaterialProperties(
                base_color=props['base_color'],
                roughness=props['roughness'],
                metallic=props['metallic'],
                specular=props['specular'],
                transparency=props.get('transparency', 0.0)
            )
        
        # Add additional luxury materials
        materials['travertine'] = MaterialProperties(
            base_color=(0.89, 0.85, 0.78),
            roughness=0.4,
            metallic=0.0,
            specular=0.3
        )
        
        materials['walnut'] = MaterialProperties(
            base_color=(0.4, 0.25, 0.15),
            roughness=0.35,
            metallic=0.0,
            specular=0.4
        )
        
        materials['limestone'] = MaterialProperties(
            base_color=(0.92, 0.90, 0.85),
            roughness=0.6,
            metallic=0.0,
            specular=0.2
        )
        
        return materials
    
    def get_material(self, name: str) -> Optional[MaterialProperties]:
        """Get material properties by name"""
        return self.materials.get(name)

class TextureGenerator:
    """Generates procedural textures for materials"""
    
    @staticmethod
    def generate_marble_texture(width: int, height: int, base_color: Tuple[float, float, float]) -> np.ndarray:
        """Generate a procedural marble texture"""
        # Create base noise pattern
        noise = np.random.rand(height, width)
        
        # Apply multiple octaves of noise for marble veining
        marble = np.zeros((height, width, 3), dtype=np.float32)
        
        # Base color
        marble[:, :, 0] = base_color[0]
        marble[:, :, 1] = base_color[1] 
        marble[:, :, 2] = base_color[2]
        
        # Add veining with Perlin-like noise
        for octave in range(3):
            scale = 2 ** octave
            octave_noise = cv2.resize(noise, (width//scale, height//scale))
            octave_noise = cv2.resize(octave_noise, (width, height))
            
            # Create veining pattern
            veins = np.sin(octave_noise * 10 + np.arange(width) * 0.01) * 0.1
            veins = np.tile(veins, (height, 1))
            
            # Apply veins to color channels
            marble[:, :, 0] -= veins * 0.05
            marble[:, :, 1] -= veins * 0.03
            marble[:, :, 2] -= veins * 0.02
        
        # Clamp values and convert to uint8
        marble = np.clip(marble * 255, 0, 255).astype(np.uint8)
        return marble
    
    @staticmethod
    def generate_wood_texture(width: int, height: int, base_color: Tuple[float, float, float]) -> np.ndarray:
        """Generate a procedural wood grain texture"""
        # Create wood grain pattern
        wood = np.zeros((height, width, 3), dtype=np.float32)
        
        # Base color
        wood[:, :, 0] = base_color[0]
        wood[:, :, 1] = base_color[1]
        wood[:, :, 2] = base_color[2]
        
        # Create grain pattern
        y_coords = np.arange(height)
        grain_pattern = np.sin(y_coords * 0.02) * 0.1 + np.sin(y_coords * 0.05) * 0.05
        grain_pattern = np.tile(grain_pattern.reshape(-1, 1), (1, width))
        
        # Add some random variation
        noise = np.random.rand(height, width) * 0.05
        grain_pattern += noise
        
        # Apply grain to all channels with different intensities
        wood[:, :, 0] += grain_pattern * 0.3
        wood[:, :, 1] += grain_pattern * 0.2
        wood[:, :, 2] += grain_pattern * 0.1
        
        # Clamp and convert
        wood = np.clip(wood * 255, 0, 255).astype(np.uint8)
        return wood
    
    @staticmethod
    def generate_glass_texture(width: int, height: int) -> np.ndarray:
        """Generate a subtle glass texture with reflective properties"""
        glass = np.ones((height, width, 3), dtype=np.uint8) * 250
        
        # Add subtle imperfections
        noise = np.random.rand(height, width) * 10
        glass[:, :, 0] -= noise
        glass[:, :, 1] -= noise
        glass[:, :, 2] -= noise
        
        return np.clip(glass, 0, 255)

class MaterialMapper:
    """Maps materials to detected architectural elements"""
    
    def __init__(self):
        self.material_library = MaterialLibrary()
        self.texture_generator = TextureGenerator()
        
        # Define material assignments for different elements
        self.element_materials = {
            'wall': ['limestone', 'travertine'],
            'floor': ['marble', 'walnut', 'travertine'],
            'ceiling': ['limestone'],
            'window': ['glass'],
            'door': ['walnut', 'steel']
        }
    
    def apply_materials(self, image: np.ndarray, elements: List[ArchitecturalElement]) -> np.ndarray:
        """
        Apply luxury materials to detected architectural elements
        
        Args:
            image: Original spatially precise rendering
            elements: List of detected architectural elements
            
        Returns:
            Image with materials applied
        """
        result = image.copy()
        
        # Resize to 4K DCI if needed
        if result.shape[:2] != (config.DCI_4K_HEIGHT, config.DCI_4K_WIDTH):
            result = cv2.resize(result, config.TARGET_RESOLUTION)
        
        # Apply materials to each element
        for element in elements:
            material_name = self._select_material_for_element(element)
            if material_name:
                result = self._apply_material_to_region(result, element, material_name)
        
        return result
    
    def _select_material_for_element(self, element: ArchitecturalElement) -> Optional[str]:
        """Select appropriate material for an architectural element"""
        possible_materials = self.element_materials.get(element.element_type, [])
        
        if not possible_materials:
            return None
            
        # For now, select first material. Could be enhanced with ML-based selection
        return possible_materials[0]
    
    def _apply_material_to_region(self, image: np.ndarray, element: ArchitecturalElement, material_name: str) -> np.ndarray:
        """Apply a specific material to a region of the image"""
        x, y, w, h = element.bounds
        
        # Ensure bounds are within image
        x = max(0, min(x, image.shape[1] - 1))
        y = max(0, min(y, image.shape[0] - 1))
        w = min(w, image.shape[1] - x)
        h = min(h, image.shape[0] - y)
        
        if w <= 0 or h <= 0:
            return image
        
        material = self.material_library.get_material(material_name)
        if not material:
            return image
        
        # Generate appropriate texture
        if material_name == 'marble':
            texture = self.texture_generator.generate_marble_texture(w, h, material.base_color)
        elif material_name in ['walnut', 'hardwood']:
            texture = self.texture_generator.generate_wood_texture(w, h, material.base_color)
        elif material_name == 'glass':
            texture = self.texture_generator.generate_glass_texture(w, h)
        else:
            # Default solid color texture
            color = tuple(int(c * 255) for c in material.base_color)
            texture = np.full((h, w, 3), color, dtype=np.uint8)
        
        # Blend texture with original image
        alpha = 0.8  # Material opacity
        image[y:y+h, x:x+w] = cv2.addWeighted(
            image[y:y+h, x:x+w], 1-alpha,
            texture, alpha,
            0
        )
        
        return image