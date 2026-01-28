"""Tests for temporal snapshot configuration system"""
import pytest
from datetime import datetime
from src.isometric_hanford.config.temporal_config import (
    TemporalSnapshot,
    TEMPORAL_SNAPSHOTS,
    SNAPSHOTS_BY_YEAR,
    get_snapshot_for_year,
    get_interpolation_snapshots,
    get_timeline_range,
    get_historical_snapshots,
    get_speculative_snapshots,
    TILE_CONFIG,
    VISUAL_STYLE,
)


class TestSnapshotDataIntegrity:
    """Test snapshot data structure and integrity"""
    
    def test_all_snapshots_loaded(self):
        """Verify all expected snapshots are present"""
        assert len(TEMPORAL_SNAPSHOTS) == 8
        expected_years = {1943, 1945, 1964, 1987, 2000, 2026, 2070, 2100}
        actual_years = {snapshot.year for snapshot in TEMPORAL_SNAPSHOTS}
        assert actual_years == expected_years
    
    def test_snapshots_chronologically_ordered(self):
        """Verify snapshots are in chronological order"""
        years = [snapshot.year for snapshot in TEMPORAL_SNAPSHOTS]
        assert years == sorted(years), "Snapshots should be in chronological order"
    
    def test_snapshot_fields_complete(self):
        """Verify all snapshots have required fields"""
        for snapshot in TEMPORAL_SNAPSHOTS:
            assert snapshot.year > 0
            assert snapshot.label
            assert snapshot.description
            assert snapshot.significance
            assert snapshot.tile_directory
            assert snapshot.tile_directory.startswith("tiles/")
    
    def test_snapshot_properties(self):
        """Test snapshot computed properties"""
        current_year = datetime.now().year
        
        # Test is_future property
        historical_snapshot = TEMPORAL_SNAPSHOTS[0]  # 1943
        assert historical_snapshot.is_future == False
        
        future_snapshot = TEMPORAL_SNAPSHOTS[-1]  # 2100
        assert future_snapshot.is_future == True
        
        # Test tile_path_template
        snapshot = TEMPORAL_SNAPSHOTS[0]
        template = snapshot.tile_path_template
        assert "{z}" in template
        assert "{x}" in template
        assert "{y}" in template
        assert f"tiles/{snapshot.year}" in template
    
    def test_snapshots_by_year_dict(self):
        """Verify lookup dictionary is correctly populated"""
        assert len(SNAPSHOTS_BY_YEAR) == len(TEMPORAL_SNAPSHOTS)
        for snapshot in TEMPORAL_SNAPSHOTS:
            assert snapshot.year in SNAPSHOTS_BY_YEAR
            assert SNAPSHOTS_BY_YEAR[snapshot.year] == snapshot


class TestYearLookupFunctions:
    """Test year lookup and retrieval functions"""
    
    def test_get_snapshot_for_exact_year(self):
        """Test lookup for exact snapshot years"""
        snapshot_1945 = get_snapshot_for_year(1945)
        assert snapshot_1945.year == 1945
        assert snapshot_1945.label == "Trinity"
        
        snapshot_2026 = get_snapshot_for_year(2026)
        assert snapshot_2026.year == 2026
        assert snapshot_2026.label == "Present Day"
    
    def test_get_snapshot_for_intermediate_year(self):
        """Test lookup returns closest snapshot for intermediate years"""
        # 1975 is between 1964 and 1987
        snapshot = get_snapshot_for_year(1975)
        # Should return closest (either 1964 or 1987)
        assert snapshot.year in [1964, 1987]
        
        # 1950 is between 1945 and 1964
        snapshot = get_snapshot_for_year(1950)
        assert snapshot.year in [1945, 1964]
    
    def test_get_snapshot_for_edge_years(self):
        """Test lookup for years at timeline boundaries"""
        # Before first snapshot
        snapshot = get_snapshot_for_year(1900)
        assert snapshot.year == 1943  # Should return earliest
        
        # After last snapshot
        snapshot = get_snapshot_for_year(2200)
        assert snapshot.year == 2100  # Should return latest
    
    def test_get_historical_snapshots(self):
        """Test filtering for historical snapshots"""
        historical = get_historical_snapshots()
        current_year = datetime.now().year
        
        assert len(historical) > 0
        for snapshot in historical:
            assert snapshot.year <= current_year
            assert snapshot.is_future == False
    
    def test_get_speculative_snapshots(self):
        """Test filtering for speculative snapshots"""
        speculative = get_speculative_snapshots()
        current_year = datetime.now().year
        
        assert len(speculative) > 0
        for snapshot in speculative:
            assert snapshot.year > current_year
            assert snapshot.is_future == True


