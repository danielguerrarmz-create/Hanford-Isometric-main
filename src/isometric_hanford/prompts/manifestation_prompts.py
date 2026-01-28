"""
AI prompt templates for isometric manifestation visualization.

Generates prompts for Flux model to create black & white isometric views
of Hanford reactors with organic-geometric radiation manifestations.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum


class ReactorState(Enum):
    """Reactor operational states"""
    CONSTRUCTION = "construction"
    OPERATIONAL = "operational"
    SHUTDOWN = "shutdown"
    COCOONED = "cocooned"


class ManifestationIntensity(Enum):
    """Manifestation visual intensity levels"""
    NONE = "none"           # 0.0 - 0.1 density
    NASCENT = "nascent"     # 0.1 - 0.3 density
    EMERGING = "emerging"   # 0.3 - 0.5 density
    MATURE = "mature"       # 0.5 - 0.7 density
    INTENSE = "intense"     # 0.7 - 0.9 density
    MAXIMUM = "maximum"     # 0.9 - 1.0 density


@dataclass
class IsometricPromptConfig:
    """Configuration for isometric view generation"""
    reactor_state: ReactorState
    manifestation_intensity: ManifestationIntensity
    density: float
    year: int
    reactor_name: str
    include_context: bool = True  # Include surrounding landscape
    
    @classmethod
    def from_density(cls, density: float, **kwargs) -> 'IsometricPromptConfig':
        """Create config from manifestation density value"""
        if density < 0.1:
            intensity = ManifestationIntensity.NONE
        elif density < 0.3:
            intensity = ManifestationIntensity.NASCENT
        elif density < 0.5:
            intensity = ManifestationIntensity.EMERGING
        elif density < 0.7:
            intensity = ManifestationIntensity.MATURE
        elif density < 0.9:
            intensity = ManifestationIntensity.INTENSE
        else:
            intensity = ManifestationIntensity.MAXIMUM
        
        return cls(manifestation_intensity=intensity, density=density, **kwargs)


# Core style components
STYLE_BASE = """
Isometric technical architectural drawing, black and white only, high contrast,
hand-drawn quality with precise linework, stippling for tonal gradients,
no color, no shading beyond stippling, architectural precision meets speculative visualization,
similar to Lebbeus Woods or Brodsky & Utkin drawings but in isometric perspective
"""

ISOMETRIC_VIEW = """
Strict isometric projection (120° angles), elevated 45-degree viewing angle,
showing structure from southwest perspective, clear depth through line weight variation,
Z-axis vertical elements precisely rendered
"""

# Reactor building descriptions by state
REACTOR_DESCRIPTIONS = {
    ReactorState.CONSTRUCTION: """
    Concrete foundation and steel framework partially complete, construction scaffolding,
    exposed rebar, unfinished walls, industrial construction aesthetic
    """,
    
    ReactorState.OPERATIONAL: """
    Massive rectangular concrete building with cooling water intake/outflow structures,
    smokestacks, industrial piping visible, functional brutalist architecture,
    no weathering or decay, pristine industrial geometry
    """,
    
    ReactorState.SHUTDOWN: """
    Intact concrete structure showing early weathering, some surface staining,
    equipment removed, sealed openings, beginning of abandonment,
    industrial geometry with subtle decay markers
    """,
    
    ReactorState.COCOONED: """
    Original concrete reactor building wrapped in newer corrugated metal shell,
    bright metal cocoon exterior encasing weathered concrete core,
    dual-layer structure visible in section, protective barrier architecture
    """
}

# Manifestation appearance descriptions
MANIFESTATION_DESCRIPTIONS = {
    ManifestationIntensity.NONE: """
    No visible radiation manifestation, clean environment around reactor
    """,
    
    ManifestationIntensity.NASCENT: """
    First hints of manifestation: thin crystalline metal filaments emerging from ground
    around reactor base, sparse distribution, individual shards barely visible,
    appearing like frozen lightning or metallic frost crystals just beginning to form
    """,
    
    ManifestationIntensity.EMERGING: """
    Moderate radiation manifestation: metal shard formations growing from ground in
    concentric rings around reactor, geometric-organic hybrid structures,
    resembling both iron filings attracted to magnet and crystalline biological growth,
    individual shards 1-3 meters tall, spacing visible between formations
    """,
    
    ManifestationIntensity.MATURE: """
    Substantial manifestation field: dense metal shard formations surrounding reactor,
    elongated geometric spikes with organic growth patterns, reaching 5-10 meters height,
    magnetic field-like radial arrangement, overlapping zones creating thicket effect,
    resembles crystallized force field or petrified magnetic flux lines
    """,
    
    ManifestationIntensity.INTENSE: """
    Heavy radiation manifestation: thick forest of metal shards enveloping reactor,
    complex geometric-organic structures 10-20 meters tall, fractal branching patterns,
    dense enough to partially obscure reactor building, aggressive protective barrier,
    appears both crystalline (mineral) and structural (skeletal/organic)
    """,
    
    ManifestationIntensity.MAXIMUM: """
    Maximum manifestation saturation: reactor completely surrounded by dense metal
    shard formations reaching 20+ meters, massive geometric-organic structures
    creating impenetrable barrier, fractal complexity with smaller shards growing
    from larger ones, ultimate expression of radiation made physical,
    appears as if reactor is protected by/imprisoned within crystalline organism
    """
}

# Landscape context elements
HANFORD_LANDSCAPE = """
Arid shrub-steppe landscape, sparse sagebrush vegetation, flat desert terrain,
Columbia River visible in background as dark ribbon, distant Rattlesnake Mountain,
sandy soil with scattered basalt rock, minimal vegetation, high desert atmosphere
"""

NEGATIVE_PROMPT = """
color, full color, painted, watercolor, photographic, photograph, realistic lighting,
shadows, soft focus, blur, curved lines where straight lines should be,
perspective distortion, improper isometric angles, decorative elements,
ornamental details, people, vehicles, pixelation, low resolution
"""


class ManifestationPromptGenerator:
    """Generates AI prompts for isometric manifestation visualization"""
    
    def __init__(self):
        self.style_base = STYLE_BASE
        self.isometric_view = ISOMETRIC_VIEW
        self.negative = NEGATIVE_PROMPT
    
    def generate_prompt(self, config: IsometricPromptConfig) -> Dict[str, str]:
        """
        Generate complete prompt for AI model.
        
        Args:
            config: IsometricPromptConfig with all parameters
            
        Returns:
            Dictionary with 'positive' and 'negative' prompts
        """
        # Build positive prompt components
        components = [
            self.style_base,
            self.isometric_view,
            REACTOR_DESCRIPTIONS[config.reactor_state],
            MANIFESTATION_DESCRIPTIONS[config.manifestation_intensity],
        ]
        
        # Add landscape context if requested
        if config.include_context:
            components.append(HANFORD_LANDSCAPE)
        
        # Add temporal context
        temporal_note = self._get_temporal_context(config.year, config.reactor_state)
        components.append(temporal_note)
        
        # Add technical specifications
        tech_specs = f"""
        Reactor designation: {config.reactor_name}
        Year: {config.year}
        Manifestation density: {config.density:.2f}
        Technical drawing precision, architectural drafting quality
        """
        components.append(tech_specs)
        
        positive_prompt = "\n\n".join(components)
        
        return {
            'positive': positive_prompt,
            'negative': self.negative,
            'config': {
                'reactor_name': config.reactor_name,
                'year': config.year,
                'state': config.reactor_state.value,
                'manifestation': config.manifestation_intensity.value,
                'density': config.density
            }
        }
    
    def _get_temporal_context(self, year: int, state: ReactorState) -> str:
        """Add temporal context to prompt"""
        if year < 1950:
            return "Early atomic age, dawn of nuclear technology, pristine pre-contamination"
        elif year < 1970:
            return "Cold War peak production era, industrial intensity, beginning of accumulation"
        elif year < 1990:
            return "Post-operational transition, early shutdown phase, initial manifestation hints"
        elif year < 2010:
            return "Cocooning era, containment architecture, manifestation growth accelerating"
        elif year < 2050:
            return "Contemporary abandoned industrial site, mature manifestation, decades of accumulation"
        else:
            return "Deep future projection, maximum manifestation, speculative far-future state"
    
    def generate_tile_prompt(
        self,
        tile_x: int,
        tile_y: int,
        tile_z: int,
        year: int,
        reactors_in_tile: List[Dict]
    ) -> Dict[str, str]:
        """
        Generate prompt for a specific tile with multiple reactors.
        
        Args:
            tile_x, tile_y, tile_z: Tile coordinates
            year: Temporal snapshot year
            reactors_in_tile: List of reactor data dicts in this tile
            
        Returns:
            Prompt dictionary
        """
        if not reactors_in_tile:
            # Empty landscape tile
            return self._generate_landscape_only_prompt(year)
        
        # Use dominant reactor for base prompt
        primary_reactor = reactors_in_tile[0]
        
        config = IsometricPromptConfig(
            reactor_state=ReactorState(primary_reactor['state']),
            manifestation_intensity=ManifestationIntensity.NONE,  # Will be set by density
            density=primary_reactor['manifestation_density'],
            year=year,
            reactor_name=primary_reactor['name'],
            include_context=True
        )
        
        config = IsometricPromptConfig.from_density(
            density=primary_reactor['manifestation_density'],
            reactor_state=config.reactor_state,
            year=year,
            reactor_name=primary_reactor['name']
        )
        
        prompt = self.generate_prompt(config)
        
        # Add tile-specific metadata
        prompt['tile_metadata'] = {
            'x': tile_x,
            'y': tile_y,
            'z': tile_z,
            'reactor_count': len(reactors_in_tile)
        }
        
        return prompt
    
    def _generate_landscape_only_prompt(self, year: int) -> Dict[str, str]:
        """Generate prompt for landscape without reactors"""
        positive = f"""
        {self.style_base}
        {self.isometric_view}
        {HANFORD_LANDSCAPE}
        
        Empty Hanford Site landscape, year {year}, no structures,
        natural desert terrain, sparse vegetation, Columbia River visible,
        technical architectural drawing style, black and white only
        """
        
        return {
            'positive': positive,
            'negative': self.negative,
            'config': {'type': 'landscape', 'year': year}
        }


# Example usage and testing
def generate_example_prompts():
    """Generate example prompts for testing"""
    generator = ManifestationPromptGenerator()
    
    examples = [
        # B Reactor through time
        IsometricPromptConfig(
            reactor_state=ReactorState.OPERATIONAL,
            manifestation_intensity=ManifestationIntensity.NONE,
            density=0.0,
            year=1960,
            reactor_name="B Reactor"
        ),
        IsometricPromptConfig.from_density(
            density=0.5,
            reactor_state=ReactorState.SHUTDOWN,
            year=1990,
            reactor_name="B Reactor"
        ),
        IsometricPromptConfig.from_density(
            density=0.85,
            reactor_state=ReactorState.COCOONED,
            year=2026,
            reactor_name="B Reactor"
        ),
    ]
    
    for i, config in enumerate(examples, 1):
        prompt = generator.generate_prompt(config)
        print(f"\n{'='*60}")
        print(f"EXAMPLE {i}: {config.reactor_name} - {config.year}")
        print(f"State: {config.reactor_state.value} | Manifestation: {config.manifestation_intensity.value}")
        print(f"{'='*60}")
        print("\nPOSITIVE PROMPT:")
        print(prompt['positive'][:500] + "...")
        print(f"\nFull prompt length: {len(prompt['positive'])} characters")


if __name__ == "__main__":
    generate_example_prompts()

