"""Generate placeholder tiles for Hanford visualization"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import math

# Configuration
TILE_SIZE = 512
GRID_WIDTH = 20
GRID_HEIGHT = 20
MAX_ZOOM = 4
IMAGE_WIDTH = GRID_WIDTH * TILE_SIZE
IMAGE_HEIGHT = GRID_HEIGHT * TILE_SIZE

# Hanford site information - optimized for reactor coverage + Columbia River
HANFORD_INFO = {
    "name": "Hanford Nuclear Site - Reactor Corridor",
    "bounds": {
        "north": 46.68,   # Just north of N Reactor
        "south": 46.56,   # Just south of KE/KW Reactors
        "east": -119.45,  # East to include F Reactor
        "west": -119.65   # West to include Columbia River
    },
    "center": {
        "lat": 46.625,    # Approximately D/DR Reactor area
        "lng": -119.55
    }
}

# Temporal snapshots
YEARS = [1943, 1945, 1964, 1987, 2000, 2026, 2070, 2100, "default"]
BASE_DIR = Path("src/app/public/dzi/hanford")

# Reactor locations (for future use)
REACTORS = [
    {"name": "B", "lat": 46.6284, "lng": -119.6442},
    {"name": "C", "lat": 46.5844, "lng": -119.6183},
    {"name": "D", "lat": 46.6625, "lng": -119.6056},
    {"name": "F", "lat": 46.6453, "lng": -119.4628},
    {"name": "H", "lat": 46.6015, "lng": -119.6325},
    {"name": "DR", "lat": 46.6625, "lng": -119.6300},
    {"name": "KE", "lat": 46.5644, "lng": -119.5938},
    {"name": "KW", "lat": 46.5655, "lng": -119.5950},
    {"name": "N", "lat": 46.6659, "lng": -119.5841},
]


def tile_to_lat_lng(x, y, total_tiles_x, total_tiles_y, bounds):
    """Convert tile coordinates to lat/lng based on bounds"""
    # Normalize tile coordinates (0.0 to 1.0) based on actual grid size
    norm_x = (x + 0.5) / total_tiles_x
    norm_y = (y + 0.5) / total_tiles_y
    
    # Map to geographic bounds
    # Note: Y is inverted (tile Y=0 is at top, lat increases north)
    lat = bounds["south"] + (bounds["north"] - bounds["south"]) * (1 - norm_y)
    lng = bounds["west"] + (bounds["east"] - bounds["west"]) * norm_x
    
    return lat, lng


def is_near_river(lat, lng):
    """Check if coordinate is near Columbia River"""
    # Columbia River flows roughly north-south through Hanford site
    # River path approximation: flows from north (~46.68) to south (~46.56)
    # Longitude varies from ~-119.62 (west) to ~-119.55 (east) as it curves
    # Approximate river path as a series of segments
    river_segments = [
        (46.68, -119.62),  # North end, more west
        (46.66, -119.60),  # Curving east
        (46.64, -119.58),
        (46.62, -119.57),
        (46.60, -119.56),
        (46.58, -119.55),  # South end, more east
        (46.56, -119.54),
    ]
    
    # Check distance to any river segment
    min_dist = float('inf')
    for river_lat, river_lng in river_segments:
        # Use proper distance calculation (degrees)
        dist = math.sqrt((lat - river_lat)**2 + (lng - river_lng)**2)
        min_dist = min(min_dist, dist)
    
    # Within ~0.015 degrees (~1 mile) of river - wider threshold for visibility
    return min_dist < 0.015


def create_placeholder_tile(year, level, x, y, total_tiles_x, total_tiles_y):
    """Create a single placeholder tile with river visualization"""
    # Get tile center coordinates using actual grid dimensions
    center_lat, center_lng = tile_to_lat_lng(x, y, total_tiles_x, total_tiles_y, HANFORD_INFO["bounds"])
    
    # Determine if this tile shows river
    near_river = is_near_river(center_lat, center_lng)
    
    # Background color
    if near_river:
        bg_color = (100, 140, 170)  # River blue
    else:
        bg_color = (240, 235, 220)  # Desert tan
    
    img = Image.new("RGB", (TILE_SIZE, TILE_SIZE), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Add subtle grid
    grid_color = (220, 215, 200) if not near_river else (80, 120, 150)
    grid_spacing = 32
    for i in range(0, TILE_SIZE + grid_spacing, grid_spacing):
        draw.line([(i, 0), (i, TILE_SIZE)], fill=grid_color, width=1)
        draw.line([(0, i), (TILE_SIZE, i)], fill=grid_color, width=1)
    
    # Check if any reactors are in this tile
    reactors_in_tile = []
    bounds = HANFORD_INFO["bounds"]
    for reactor in REACTORS:
        # Convert reactor lat/lng to tile coordinates using actual grid dimensions
        norm_y = 1 - (reactor["lat"] - bounds["south"]) / (bounds["north"] - bounds["south"])
        norm_x = (reactor["lng"] - bounds["west"]) / (bounds["east"] - bounds["west"])
        r_x = int(norm_x * total_tiles_x)
        r_y = int(norm_y * total_tiles_y)
        
        if r_x == x and r_y == y:
            reactors_in_tile.append(reactor["name"])
    
    # Add year label
    try:
        # Try to use a system font
        font = ImageFont.truetype("arial.ttf", 16)
        small_font = ImageFont.truetype("arial.ttf", 12)
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except:
            font = ImageFont.load_default()
            small_font = font
    
    text_color = (255, 255, 255) if near_river else (100, 100, 100)
    
    year_str = str(year)
    draw.text((10, 10), year_str, fill=text_color, font=font)
    
    # Label reactors if present
    if reactors_in_tile:
        reactor_text = ", ".join(reactors_in_tile)
        draw.text((10, 35), f"R {reactor_text}", fill=(200, 50, 50), font=small_font)
    
    if near_river:
        draw.text((10, TILE_SIZE - 25), "Columbia River", fill=(255, 255, 255), font=small_font)
    
    # Add a subtle border
    border_color = (180, 175, 160) if not near_river else (60, 100, 130)
    draw.rectangle([(0, 0), (TILE_SIZE - 1, TILE_SIZE - 1)], outline=border_color, width=2)
    
    return img


def generate_tiles_for_year(year, max_level=MAX_ZOOM):
    """Generate placeholder tiles for a specific year"""
    year_dir = BASE_DIR / str(year)
    tiles_dir = year_dir / "tiles_files"
    
    total_tiles_generated = 0
    
    for level in range(max_level + 1):
        # Calculate grid dimensions at this level
        # Level 0: 1x1 tile (full image)
        # Level 1: 2x2 tiles
        # Level 2: 4x4 tiles
        # Level 3: 8x8 tiles
        # Level 4: 16x16 tiles (or 20x20 for our grid)
        
        # For DZI format, level 0 is the most zoomed out
        # Each level doubles the number of tiles
        tiles_x = min(GRID_WIDTH, 2 ** level)
        tiles_y = min(GRID_HEIGHT, 2 ** level)
        
        # But we want to fill the full grid at max level
        if level == max_level:
            tiles_x = GRID_WIDTH
            tiles_y = GRID_HEIGHT
        
        level_dir = tiles_dir / str(level)
        level_dir.mkdir(parents=True, exist_ok=True)
        
        for x in range(tiles_x):
            for y in range(tiles_y):
                tile = create_placeholder_tile(year, level, x, y, tiles_x, tiles_y)
                tile_path = level_dir / f"{x}_{y}.webp"
                tile.save(tile_path, "WEBP", quality=85)
                total_tiles_generated += 1
        
        print(f"  Level {level}: Generated {tiles_x}x{tiles_y} = {tiles_x * tiles_y} tiles")
    
    return total_tiles_generated


def main():
    """Generate placeholder tiles for all temporal snapshots"""
    print("=" * 60)
    print("Generating placeholder tiles for Hanford visualization")
    print("=" * 60)
    print(f"Output directory: {BASE_DIR}")
    print(f"Tile size: {TILE_SIZE}x{TILE_SIZE}px")
    print(f"Grid size: {GRID_WIDTH}x{GRID_HEIGHT} tiles")
    print(f"Image size: {IMAGE_WIDTH}x{IMAGE_HEIGHT}px")
    print(f"Max zoom level: {MAX_ZOOM}")
    print()
    
    total_all_tiles = 0
    
    for year in YEARS:
        print(f"Generating tiles for {year}...")
        tiles_count = generate_tiles_for_year(year)
        total_all_tiles += tiles_count
        print(f"  Total tiles for {year}: {tiles_count}")
        print()
    
    print("=" * 60)
    print(f"Placeholder tile generation complete!")
    print(f"Total tiles generated: {total_all_tiles}")
    print()
    print("These placeholder tiles will be replaced with AI-generated tiles")
    print("when the actual generation pipeline is run.")
    print("=" * 60)


if __name__ == "__main__":
    main()

