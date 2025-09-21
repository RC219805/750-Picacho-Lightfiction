"""
Simplified material system for demonstration without heavy dependencies
"""

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

class MaterialMapper:
    """Simplified material mapper for demonstration"""
    
    def __init__(self):
        self.material_library = MaterialLibrary()
        
        # Define material assignments for different elements
        self.element_materials = {
            'wall': ['limestone', 'travertine'],
            'floor': ['marble', 'walnut', 'travertine'],
            'ceiling': ['limestone'],
            'window': ['glass'],
            'door': ['walnut', 'steel']
        }
    
    def apply_materials(self, elements: List[ArchitecturalElement]) -> Dict[str, str]:
        """
        Simulate material application to detected architectural elements
        
        Args:
            elements: List of detected architectural elements
            
        Returns:
            Dictionary mapping element types to selected materials
        """
        applied_materials = {}
        
        # Apply materials to each element
        for element in elements:
            material_name = self._select_material_for_element(element)
            if material_name:
                applied_materials[f"{element.element_type}_{id(element)}"] = material_name
        
        return applied_materials
    
    def _select_material_for_element(self, element: ArchitecturalElement) -> Optional[str]:
        """Select appropriate material for an architectural element"""
        possible_materials = self.element_materials.get(element.element_type, [])
        
        if not possible_materials:
            return None
            
        # For luxury estate, prefer premium materials
        if element.element_type == 'floor':
            return 'marble'  # Luxury flooring
        elif element.element_type == 'wall':
            return 'limestone'  # Contemporary wall finish
        elif element.element_type == 'window':
            return 'glass'
        elif element.element_type == 'door':
            return 'walnut'  # High-end wood door
        elif element.element_type == 'ceiling':
            return 'limestone'
        
        return possible_materials[0]

# Try to import full version if dependencies are available
try:
    import cv2
    import numpy as np
    from material_system_full import MaterialMapper as FullMaterialMapper
    # Use full version if available
    MaterialMapper = FullMaterialMapper
except ImportError:
    # Use simplified version defined above
    pass