import cv2
import numpy as np
import rasterio
from rasterio.transform import from_bounds
from rasterio.features import shapes
import geopandas as gpd
from shapely.geometry import shape
import os

# 1. Define Input/Output configuration
# Note: Using 'ore.jpeg' instead of 'oceanography.jpg' to match provided files and key
INPUT_FILES = {
    'biomes': 'biomes.jpeg',
    'ore': 'ore.jpeg',
    'soil': 'soil.jpeg',
    'topography': 'topography.jpg'
}
KEY_FILE = 'orekey.txt'
OUTPUT_GPKG = 'output_map_stack.gpkg'

# Define global bounding box for Georeferencing (e.g., standard WGS84 global extent)
# [minx, miny, maxx, maxy]
BOUNDS = [-180.0, -90.0, 180.0, 90.0]
CRS = "EPSG:4326"

# Placeholder dictionaries for legend RGB values (Format: BGR for OpenCV)
# In practice, you would extract these using a color picker or K-Means clustering.
LEGEND_COLORS = {
    'biomes': {
        'Jungles': (34, 65, 34), 
        'Deserts': (170, 204, 222), 
        'Grasslands': (140, 180, 150), 
        'Temperate Forests': (70, 110, 80),
        'Tundra': (230, 230, 230),
        'Oceans': (130, 80, 20)
    },
    'soil': {
        'Soil_Type_1': (200, 200, 200),
        'Soil_Type_2': (150, 150, 150),
        # ... Add corresponding colors based on legend
    },
    'topography': {
        'High_Elevation': (150, 200, 150),
        'Sea_Level': (200, 255, 200),
        'Deep_Ocean': (100, 0, 0)
    }
}

def parse_ore_key(filepath):
    """Parses the text file to map ore types to hypothetical RGB colors."""
    ore_dict = {}
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                if line.strip():
                    # Assigning arbitrary BGR colors for demonstration based on descriptions
                    # A robust approach for markers requires template matching or shape detection
                    color_val = (0, 0, 255 - (i * 10)) 
                    ore_dict[line.strip()] = color_val
    return ore_dict

def crop_image(img, crop_ratio=0.15):
    """Crops the right side of the image to remove legends/keys."""
    height, width = img.shape[:2]
    crop_width = int(width * (1.0 - crop_ratio))
    return img[:, :crop_width]

def classify_colors(img, color_dict, tolerance=30):
    """
    Classifies image pixels based on the nearest color in the dictionary.
    Uses Euclidean distance to handle JPEG compression artifacts.
    """
    # Create an empty classification array
    classified = np.zeros(img.shape[:2], dtype=np.uint8)
    
    for class_id, (class_name, color) in enumerate(color_dict.items(), start=1):
        # Calculate Euclidean distance between image pixels and target color
        diff = np.sqrt(np.sum((img.astype(np.float32) - np.array(color)) ** 2, axis=2))
        
        # Apply threshold/tolerance to account for JPEG noise
        mask = diff < tolerance
        
        # Apply morphological filtering to clean up noise/artifacts
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        mask = cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        classified[mask == 1] = class_id
        
    return classified

def vectorize_raster(classified_array, transform, class_dict):
    """Converts a classified raster array into GeoDataFrame polygons."""
    results = []
    
    # Map integer IDs back to class names
    id_to_name = {i: name for i, name in enumerate(class_dict.keys(), start=1)}
    
    # Generate shapes using rasterio
    for geom, value in shapes(classified_array, transform=transform):
        val = int(value)
        if val in id_to_name:
            results.append({
                'geometry': shape(geom),
                'attribute': id_to_name[val]
            })
            
    if results:
        gdf = gpd.GeoDataFrame(results, crs=CRS)
        return gdf
    else:
        return gpd.GeoDataFrame(columns=['geometry', 'attribute'], crs=CRS)

def main():
    # Parse text key for the ore map
    LEGEND_COLORS['ore'] = parse_ore_key(KEY_FILE)
    
    # Dictionary to hold the final GeoDataFrames
    vector_layers = {}

    for name, filename in INPUT_FILES.items():
        if not os.path.exists(filename):
            print(f"File {filename} not found. Skipping...")
            continue
            
        print(f"Processing {name} ({filename})...")
        
        # 1. Image Preprocessing & Cropping
        img = cv2.imread(filename)
        cropped_img = crop_image(img, crop_ratio=0.18) # ~18% crop to remove right legend
        
        # 2. Color Thresholding / Classification
        if name in LEGEND_COLORS:
            classified_raster = classify_colors(cropped_img, LEGEND_COLORS[name])
        else:
            print(f"No color legend defined for {name}. Skipping classification.")
            continue
            
        # 3. Georeferencing / Spatial Alignment
        height, width = classified_raster.shape
        transform = from_bounds(*BOUNDS, width, height)
        
        # 4. Raster-to-Vector Polygonization
        gdf = vectorize_raster(classified_raster, transform, LEGEND_COLORS[name])
        
        # Clean up geometries (fixing potential self-intersections from raster borders)
        gdf['geometry'] = gdf['geometry'].buffer(0)
        vector_layers[name] = gdf
        
    # 5. Export to GeoPackage
    if vector_layers:
        print(f"Exporting layers to {OUTPUT_GPKG}...")
        for layer_name, gdf in vector_layers.items():
            gdf.to_file(OUTPUT_GPKG, layer=layer_name, driver="GPKG")
        print("Export complete.")
    else:
        print("No layers generated.")

if __name__ == "__main__":
    main()