"""
Configuration settings for Picacho Lane photorealistic rendering system
"""

# Resolution settings for 4K DCI
DCI_4K_WIDTH = 4096
DCI_4K_HEIGHT = 2160
TARGET_RESOLUTION = (DCI_4K_WIDTH, DCI_4K_HEIGHT)

# Montecito/Santa Barbara lighting characteristics
MONTECITO_LIGHTING = {
    'golden_hour_temp': 3200,  # Kelvin
    'midday_temp': 5600,
    'ambient_intensity': 0.3,
    'directional_intensity': 0.8,
    'coastal_haze_factor': 0.15
}

# Luxury contemporary estate material properties
LUXURY_MATERIALS = {
    'marble': {
        'roughness': 0.1,
        'metallic': 0.0,
        'specular': 0.9,
        'base_color': (0.95, 0.95, 0.92)
    },
    'hardwood': {
        'roughness': 0.3,
        'metallic': 0.0,
        'specular': 0.4,
        'base_color': (0.6, 0.4, 0.2)
    },
    'glass': {
        'roughness': 0.02,
        'metallic': 0.0,
        'specular': 1.0,
        'transparency': 0.95,
        'base_color': (0.98, 0.98, 0.98)
    },
    'steel': {
        'roughness': 0.2,
        'metallic': 1.0,
        'specular': 0.9,
        'base_color': (0.7, 0.7, 0.7)
    }
}

# Spatial detection thresholds
DETECTION_THRESHOLDS = {
    'floor_plane_tolerance': 0.05,
    'wall_angle_tolerance': 5.0,  # degrees
    'window_aspect_ratio_min': 0.3,
    'door_aspect_ratio_range': (1.8, 2.5)
}