"""
Core spatial analysis module for detecting architectural elements
in spatially precise renderings without textures/surfaces.
"""

import cv2
import numpy as np
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
    """Analyzes spatial renderings to detect architectural elements"""
    
    def __init__(self):
        self.detected_elements = []
        
    def analyze_rendering(self, image: np.ndarray) -> List[ArchitecturalElement]:
        """
        Analyze a spatially precise rendering to detect architectural elements
        
        Args:
            image: Input rendering as numpy array
            
        Returns:
            List of detected architectural elements
        """
        # Ensure image is in correct format
        if len(image.shape) == 3 and image.shape[2] == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        elements = []
        
        # Detect major structural elements
        elements.extend(self._detect_walls(gray, image))
        elements.extend(self._detect_floors_ceilings(gray, image))
        elements.extend(self._detect_openings(gray, image))
        
        self.detected_elements = elements
        return elements
    
    def _detect_walls(self, gray: np.ndarray, color_image: np.ndarray) -> List[ArchitecturalElement]:
        """Detect wall surfaces using edge detection and line analysis"""
        elements = []
        
        # Edge detection for structural lines
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Hough line detection for wall boundaries
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, 
                               minLineLength=50, maxLineGap=10)
        
        if lines is not None:
            # Group vertical lines as potential walls
            vertical_lines = []
            for line in lines:
                x1, y1, x2, y2 = line[0]
                angle = np.abs(np.arctan2(y2-y1, x2-x1) * 180 / np.pi)
                if angle > 80 and angle < 100:  # Near vertical
                    vertical_lines.append(line[0])
            
            # Create wall elements from vertical line clusters
            for i, line in enumerate(vertical_lines):
                x1, y1, x2, y2 = line
                x, y = min(x1, x2), min(y1, y2)
                w, h = abs(x2-x1) + 20, abs(y2-y1)  # Add width for wall thickness
                
                element = ArchitecturalElement(
                    element_type='wall',
                    bounds=(x, y, w, h),
                    confidence=0.8,
                    geometry={'orientation': 'vertical', 'line': line}
                )
                elements.append(element)
        
        return elements
    
    def _detect_floors_ceilings(self, gray: np.ndarray, color_image: np.ndarray) -> List[ArchitecturalElement]:
        """Detect floor and ceiling planes using horizontal line detection"""
        elements = []
        
        edges = cv2.Canny(gray, 30, 100)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=80, 
                               minLineLength=100, maxLineGap=20)
        
        if lines is not None:
            horizontal_lines = []
            for line in lines:
                x1, y1, x2, y2 = line[0]
                angle = np.abs(np.arctan2(y2-y1, x2-x1) * 180 / np.pi)
                if angle < 10 or angle > 170:  # Near horizontal
                    horizontal_lines.append(line[0])
            
            # Sort by y-coordinate to identify floor (bottom) and ceiling (top)
            horizontal_lines.sort(key=lambda line: min(line[1], line[3]))
            
            if len(horizontal_lines) >= 2:
                # Top line likely ceiling
                top_line = horizontal_lines[0]
                x1, y1, x2, y2 = top_line
                ceiling_element = ArchitecturalElement(
                    element_type='ceiling',
                    bounds=(0, min(y1, y2) - 10, color_image.shape[1], 20),
                    confidence=0.7,
                    geometry={'orientation': 'horizontal', 'line': top_line}
                )
                elements.append(ceiling_element)
                
                # Bottom line likely floor
                bottom_line = horizontal_lines[-1]
                x1, y1, x2, y2 = bottom_line
                floor_element = ArchitecturalElement(
                    element_type='floor',
                    bounds=(0, min(y1, y2), color_image.shape[1], 20),
                    confidence=0.7,
                    geometry={'orientation': 'horizontal', 'line': bottom_line}
                )
                elements.append(floor_element)
        
        return elements
    
    def _detect_openings(self, gray: np.ndarray, color_image: np.ndarray) -> List[ArchitecturalElement]:
        """Detect windows and doors as rectangular openings"""
        elements = []
        
        # Use contour detection to find rectangular regions
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            # Approximate contour to polygon
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # Look for rectangular shapes (4 corners)
            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = h / w if w > 0 else 0
                area = cv2.contourArea(contour)
                
                # Filter by size and aspect ratio
                if area > 1000:  # Minimum size threshold
                    if config.DETECTION_THRESHOLDS['door_aspect_ratio_range'][0] <= aspect_ratio <= config.DETECTION_THRESHOLDS['door_aspect_ratio_range'][1]:
                        # Likely a door
                        element = ArchitecturalElement(
                            element_type='door',
                            bounds=(x, y, w, h),
                            confidence=0.6,
                            geometry={'aspect_ratio': aspect_ratio, 'area': area}
                        )
                        elements.append(element)
                    elif aspect_ratio >= config.DETECTION_THRESHOLDS['window_aspect_ratio_min']:
                        # Likely a window
                        element = ArchitecturalElement(
                            element_type='window',
                            bounds=(x, y, w, h),
                            confidence=0.6,
                            geometry={'aspect_ratio': aspect_ratio, 'area': area}
                        )
                        elements.append(element)
        
        return elements