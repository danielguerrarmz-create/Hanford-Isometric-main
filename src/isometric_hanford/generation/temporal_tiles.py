"""Temporal tile generation system for Hanford Site visualization"""
import logging
from pathlib import Path
from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.isometric_hanford.config.temporal_config import (
    TEMPORAL_SNAPSHOTS,
    TemporalSnapshot,
    TILE_CONFIG,
    get_historical_snapshots,
    get_speculative_snapshots,
)
from src.isometric_hanford.data.reactors import (
    REACTORS,
    get_reactors_by_status,
    calculate_manifestation_density,
    get_manifestation_radius,
)

logger = logging.getLogger(__name__)


class TemporalTileGenerator:
    """Generates tile sets for different temporal snapshots"""
    
    def __init__(self, output_base_dir: Path, max_workers: int = 4):
        """
        Initialize temporal tile generator.
        
        Args:
            output_base_dir: Base directory for all tile output (e.g., 'tiles/')
            max_workers: Maximum parallel tile generation workers
        """
        self.output_base_dir = Path(output_base_dir)
        self.max_workers = max_workers
        self.tile_config = TILE_CONFIG
        
    def generate_all_snapshots(
        self,
        snapshots: Optional[List[TemporalSnapshot]] = None,
        skip_existing: bool = True
    ) -> dict:
        """
        Generate tiles for all temporal snapshots.
        
        Args:
            snapshots: List of snapshots to generate (defaults to all)
            skip_existing: Skip generation if tiles already exist
            
        Returns:
            Dictionary with generation statistics
        """
        if snapshots is None:
            snapshots = TEMPORAL_SNAPSHOTS
        
        logger.info(f"Starting generation for {len(snapshots)} temporal snapshots")
        
        results = {
            'total_snapshots': len(snapshots),
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'details': []
        }
        
        for snapshot in snapshots:
            logger.info(f"Generating snapshot: {snapshot.year} - {snapshot.label}")
            
            try:
                result = self._generate_snapshot(snapshot, skip_existing)
                results['details'].append(result)
                
                if result['status'] == 'success':
                    results['successful'] += 1
                elif result['status'] == 'skipped':
                    results['skipped'] += 1
                else:
                    results['failed'] += 1
                    
            except Exception as e:
                logger.error(f"Failed to generate snapshot {snapshot.year}: {e}")
                results['failed'] += 1
                results['details'].append({
                    'year': snapshot.year,
                    'status': 'error',
                    'error': str(e)
                })
        
        return results
    
    def _generate_snapshot(
        self,
        snapshot: TemporalSnapshot,
        skip_existing: bool
    ) -> dict:
        """
        Generate tiles for a single temporal snapshot.
        
        Args:
            snapshot: Temporal snapshot to generate
            skip_existing: Skip if tiles already exist
            
        Returns:
            Generation result dictionary
        """
        output_dir = self.output_base_dir / str(snapshot.year)
        
        # Check if tiles already exist
        if skip_existing and output_dir.exists():
            tile_count = len(list(output_dir.rglob("*.png")))
            if tile_count > 0:
                logger.info(f"Skipping {snapshot.year}: {tile_count} tiles already exist")
                return {
                    'year': snapshot.year,
                    'status': 'skipped',
                    'existing_tiles': tile_count
                }
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get reactor states for this year
        reactor_states = get_reactors_by_status(snapshot.year)
        
        # Calculate manifestation data for this year
        manifestation_data = self._calculate_manifestation_data(snapshot.year)
        
        # Generate tiles (this will call the actual tile generation)
        tile_count = self._generate_tiles_for_year(
            year=snapshot.year,
            output_dir=output_dir,
            reactor_states=reactor_states,
            manifestation_data=manifestation_data
        )
        
        logger.info(f"Generated {tile_count} tiles for {snapshot.year}")
        
        return {
            'year': snapshot.year,
            'status': 'success',
            'tiles_generated': tile_count,
            'output_dir': str(output_dir)
        }
    
    def _calculate_manifestation_data(self, year: int) -> dict:
        """
        Calculate manifestation density and radius for all reactors at given year.
        
        Args:
            year: Year to calculate for
            
        Returns:
            Dictionary mapping reactor designation to manifestation data
        """
        manifestation_data = {}
        
        for designation, reactor in REACTORS.items():
            density = calculate_manifestation_density(reactor, year)
            radius = get_manifestation_radius(reactor, year)
            
            manifestation_data[designation] = {
                'density': density,
                'radius_meters': radius,
                'operational': (reactor.operational_start <= year <= reactor.operational_end),
                'cocooned': (reactor.cocooned_year and year >= reactor.cocooned_year),
            }
        
        return manifestation_data
    
    def _generate_tiles_for_year(
        self,
        year: int,
        output_dir: Path,
        reactor_states: dict,
        manifestation_data: dict
    ) -> int:
        """
        Generate actual tile images for a specific year.
        
        This is a placeholder that will integrate with the existing tile generation system.
        
        Args:
            year: Year being generated
            output_dir: Output directory for tiles
            reactor_states: Reactor operational states
            manifestation_data: Manifestation visualization data
            
        Returns:
            Number of tiles generated
        """
        # TODO: Integrate with existing tile generation system
        # This will be implemented in next step when we understand the existing system
        
        logger.warning(f"Tile generation stub called for {year}")
        logger.info(f"  Output: {output_dir}")
        logger.info(f"  Operational reactors: {len(reactor_states['operational'])}")
        logger.info(f"  Cocooned reactors: {len(reactor_states['cocooned'])}")
        logger.info(f"  Manifestation data: {len(manifestation_data)} reactors")
        
        # Return 0 for now - will be replaced with actual generation
        return 0
    
    def generate_single_year(self, year: int) -> dict:
        """
        Generate tiles for a single year (useful for testing).
        
        Args:
            year: Year to generate
            
        Returns:
            Generation result
        """
        from src.isometric_hanford.config.temporal_config import get_snapshot_for_year
        
        snapshot = get_snapshot_for_year(year)
        return self._generate_snapshot(snapshot, skip_existing=False)


def generate_temporal_tiles(
    output_dir: str = "tiles",
    snapshots: Optional[List[int]] = None,
    historical_only: bool = False,
    max_workers: int = 4
) -> dict:
    """
    Convenience function to generate temporal tiles.
    
    Args:
        output_dir: Base output directory
        snapshots: List of years to generate (None = all)
        historical_only: Only generate historical snapshots
        max_workers: Maximum parallel workers
        
    Returns:
        Generation statistics
    """
    generator = TemporalTileGenerator(
        output_base_dir=Path(output_dir),
        max_workers=max_workers
    )
    
    # Determine which snapshots to generate
    if snapshots is not None:
        from src.isometric_hanford.config.temporal_config import SNAPSHOTS_BY_YEAR
        snapshot_list = [SNAPSHOTS_BY_YEAR[year] for year in snapshots if year in SNAPSHOTS_BY_YEAR]
    elif historical_only:
        snapshot_list = get_historical_snapshots()
    else:
        snapshot_list = TEMPORAL_SNAPSHOTS
    
    return generator.generate_all_snapshots(snapshot_list)


# CLI interface for testing
if __name__ == "__main__":
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) > 1:
        year = int(sys.argv[1])
        print(f"\nGenerating tiles for {year}...")
        generator = TemporalTileGenerator(output_base_dir=Path("tiles"))
        result = generator.generate_single_year(year)
        print(f"\nResult: {result}")
    else:
        print("Usage: python -m src.isometric_hanford.generation.temporal_tiles <year>")
        print("Example: python -m src.isometric_hanford.generation.temporal_tiles 2026")