class TestInterpolationCalculations:
    """Test interpolation calculation functions"""
    
    def test_interpolation_for_exact_snapshot_year(self):
        """Test interpolation for exact snapshot years"""
        lower, upper, factor = get_interpolation_snapshots(1945)
        assert lower.year == 1945
        assert upper.year == 1945
        assert factor == 0.0
    
    def test_interpolation_for_intermediate_year(self):
        """Test interpolation between two snapshots"""
        # 1975 is between 1964 and 1987
        lower, upper, factor = get_interpolation_snapshots(1975)
        assert lower.year == 1964
        assert upper.year == 1987
        assert 0.0 < factor < 1.0
        
        # Factor should be approximately (1975-1964)/(1987-1964) = 11/23 ≈ 0.478
        expected_factor = (1975 - 1964) / (1987 - 1964)
        assert abs(factor - expected_factor) < 0.001
    
    def test_interpolation_for_year_before_first_snapshot(self):
        """Test interpolation for years before first snapshot"""
        lower, upper, factor = get_interpolation_snapshots(1900)
        # Should return first snapshot for both
        assert lower.year == 1943
        assert upper.year == 1943
        assert factor == 0.0
    
    def test_interpolation_for_year_after_last_snapshot(self):
        """Test interpolation for years after last snapshot"""
        lower, upper, factor = get_interpolation_snapshots(2200)
        # Should return last snapshot for both
        assert lower.year == 2100
        assert upper.year == 2100
        assert factor == 0.0
    
    def test_interpolation_factor_bounds(self):
        """Test interpolation factor is always between 0 and 1"""
        test_years = [1900, 1950, 1975, 2000, 2050, 2200]
        for year in test_years:
            lower, upper, factor = get_interpolation_snapshots(year)
            assert 0.0 <= factor <= 1.0
    
    def test_interpolation_midpoint(self):
        """Test interpolation at midpoint between snapshots"""
        # 1975.5 is midpoint between 1964 and 1987
        lower, upper, factor = get_interpolation_snapshots(1975)
        # Factor should be close to 0.5
        expected_factor = (1975 - 1964) / (1987 - 1964)
        assert abs(factor - expected_factor) < 0.01


class TestTimelineRangeValidation:
    """Test timeline range and boundary functions"""
    
    def test_get_timeline_range(self):
        """Test timeline range calculation"""
        min_year, max_year = get_timeline_range()
        assert min_year == 1943
        assert max_year == 2100
        assert min_year < max_year
    
    def test_timeline_range_consistency(self):
        """Test timeline range matches snapshot years"""
        min_year, max_year = get_timeline_range()
        snapshot_years = [s.year for s in TEMPORAL_SNAPSHOTS]
        assert min_year == min(snapshot_years)
        assert max_year == max(snapshot_years)
    
    def test_historical_vs_speculative_split(self):
        """Test that historical + speculative = total snapshots"""
        historical = get_historical_snapshots()
        speculative = get_speculative_snapshots()
        
        # Should cover all snapshots
        assert len(historical) + len(speculative) == len(TEMPORAL_SNAPSHOTS)
        
        # Should not overlap
        historical_years = {s.year for s in historical}
        speculative_years = {s.year for s in speculative}
        assert historical_years.isdisjoint(speculative_years)


class TestConfigurationConstants:
    """Test configuration constants"""
    
    def test_tile_config_structure(self):
        """Test tile configuration structure"""
        assert 'min_zoom' in TILE_CONFIG
        assert 'max_zoom' in TILE_CONFIG
        assert 'tile_size' in TILE_CONFIG
        assert 'format' in TILE_CONFIG
        assert 'quality' in TILE_CONFIG
        
        assert TILE_CONFIG['min_zoom'] < TILE_CONFIG['max_zoom']
        assert TILE_CONFIG['tile_size'] > 0
        assert TILE_CONFIG['format'] == 'png'
        assert 0 < TILE_CONFIG['quality'] <= 100
    
    def test_visual_style_structure(self):
        """Test visual style configuration structure"""
        assert 'background_color' in VISUAL_STYLE
        assert 'river_color' in VISUAL_STYLE
        assert 'reactor_color' in VISUAL_STYLE
        assert 'manifestation_color' in VISUAL_STYLE
        
        # Colors should be RGB tuples
        for color_key in ['background_color', 'river_color', 'reactor_color', 'manifestation_color']:
            color = VISUAL_STYLE[color_key]
            assert isinstance(color, tuple)
            assert len(color) == 3
            assert all(0 <= c <= 255 for c in color)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

