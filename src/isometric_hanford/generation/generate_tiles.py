"""
Tile generation for Hanford isometric visualization.

Generates isometric tiles using Nano Banana Pro API (Gemini) for each temporal snapshot.
"""
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import json
import math
import os
import tempfile
from dataclasses import dataclass

from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

from isometric_hanford.prompts.manifestation_prompts import (
    ManifestationPromptGenerator,
    IsometricPromptConfig,
    ReactorState,
    ManifestationIntensity,
)
from isometric_hanford.data.reactors import (
    REACTORS,
    get_reactors_by_status,
    calculate_manifestation_density,
    Reactor,
)
from isometric_hanford.config.temporal_config import TEMPORAL_SNAPSHOTS

# Load environment variables
load_dotenv()


@dataclass
class TileGenerationConfig:
    """Configuration for tile generation"""
    output_dir: Path
    zoom_levels: List[int]
    tile_size: int = 256
    bounds: Dict[str, float] = None
    gemini_model: str = "gemini-2.0-flash-exp"  # Nano Banana Pro, fallback to gemini-3-pro-image-preview
    dry_run: bool = False  # If True, only generate prompts, don't call API
    test_mode: bool = False  # If True, only generate first tile per zoom level
    
    def __post_init__(self):
        if self.bounds is None:
            self.bounds = {
                'north': 46.68,
                'south': 46.56,
                'east': -119.45,
                'west': -119.65,
            }


