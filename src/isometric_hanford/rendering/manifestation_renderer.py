"""
Manifestation visualization renderer for Hanford reactors.

Renders radiation as physical metal shard formations using:
- Magnetic field-like directional patterns
- Density-based stippling for atmospheric diffusion
- Technical drawing aesthetic (black & white, high contrast)
"""
import numpy as np
import math
from dataclasses import dataclass
from typing import Tuple, List, Optional
from PIL import Image, ImageDraw
import logging

logger = logging.getLogger(__name__)


@dataclass
class ShardPattern:
    """Represents a single metal shard in the manifestation field"""
    x: float
    y: float
    length: float
    angle: float  # radians
    thickness: float
    intensity: float  # 0.0-1.0


@dataclass
class ManifestationField:
    """Complete manifestation field for a reactor"""
    center_x: float
    center_y: float
    radius: float
    density: float
    shards: List[ShardPattern]


class ManifestationRenderer:
    """Renders radiation manifestation as metal shard formations"""
    
    def __init__(
        self,
        image_width: int = 1024,
        image_height: int = 1024,
        background_color: Tuple[int, int, int] = (240, 240, 235),
        shard_color: Tuple[int, int, int] = (20, 20, 20),
    ):
        """
        Initialize manifestation renderer.
        
        Args:
            image_width: Output image width
            image_height: Output image height
            background_color: RGB background (off-white desert)
            shard_color: RGB shard color (near-black metal)
        """
        self.image_width = image_width
        self.image_height = image_height
        self.background_color = background_color
        self.shard_color = shard_color
        
    def generate_manifestation_field(
        self,
        center_x: float,
        center_y: float,
        radius: float,
        density: float,
        seed: Optional[int] = None
    ) -> ManifestationField:
        """
        Generate a manifestation field with metal shard patterns.
        
        Args:
            center_x: Field center X coordinate (pixels)
            center_y: Field center Y coordinate (pixels)
            radius: Field radius (pixels)
            density: Manifestation density (0.0-1.0)
            seed: Random seed for reproducible generation
            
        Returns:
            ManifestationField with shard patterns
        """
        if seed is not None:
            np.random.seed(seed)
        
        shards = []
        
        if density <= 0.0 or radius <= 0.0:
            return ManifestationField(center_x, center_y, radius, density, shards)
        
        # Number of shards scales with density and area
        base_shard_count = int(density * radius * 2)  # Tunable
        shard_count = max(10, min(base_shard_count, 500))  # Clamp for performance
        
        logger.debug(f"Generating {shard_count} shards for density={density:.3f}, radius={radius:.1f}")
        
        # Generate shards in concentric rings (magnetic field pattern)
        ring_count = int(density * 8) + 3  # More rings = denser manifestation
        
        for ring_idx in range(ring_count):
            ring_progress = ring_idx / ring_count  # 0.0 to 1.0
            ring_radius = radius * ring_progress
            
            # Shards per ring decreases toward center
            shards_in_ring = int(shard_count * (1 - ring_progress * 0.5) / ring_count)
            
            for _ in range(shards_in_ring):
                shard = self._generate_single_shard(
                    center_x, center_y,
                    ring_radius, radius,
                    density, ring_progress
                )
                shards.append(shard)
        
        return ManifestationField(center_x, center_y, radius, density, shards)
    
    def _generate_single_shard(
        self,
        center_x: float,
        center_y: float,
        ring_radius: float,
        max_radius: float,
        density: float,
        ring_progress: float
    ) -> ShardPattern:
        """
        Generate a single metal shard with magnetic field orientation.
        
        Args:
            center_x, center_y: Field center
            ring_radius: Radius of current ring
            max_radius: Maximum field radius
            density: Overall manifestation density
            ring_progress: Position in field (0.0=center, 1.0=edge)
            
        Returns:
            Single ShardPattern
        """
        # Position on ring with some randomness
        angle = np.random.uniform(0, 2 * math.pi)
        radius_variation = np.random.uniform(0.8, 1.2)
        
        x = center_x + ring_radius * radius_variation * math.cos(angle)
        y = center_y + ring_radius * radius_variation * math.sin(angle)
        
        # Shard points toward/away from center (magnetic field lines)
        # Outer shards point outward, inner shards more chaotic
        base_angle = angle + math.pi  # Point away from center
        angle_chaos = (1 - ring_progress) * np.random.uniform(-0.5, 0.5)
        shard_angle = base_angle + angle_chaos
        
        # Shard length varies with density and position
        base_length = 15 + (density * 40)  # Longer shards = higher density
        length_variation = np.random.uniform(0.6, 1.4)
        # Outer shards longer than inner
        position_factor = 0.5 + ring_progress * 0.5
        length = base_length * length_variation * position_factor
        
        # Thickness varies with density
        thickness = 1.0 + (density * 2.5)
        thickness *= np.random.uniform(0.8, 1.2)
        
        # Intensity varies (for stippling effect)
        intensity = density * np.random.uniform(0.7, 1.0)
        # Outer shards slightly fainter
        intensity *= (1.0 - ring_progress * 0.3)
        
        return ShardPattern(
            x=x, y=y,
            length=length,
            angle=shard_angle,
            thickness=thickness,
            intensity=intensity
        )
    
    def render_field_to_image(
        self,
        field: ManifestationField,
        show_debug: bool = False
    ) -> Image.Image:
        """
        Render a manifestation field to an image.
        
        Args:
            field: ManifestationField to render
            show_debug: Draw debug circles/centers
            
        Returns:
            PIL Image with rendered manifestation
        """
        # Create image
        img = Image.new('RGB', (self.image_width, self.image_height), self.background_color)
        draw = ImageDraw.Draw(img)
        
        if show_debug:
            # Draw field boundary
            draw.ellipse(
                [
                    field.center_x - field.radius,
                    field.center_y - field.radius,
                    field.center_x + field.radius,
                    field.center_y + field.radius
                ],
                outline=(200, 200, 200),
                width=1
            )
            # Draw center point
            draw.ellipse(
                [
                    field.center_x - 5,
                    field.center_y - 5,
                    field.center_x + 5,
                    field.center_y + 5
                ],
                fill=(255, 0, 0)
            )
        
        # Render shards (back to front for proper layering)
        for shard in field.shards:
            self._draw_shard(draw, shard)
        
        logger.info(f"Rendered {len(field.shards)} shards")
        
        return img
    
    def _draw_shard(self, draw: ImageDraw.ImageDraw, shard: ShardPattern):
        """
        Draw a single metal shard.
        
        Args:
            draw: PIL ImageDraw object
            shard: ShardPattern to draw
        """
        # Calculate shard endpoints
        dx = shard.length * math.cos(shard.angle)
        dy = shard.length * math.sin(shard.angle)
        
        x1, y1 = shard.x, shard.y
        x2, y2 = shard.x + dx, shard.y + dy
        
        # Calculate color based on intensity
        intensity = int(shard.intensity * 255)
        color = (
            255 - intensity,  # More intense = darker
            255 - intensity,
            255 - intensity
        )
        
        # Draw shard as line
        draw.line(
            [(x1, y1), (x2, y2)],
            fill=color,
            width=int(shard.thickness)
        )
    
    def render_multiple_reactors(
        self,
        reactor_fields: List[ManifestationField],
        show_debug: bool = False
    ) -> Image.Image:
        """
        Render multiple reactor manifestation fields on one image.
        
        Args:
            reactor_fields: List of ManifestationFields
            show_debug: Show debug visualization
            
        Returns:
            Composite image with all manifestations
        """
        img = Image.new('RGB', (self.image_width, self.image_height), self.background_color)
        draw = ImageDraw.Draw(img)
        
        # Collect all shards from all fields
        all_shards = []
        for field in reactor_fields:
            all_shards.extend(field.shards)
        
        # Sort by distance from center (render far to near for proper layering)
        # This creates depth effect
        all_shards.sort(key=lambda s: math.sqrt(
            (s.x - self.image_width/2)**2 + (s.y - self.image_height/2)**2
        ), reverse=True)
        
        # Render all shards
        for shard in all_shards:
            self._draw_shard(draw, shard)
        
        # Debug visualization
        if show_debug:
            for field in reactor_fields:
                draw.ellipse(
                    [
                        field.center_x - field.radius,
                        field.center_y - field.radius,
                        field.center_x + field.radius,
                        field.center_y + field.radius
                    ],
                    outline=(200, 0, 0),
                    width=2
                )
        
        logger.info(f"Rendered {len(all_shards)} total shards from {len(reactor_fields)} reactors")
        
        return img


