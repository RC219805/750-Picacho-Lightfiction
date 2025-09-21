"""
Example usage of the Picacho Lane Luxury Estate Rendering Pipeline
Demonstrates various features and configurations
"""

from picacho_pipeline import PicachoRenderingPipeline
from material_system import MaterialLibrary, MaterialMapper
from spatial_analyzer import SpatialAnalyzer
from photorealistic_enhancer import PhotorealisticProcessor
import config

def demo_material_library():
    """Demonstrate the material library capabilities"""
    print("=== LUXURY MATERIAL LIBRARY DEMO ===")
    
    materials = MaterialLibrary()
    print(f"Available materials: {len(materials.materials)}")
    
    for name, material in materials.materials.items():
        print(f"\n{name.upper()}:")
        print(f"  Base Color: RGB{material.base_color}")
        print(f"  Roughness: {material.roughness}")
        print(f"  Metallic: {material.metallic}")
        print(f"  Specular: {material.specular}")
        if material.transparency > 0:
            print(f"  Transparency: {material.transparency}")
    
    print("\n" + "="*50)

def demo_spatial_analysis():
    """Demonstrate spatial analysis capabilities"""
    print("=== SPATIAL ANALYSIS DEMO ===")
    
    analyzer = SpatialAnalyzer()
    elements = analyzer.analyze_rendering()
    
    print(f"Detected {len(elements)} architectural elements:")
    
    element_counts = {}
    total_area = 0
    
    for element in elements:
        element_type = element.element_type
        element_counts[element_type] = element_counts.get(element_type, 0) + 1
        
        # Calculate area
        _, _, w, h = element.bounds
        area = w * h
        total_area += area
        
        print(f"\n{element_type.upper()} #{element_counts[element_type]}:")
        print(f"  Bounds: {element.bounds}")
        print(f"  Area: {area:,} pixels")
        print(f"  Confidence: {element.confidence:.2f}")
        print(f"  Geometry: {element.geometry}")
    
    print(f"\nTOTAL SURFACE AREA: {total_area:,} pixels")
    print(f"ELEMENT SUMMARY: {element_counts}")
    print("\n" + "="*50)

def demo_lighting_conditions():
    """Demonstrate different lighting conditions"""
    print("=== LIGHTING CONDITIONS DEMO ===")
    
    processor = PhotorealisticProcessor()
    elements = SpatialAnalyzer().analyze_rendering()
    
    lighting_conditions = ['golden_hour', 'midday', 'evening']
    
    for condition in lighting_conditions:
        print(f"\n{condition.upper().replace('_', ' ')} LIGHTING:")
        
        if condition in ['golden_hour', 'midday']:
            # Simulate lighting application
            results = processor.enhance_rendering({}, elements, condition)
            lighting = results['lighting_applied']
            
            print(f"  Color Temperature: {lighting.get('color_temperature', 'Variable')}K")
            
            if 'intensity_adjustments' in lighting:
                print("  Intensity Adjustments:")
                for adj, value in lighting['intensity_adjustments'].items():
                    print(f"    {adj.replace('_', ' ').title()}: {value}")
            
            if 'atmospheric_effects' in lighting:
                print("  Atmospheric Effects:")
                for effect, status in lighting['atmospheric_effects'].items():
                    print(f"    {effect.replace('_', ' ').title()}: {status}")
            
            print("  Coastal Effects:")
            coastal = lighting['coastal_effects']
            for effect, value in coastal.items():
                print(f"    {effect.replace('_', ' ').title()}: {value}")
    
    print("\n" + "="*50)

def demo_quality_presets():
    """Demonstrate quality presets"""
    print("=== QUALITY PRESETS DEMO ===")
    
    pipeline = PicachoRenderingPipeline()
    presets = ['draft', 'high', 'ultra']
    
    for preset in presets:
        print(f"\n{preset.upper()} QUALITY:")
        features = pipeline._get_quality_features(preset)
        for feature in features:
            print(f"  ✓ {feature}")
    
    print("\n" + "="*50)

def demo_montecito_features():
    """Demonstrate Montecito-specific features"""
    print("=== MONTECITO FEATURES DEMO ===")
    
    print("COASTAL LIGHTING CHARACTERISTICS:")
    for key, value in config.MONTECITO_LIGHTING.items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    
    print("\nLUXURY MATERIAL SELECTION:")
    print("  Floors: Carrara marble with low roughness (0.1)")
    print("  Walls: Limestone with natural texture (0.6 roughness)")
    print("  Windows: High-performance glass (0.02 roughness)")
    print("  Doors: Premium walnut wood (0.35 roughness)")
    print("  Accents: Contemporary steel elements")
    
    print("\nCONTEMPORARY DESIGN ELEMENTS:")
    print("  ✓ Clean geometric lines")
    print("  ✓ Premium natural materials")
    print("  ✓ Large glass openings")
    print("  ✓ Sophisticated color palette")
    print("  ✓ Professional lighting design")
    
    print("\nPICAHO LANE AESTHETIC:")
    print("  ✓ Santa Barbara coastal environment")
    print("  ✓ Luxury residential standards")
    print("  ✓ Contemporary architectural style")
    print("  ✓ High-end material finishes")
    print("  ✓ Professional visualization quality")
    
    print("\n" + "="*50)

def demo_complete_pipeline():
    """Demonstrate complete pipeline with different configurations"""
    print("=== COMPLETE PIPELINE DEMO ===")
    
    pipeline = PicachoRenderingPipeline()
    
    # Configuration matrix
    configs = [
        ('golden_hour', 'ultra', 'Sunset luxury showcase'),
        ('midday', 'high', 'Bright contemporary presentation'),
        ('evening', 'draft', 'Quick evening preview')
    ]
    
    for time_of_day, quality, description in configs:
        print(f"\nCONFIGURATION: {description}")
        print(f"Time: {time_of_day}, Quality: {quality}")
        print("-" * 40)
        
        result = pipeline.transform_rendering(
            input_description=f"Estate wireframe - {description}",
            time_of_day=time_of_day,
            quality_preset=quality
        )
        
        print(f"✓ Processed {result['elements_detected']} elements")
        print(f"✓ Applied {result['materials_applied']} materials")
        print(f"✓ Resolution: {result['target_resolution'][0]}x{result['target_resolution'][1]}")
        
        # Show specific enhancement details
        enhancements = result['enhancement_results']
        lighting = enhancements['lighting_applied']
        
        if lighting.get('color_temperature'):
            print(f"✓ Color temperature: {lighting['color_temperature']}K")
        
        shadows = enhancements['shadows_added']['elements_with_shadows']
        reflections = enhancements['reflections_added']['reflective_surfaces']
        print(f"✓ Shadows: {len(shadows)} elements")
        print(f"✓ Reflections: {len(reflections)} surfaces")
    
    print("\n" + "="*50)

def main():
    """Run all demonstrations"""
    print("PICACHO LANE LUXURY ESTATE RENDERING PIPELINE")
    print("Complete Feature Demonstration")
    print("=" * 70)
    
    demo_material_library()
    demo_spatial_analysis()
    demo_lighting_conditions()
    demo_quality_presets()
    demo_montecito_features()
    demo_complete_pipeline()
    
    print("\n" + "=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("The system is ready for production use with actual architectural renderings.")
    print("Install OpenCV and imaging dependencies to process real image files.")

if __name__ == "__main__":
    main()