class HanfordTileGenerator:
    """Generates isometric tiles for Hanford site"""
    
    def __init__(self, config: TileGenerationConfig):
        self.config = config
        self.prompt_generator = ManifestationPromptGenerator()
        
    def generate_snapshot(self, year: int) -> None:
        """Generate all tiles for a temporal snapshot"""
        print(f"\nGenerating tiles for year {year}...")
        
        # Get reactor states for this year
        reactor_states = get_reactors_by_status(year)
        
        # Create output directory
        year_dir = self.config.output_dir / str(year)
        year_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate tiles for each zoom level
        for zoom in self.config.zoom_levels:
            self._generate_zoom_level(year, zoom, reactor_states)
    
    def _generate_zoom_level(self, year: int, zoom: int, reactor_states: Dict) -> None:
        """Generate tiles for a specific zoom level"""
        print(f"  Zoom level {zoom}...")
        
        # Calculate tile grid for bounds
        tiles = self._calculate_tile_grid(zoom)
        
        # In test mode, only generate first tile
        if self.config.test_mode:
            tiles = tiles[:1]
            print(f"    [TEST MODE] Generating 1 tile (first tile only)...")
        else:
            print(f"    Generating {len(tiles)} tiles...")
        
        for tile_x, tile_y in tiles:
            self._generate_single_tile(year, zoom, tile_x, tile_y, reactor_states)
    
    def _calculate_tile_grid(self, zoom: int) -> List[Tuple[int, int]]:
        """Calculate which tiles cover the site bounds"""
        bounds = self.config.bounds
        
        # Convert bounds to tile coordinates using Web Mercator projection
        def lat_lng_to_tile(lat: float, lng: float, zoom: int) -> Tuple[int, int]:
            """Convert lat/lng to tile coordinates"""
            n = 2.0 ** zoom
            x = int((lng + 180.0) / 360.0 * n)
            lat_rad = math.radians(lat)
            y = int((1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi) / 2.0 * n)
            return x, y
        
        # Get tile bounds
        x_min, y_max = lat_lng_to_tile(bounds['south'], bounds['west'], zoom)
        x_max, y_min = lat_lng_to_tile(bounds['north'], bounds['east'], zoom)
        
        # Generate tile list
        tiles = []
        for x in range(x_min, x_max + 1):
            for y in range(y_min, y_max + 1):
                tiles.append((x, y))
        
        return tiles
    
    def _generate_single_tile(
        self,
        year: int,
        zoom: int,
        tile_x: int,
        tile_y: int,
        reactor_states: Dict
    ) -> None:
        """Generate a single tile using Flux AI"""
        
        # Find reactors in this tile
        reactors_in_tile = self._find_reactors_in_tile(tile_x, tile_y, zoom)
        
        if not reactors_in_tile:
            # Generate landscape-only tile
            prompt = self.prompt_generator._generate_landscape_only_prompt(year)
        else:
            # Generate tile with reactors
            reactor_data = []
            for reactor_name in reactors_in_tile:
                reactor = REACTORS[reactor_name]
                density = calculate_manifestation_density(reactor, year)
                
                # Determine state
                if year < reactor.operational_start:
                    state = 'construction'
                elif year <= reactor.operational_end:
                    state = 'operational'
                elif reactor.cocooned_year and year >= reactor.cocooned_year:
                    state = 'cocooned'
                else:
                    state = 'shutdown'
                
                reactor_data.append({
                    'name': reactor.name,
                    'state': state,
                    'manifestation_density': density,
                })
            
            prompt = self.prompt_generator.generate_tile_prompt(
                tile_x, tile_y, zoom, year, reactor_data
            )
        
        # Call Nano Banana Pro API to generate image (unless dry run)
        if self.config.dry_run:
            self._save_prompt_for_tile(year, zoom, tile_x, tile_y, prompt)
            print(f"      [DRY RUN] Saved prompt for tile ({tile_x}, {tile_y})")
        else:
            try:
                generated_image = self._call_nano_banana_pro(prompt)
                self._save_generated_tile(year, zoom, tile_x, tile_y, generated_image)
                print(f"      [OK] Generated tile ({tile_x}, {tile_y})")
            except Exception as e:
                print(f"      [ERROR] Failed to generate tile ({tile_x}, {tile_y}): {e}")
                # Save prompt for manual retry
                self._save_prompt_for_tile(year, zoom, tile_x, tile_y, prompt)
    
    def _find_reactors_in_tile(self, tile_x: int, tile_y: int, zoom: int) -> List[str]:
        """Find which reactors are in this tile"""
        reactors_in_tile = []
        
        def lat_lng_to_tile(lat: float, lng: float, zoom: int) -> Tuple[int, int]:
            """Convert lat/lng to tile coordinates"""
            n = 2.0 ** zoom
            x = int((lng + 180.0) / 360.0 * n)
            lat_rad = math.radians(lat)
            y = int((1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi) / 2.0 * n)
            return x, y
        
        for name, reactor in REACTORS.items():
            # Convert reactor lat/lng to tile coords
            r_x, r_y = lat_lng_to_tile(reactor.latitude, reactor.longitude, zoom)
            
            if r_x == tile_x and r_y == tile_y:
                reactors_in_tile.append(name)
        
        return reactors_in_tile
    
    def _call_nano_banana_pro(self, prompt: Dict) -> Image.Image:
        """
        Call Nano Banana Pro API (Gemini) to generate image from prompt.
        
        Args:
            prompt: Dictionary with 'positive' and 'negative' prompt strings
            
        Returns:
            Generated PIL Image
        """
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
        
        client = genai.Client(api_key=api_key)
        
        # Build contents list with prompt text
        contents = [prompt['positive']]
        
        # Add negative prompt if provided
        if prompt.get('negative'):
            contents.append(f"\n\nNegative prompt (avoid these): {prompt['negative']}")
        
        print(f"      [API] Calling Nano Banana Pro API (model: {self.config.gemini_model})...")
        
        # Call Gemini API with configured model
        # Try primary model first, fallback to regular Nano Banana if needed
        try:
            response = client.models.generate_content(
                model=self.config.gemini_model,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"],
                    image_config=types.ImageConfig(
                        aspect_ratio="1:1",  # Square tiles
                    ),
                ),
            )
        except Exception as e:
            # Fallback to regular Nano Banana if Pro not available
            if self.config.gemini_model != "gemini-3-pro-image-preview":
                print(f"      [WARN] {self.config.gemini_model} not available, using regular Nano Banana")
                response = client.models.generate_content(
                    model="gemini-3-pro-image-preview",
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_modalities=["TEXT", "IMAGE"],
                        image_config=types.ImageConfig(
                            aspect_ratio="1:1",
                        ),
                    ),
                )
            else:
                raise  # Re-raise if already using fallback
        
        # Extract the generated image
        for part in response.parts:
            if part.text is not None:
                print(f"      [INFO] Model response: {part.text[:100]}...")
            elif image := part.as_image():
                print(f"      [OK] Received generated image: {image._pil_image.size}")
                return image._pil_image
        
        raise ValueError("No image in Gemini response")
    
    def _save_generated_tile(
        self,
        year: int,
        zoom: int,
        tile_x: int,
        tile_y: int,
        image: Image.Image
    ) -> None:
        """Save generated tile image"""
        tile_dir = self.config.output_dir / str(year) / "tiles" / str(zoom)
        tile_dir.mkdir(parents=True, exist_ok=True)
        
        # Resize to tile size if needed
        if image.size != (self.config.tile_size, self.config.tile_size):
            image = image.resize(
                (self.config.tile_size, self.config.tile_size),
                Image.Resampling.LANCZOS
            )
        
        tile_file = tile_dir / f"{tile_x}_{tile_y}.png"
        image.save(tile_file, "PNG")
    
    def _save_prompt_for_tile(
        self,
        year: int,
        zoom: int,
        tile_x: int,
        tile_y: int,
        prompt: Dict
    ) -> None:
        """Save prompt to file for later generation (fallback)"""
        prompt_dir = self.config.output_dir / str(year) / "prompts" / str(zoom)
        prompt_dir.mkdir(parents=True, exist_ok=True)
        
        prompt_file = prompt_dir / f"{tile_x}_{tile_y}.json"
        
        with open(prompt_file, 'w') as f:
            json.dump(prompt, f, indent=2)