def create_test_manifestation(
    output_path: str = "test_manifestation.png",
    density: float = 0.8,
    show_debug: bool = False
):
    """
    Create a test manifestation rendering.
    
    Args:
        output_path: Where to save test image
        density: Manifestation density to test
        show_debug: Show debug visualization
    """
    renderer = ManifestationRenderer(image_width=800, image_height=800)
    
    # Generate test field at center
    field = renderer.generate_manifestation_field(
        center_x=400,
        center_y=400,
        radius=300,
        density=density,
        seed=42  # Reproducible
    )
    
    # Render to image
    img = renderer.render_field_to_image(field, show_debug=show_debug)
    img.save(output_path)
    
    print(f"Test manifestation saved to {output_path}")
    print(f"Density: {density:.2f}")
    print(f"Shards generated: {len(field.shards)}")


# CLI interface for testing
if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) > 1:
        density = float(sys.argv[1])
    else:
        density = 0.8
    
    print(f"\nGenerating test manifestation with density={density}...")
    create_test_manifestation(
        output_path=f"manifestation_test_{density:.2f}.png",
        density=density,
        show_debug=True
    )
    print("\nTry different densities:")
    print("  python -m src.isometric_hanford.rendering.manifestation_renderer 0.2")
    print("  python -m src.isometric_hanford.rendering.manifestation_renderer 0.5")
    print("  python -m src.isometric_hanford.rendering.manifestation_renderer 0.9")

