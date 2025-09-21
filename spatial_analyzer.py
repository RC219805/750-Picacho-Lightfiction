"""
Fallback spatial analysis module using basic Python for demonstration
when OpenCV is not available
"""

import os
import sys
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import config

@dataclass
class ArchitecturalElement:
    """Represents a detected architectural element"""
    element_type: str  # 'wall', 'floor', 'ceiling', 'window', 'door'
    bounds: Tuple[int, int, int, int]  # x, y, width, height
    confidence: float
    geometry: Dict  # Additional geometric properties
    material_hint: Optional[str] = None

class SpatialAnalyzer:
    """Simplified spatial analyzer for demonstration purposes"""
    
    def __init__(self):
        self.detected_elements = []
        
    def analyze_rendering(self, image_path: str = None) -> List[ArchitecturalElement]:
        """
        Simulate architectural element detection for demonstration
        
        Args:
            image_path: Path to input image (simulated for now)
            
        Returns:
            List of simulated architectural elements
        """
        # Simulate detected elements for a luxury contemporary estate
        elements = []
        
        # Simulate wall detection
        wall1 = ArchitecturalElement(
            element_type='wall',
            bounds=(100, 200, 50, 1500),  # Left wall
            confidence=0.92,
            geometry={'orientation': 'vertical', 'surface_area': 75000}
        )
        elements.append(wall1)
        
        wall2 = ArchitecturalElement(
            element_type='wall', 
            bounds=(3900, 200, 50, 1500),  # Right wall
            confidence=0.89,
            geometry={'orientation': 'vertical', 'surface_area': 75000}
        )
        elements.append(wall2)
        
        # Simulate floor detection
        floor = ArchitecturalElement(
            element_type='floor',
            bounds=(0, 1800, config.DCI_4K_WIDTH, 200),
            confidence=0.95,
            geometry={'orientation': 'horizontal', 'surface_area': 800000}
        )
        elements.append(floor)
        
        # Simulate ceiling detection
        ceiling = ArchitecturalElement(
            element_type='ceiling',
            bounds=(0, 100, config.DCI_4K_WIDTH, 100),
            confidence=0.88,
            geometry={'orientation': 'horizontal', 'surface_area': 400000}
        )
        elements.append(ceiling)
        
        # Simulate window detection
        window1 = ArchitecturalElement(
            element_type='window',
            bounds=(1200, 600, 800, 600),
            confidence=0.85,
            geometry={'aspect_ratio': 0.75, 'area': 480000}
        )
        elements.append(window1)
        
        window2 = ArchitecturalElement(
            element_type='window',
            bounds=(2400, 600, 800, 600),
            confidence=0.82,
            geometry={'aspect_ratio': 0.75, 'area': 480000}
        )
        elements.append(window2)
        
        # Simulate door detection
        door = ArchitecturalElement(
            element_type='door',
            bounds=(1800, 1000, 400, 800),
            confidence=0.78,
            geometry={'aspect_ratio': 2.0, 'area': 320000}
        )
        elements.append(door)
        
        self.detected_elements = elements
        return elements

# Keep the imports flexible for when OpenCV becomes available
try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    # Create minimal numpy-like functionality for basic operations
    class MockNumPy:
        @staticmethod
        def array(data):
            return data
        
        @staticmethod
        def zeros(shape, dtype=None):
            if len(shape) == 3:
                return [[[0 for _ in range(shape[2])] for _ in range(shape[1])] for _ in range(shape[0])]
            elif len(shape) == 2:
                return [[0 for _ in range(shape[1])] for _ in range(shape[0])]
            else:
                return [0] * shape[0]
    
    np = MockNumPy()

if OPENCV_AVAILABLE:
    # Import the full-featured version when OpenCV is available
    from spatial_analyzer_full import SpatialAnalyzer as FullSpatialAnalyzer
    SpatialAnalyzer = FullSpatialAnalyzer