def generate_all_snapshots(dry_run: bool = False, model: str = None, test_mode: bool = False):
    """
    Generate tiles for all temporal snapshots.
    
    Args:
        dry_run: If True, only generate prompts without calling API
        model: Gemini model name (default: gemini-2.0-flash-exp for Nano Banana Pro)
        test_mode: If True, only generate 1 tile per zoom level for testing
    """
    # Check for API key (unless dry run)
    if not dry_run and not os.getenv("GEMINI_API_KEY"):
        print("⚠️  Warning: GEMINI_API_KEY not found in environment")
        print("   Set it with: export GEMINI_API_KEY=your_key")
        print("   Or create a .env file with: GEMINI_API_KEY=your_key")
        print("\n   Switching to dry-run mode (prompts only)...")
        dry_run = True
    
    config = TileGenerationConfig(
        output_dir=Path("output/tiles/hanford"),
        zoom_levels=[13, 14],  # Start with 2 zoom levels
        gemini_model=model or "gemini-2.0-flash-exp",  # Nano Banana Pro
        dry_run=dry_run,
    )
    
    if dry_run:
        print("\n[DRY RUN MODE] Generating prompts only (no API calls)")
    else:
        print(f"\n[GENERATION MODE] Using model: {config.gemini_model}")
    
    if test_mode:
        print("[TEST MODE] Generating only first tile per zoom level")
        config.test_mode = True
    
    generator = HanfordTileGenerator(config)
    
    # In test mode, only generate one snapshot
    snapshots_to_generate = [TEMPORAL_SNAPSHOTS[0]] if test_mode else TEMPORAL_SNAPSHOTS
    
    for snapshot in snapshots_to_generate:
        generator.generate_snapshot(snapshot.year)
    
    print("\n[OK] Tile generation complete!")
    print(f"Output: {config.output_dir}")
    if not dry_run:
        print(f"Tiles: {config.output_dir}/<year>/tiles/<zoom>/")
    print(f"Prompts: {config.output_dir}/<year>/prompts/<zoom>/")


if __name__ == "__main__":
    generate_all_snapshots()

