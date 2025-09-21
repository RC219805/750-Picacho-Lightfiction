# 750-Picacho-Lightfiction

Spatially aware application of materials and textures to architectural renderings at 4K DCI resolution.

## Overview

This system transforms spatially precise architectural renderings (without surfaces, finishes, or advanced textures) into photorealistic renderings of luxury contemporary estates on Picacho Lane in Montecito. The pipeline delivers highest-caliber quality with paramount attention to detail.

## Features

### Core Capabilities
- **Spatial Analysis**: Automated detection of architectural elements (walls, floors, ceilings, windows, doors)
- **Luxury Material Library**: PBR-based materials including marble, limestone, walnut, glass, and steel
- **Montecito Lighting Simulation**: Natural lighting characteristics specific to Santa Barbara coastal environment
- **4K DCI Resolution**: Professional output at 4096×2160 resolution
- **Photorealistic Enhancement**: Advanced shadows, reflections, and atmospheric effects

### Specialized Features for Picacho Lane
- **Contemporary Aesthetic**: Material selections optimized for luxury contemporary architecture
- **Coastal Environment**: Atmospheric effects and lighting tuned for Montecito's coastal setting
- **Premium Finishes**: High-end material library with proper PBR properties
- **Professional Quality**: Ultra-high quality presets for architectural visualization

## Installation

### Requirements
```bash
pip install -r requirements.txt
```

Required packages:
- OpenCV (opencv-python>=4.8.0)
- Pillow (>=10.0.0)
- NumPy (>=1.21.0)
- SciPy (>=1.9.0)
- scikit-image (>=0.19.0)
- matplotlib (>=3.5.0)

### Quick Start

```bash
# Run demonstration
python picacho_pipeline.py --demo

# Process with different lighting
python picacho_pipeline.py --time golden_hour --quality ultra

# Available options
python picacho_pipeline.py --help
```

## Pipeline Architecture

### 1. Spatial Analysis (`spatial_analyzer.py`)
Detects and classifies architectural elements:
- Wall surfaces and orientations
- Floor and ceiling planes
- Window and door openings
- Geometric properties and confidence scoring

### 2. Material System (`material_system.py`)
Applies luxury materials with PBR properties:
- **MaterialLibrary**: 7+ premium materials with realistic properties
- **TextureGenerator**: Procedural texture generation for marble, wood, glass
- **MaterialMapper**: Intelligent material assignment based on element type

### 3. Photorealistic Enhancement (`photorealistic_enhancer.py`)
Renders realistic lighting and effects:
- **LightingSimulator**: Montecito-specific natural lighting
- **ShadowRenderer**: Environmental shadow casting
- **ReflectionRenderer**: Realistic surface reflections
- **PostProcessor**: Color grading and detail enhancement

### 4. Main Pipeline (`picacho_pipeline.py`)
Orchestrates the complete transformation:
- Quality presets (draft, high, ultra)
- Time-of-day lighting options
- 4K DCI output optimization
- Comprehensive result reporting

## Usage Examples

### Basic Usage
```python
from picacho_pipeline import PicachoRenderingPipeline

pipeline = PicachoRenderingPipeline()
result = pipeline.transform_rendering(
    input_description="Contemporary estate wireframe",
    time_of_day='midday',
    quality_preset='ultra'
)
```

### Material Customization
```python
from material_system import MaterialLibrary

materials = MaterialLibrary()
marble = materials.get_material('marble')
print(f"Marble properties: {marble.base_color}, roughness: {marble.roughness}")
```

### Lighting Configuration
```python
import config

# Montecito lighting characteristics
print(f"Golden hour temperature: {config.MONTECITO_LIGHTING['golden_hour_temp']}K")
print(f"Coastal haze factor: {config.MONTECITO_LIGHTING['coastal_haze_factor']}")
```

## Configuration

### Material Properties (`config.py`)
```python
LUXURY_MATERIALS = {
    'marble': {
        'roughness': 0.1,
        'metallic': 0.0,
        'specular': 0.9,
        'base_color': (0.95, 0.95, 0.92)
    },
    # ... additional materials
}
```

### Lighting Settings
```python
MONTECITO_LIGHTING = {
    'golden_hour_temp': 3200,  # Kelvin
    'midday_temp': 5600,
    'ambient_intensity': 0.3,
    'directional_intensity': 0.8,
    'coastal_haze_factor': 0.15
}
```

## Quality Presets

### Ultra Quality
- Maximum detail enhancement (80% strength)
- Ray-traced quality reflections
- Advanced noise reduction
- Luxury aesthetic color grading
- Professional 4K DCI output

### High Quality
- Enhanced detail sharpening (50% strength)
- Advanced material reflectance
- High-quality shadow sampling
- Improved texture resolution

### Draft Quality
- Basic material rendering
- Standard lighting calculation
- Fast preview quality

## Architecture Detection

The system automatically detects:
- **Walls**: Vertical surfaces with material assignment
- **Floors**: Horizontal base planes (typically marble/walnut)
- **Ceilings**: Horizontal top planes (typically limestone)
- **Windows**: Glass openings with reflections
- **Doors**: Wood/metal openings with appropriate materials

## Montecito-Specific Features

### Coastal Lighting
- Santa Barbara coastal atmospheric effects
- Natural haze simulation
- Temperature-accurate daylight simulation

### Luxury Materials
- Carrara marble flooring
- Limestone wall finishes
- Walnut wood elements
- High-performance glass
- Contemporary steel accents

### Contemporary Aesthetic
- Clean line emphasis
- Premium surface finishes
- Sophisticated color grading
- Professional architectural visualization standards

## Testing

```bash
# Run comprehensive pipeline test
python test_pipeline.py

# Test specific modules
python -c "from material_system import MaterialLibrary; print('Materials:', list(MaterialLibrary().materials.keys()))"
```

## Development

### Adding New Materials
1. Define material properties in `config.py`
2. Add to MaterialLibrary in `material_system.py`
3. Create texture generator if needed
4. Update element mapping in MaterialMapper

### Extending Lighting
1. Add lighting configuration to `config.py`
2. Implement in LightingSimulator
3. Add time-of-day option to pipeline

## System Requirements

- Python 3.7+
- 8GB+ RAM (for 4K processing)
- OpenCV-compatible system
- Storage space for 4K output images

## License

Professional architectural visualization system for Picacho Lane project.

## Output Quality

The system produces professional-grade photorealistic renderings suitable for:
- Architectural presentations
- Real estate marketing
- Design development
- Client visualization
- Professional portfolios

Target specifications:
- **Resolution**: 4096×2160 (DCI 4K)
- **Quality**: Photorealistic architectural visualization
- **Materials**: Luxury contemporary finishes
- **Lighting**: Montecito natural environment
- **Detail Level**: Highest caliber with paramount attention to detail
