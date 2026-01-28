"""Temporal snapshot configuration for Hanford Site visualization"""
from dataclasses import dataclass
from typing import List, Dict, Tuple
from datetime import datetime


@dataclass
class TemporalSnapshot:
    """Represents a specific point in time for tile generation"""
    year: int
    label: str
    description: str
    significance: str
    tile_directory: str
    
    @property
    def is_future(self) -> bool:
        """Check if this snapshot is in the future"""
        return self.year > datetime.now().year
    
    @property
    def tile_path_template(self) -> str:
        """Generate tile path template for this snapshot"""
        return f"tiles/{self.year}/{{z}}/{{x}}/{{y}}.png"


# Key temporal snapshots spanning 1943-2100
TEMPORAL_SNAPSHOTS: List[TemporalSnapshot] = [
    TemporalSnapshot(
        year=1943,
        label="Origin",
        description="Manhattan Project begins, B Reactor construction",
        significance="Birth of the nuclear age at Hanford",
        tile_directory="tiles/1943"
    ),
    TemporalSnapshot(
        year=1945,
        label="Trinity",
        description="First plutonium production, Nagasaki bomb material",
        significance="Hanford plutonium used in Fat Man bomb",
        tile_directory="tiles/1945"
    ),
    TemporalSnapshot(
        year=1964,
        label="Peak Production",
        description="All 9 reactors operational simultaneously",
        significance="Maximum plutonium production capacity",
        tile_directory="tiles/1964"
    ),
    TemporalSnapshot(
        year=1987,
        label="Last Shutdown",
        description="N Reactor closes, ending plutonium production",
        significance="End of 44-year production era",
        tile_directory="tiles/1987"
    ),
    TemporalSnapshot(
        year=2000,
        label="Millennium Threshold",
        description="Early cocooning era, first manifestations visible",
        significance="Transition to containment phase",
        tile_directory="tiles/2000"
    ),
    TemporalSnapshot(
        year=2026,
        label="Present Day",
        description="8 reactors cocooned, manifestations mature",
        significance="Current state of the site",
        tile_directory="tiles/2026"
    ),
    TemporalSnapshot(
        year=2070,
        label="Cocoon Expiration",
        description="75-year cocoon lifespan reaching end",
        significance="Projected cocoon failure timeline",
        tile_directory="tiles/2070"
    ),
    TemporalSnapshot(
        year=2100,
        label="Deep Future",
        description="Maximum manifestation density achieved",
        significance="Speculative far-future state",
        tile_directory="tiles/2100"
    ),
]


# Snapshot lookup dictionary
SNAPSHOTS_BY_YEAR: Dict[int, TemporalSnapshot] = {
    snapshot.year: snapshot for snapshot in TEMPORAL_SNAPSHOTS
}


def get_snapshot_for_year(year: int) -> TemporalSnapshot:
    """Get the snapshot for a specific year"""
    if year in SNAPSHOTS_BY_YEAR:
        return SNAPSHOTS_BY_YEAR[year]
    
    # If exact year not found, return closest snapshot
    closest_year = min(SNAPSHOTS_BY_YEAR.keys(), key=lambda y: abs(y - year))
    return SNAPSHOTS_BY_YEAR[closest_year]


def get_interpolation_snapshots(year: int) -> Tuple[TemporalSnapshot, TemporalSnapshot, float]:
    """
    Get the two snapshots to interpolate between for a given year.
    Returns (lower_snapshot, upper_snapshot, interpolation_factor)
    """
    snapshot_years = sorted(SNAPSHOTS_BY_YEAR.keys())
    
    # If exact match, return that snapshot for both
    if year in SNAPSHOTS_BY_YEAR:
        return SNAPSHOTS_BY_YEAR[year], SNAPSHOTS_BY_YEAR[year], 0.0
    
    # Find bounding snapshots
    lower_year = max([y for y in snapshot_years if y <= year], default=snapshot_years[0])
    upper_year = min([y for y in snapshot_years if y > year], default=snapshot_years[-1])
    
    if lower_year == upper_year:
        return SNAPSHOTS_BY_YEAR[lower_year], SNAPSHOTS_BY_YEAR[lower_year], 0.0
    
    # Calculate interpolation factor (0.0 to 1.0)
    interpolation_factor = (year - lower_year) / (upper_year - lower_year)
    
    return (
        SNAPSHOTS_BY_YEAR[lower_year],
        SNAPSHOTS_BY_YEAR[upper_year],
        interpolation_factor
    )


def get_timeline_range() -> Tuple[int, int]:
    """Get the full temporal range covered by snapshots"""
    years = [snapshot.year for snapshot in TEMPORAL_SNAPSHOTS]
    return min(years), max(years)


def get_historical_snapshots() -> List[TemporalSnapshot]:
    """Get only historical (past) snapshots"""
    current_year = datetime.now().year
    return [s for s in TEMPORAL_SNAPSHOTS if s.year <= current_year]


def get_speculative_snapshots() -> List[TemporalSnapshot]:
    """Get only speculative (future) snapshots"""
    current_year = datetime.now().year
    return [s for s in TEMPORAL_SNAPSHOTS if s.year > current_year]


# Tile generation configuration
TILE_CONFIG = {
    'min_zoom': 10,    # Hanford site scale
    'max_zoom': 16,    # Detailed reactor view
    'tile_size': 256,  # Standard tile size in pixels
    'format': 'png',
    'quality': 95,
}


# Site boundaries for visualization
SITE_BOUNDS = {
    'north': 46.68,
    'south': 46.56,
    'east': -119.45,
    'west': -119.65,
}

# Visual style parameters for temporal rendering
VISUAL_STYLE = {
    'background_color': (240, 240, 235),  # Off-white desert
    'river_color': (70, 130, 180),        # Columbia River blue
    'reactor_color': (60, 60, 60),        # Dark gray concrete
    'manifestation_color': (20, 20, 20),  # Near-black metal shards
    'line_weight': 1.5,
    'stipple_density': 0.3,
}

