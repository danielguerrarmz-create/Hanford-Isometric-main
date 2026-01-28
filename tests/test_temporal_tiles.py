"""Tests for temporal tile generation system"""
import pytest
from pathlib import Path
from src.isometric_hanford.generation.temporal_tiles import (
    TemporalTileGenerator,
    generate_temporal_tiles,
)
from src.isometric_hanford.config.temporal_config import TEMPORAL_SNAPSHOTS


class TestTemporalTileGenerator:
    """Test temporal tile generation"""
    
    def test_generator_initialization(self, tmp_path):
        """Test generator can be initialized"""
        generator = TemporalTileGenerator(output_base_dir=tmp_path)
        assert generator.output_base_dir == tmp_path
        assert generator.max_workers == 4
    
    def test_calculate_manifestation_data(self, tmp_path):
        """Test manifestation data calculation"""
        generator = TemporalTileGenerator(output_base_dir=tmp_path)
        
        # Test for 2026
        data = generator._calculate_manifestation_data(2026)
        
        assert len(data) == 9  # All reactors
        assert 'B' in data
        
        # B Reactor should have high manifestation by 2026
        b_data = data['B']
        assert b_data['density'] > 0.7
        assert b_data['radius_meters'] > 300
        assert not b_data['operational']
        assert b_data['cocooned']
    
    def test_manifestation_data_during_operation(self, tmp_path):
        """Test manifestation is zero during operation"""
        generator = TemporalTileGenerator(output_base_dir=tmp_path)
        
        # Test for 1960 (peak operation)
        data = generator._calculate_manifestation_data(1960)
        
        # All operational reactors should have zero manifestation
        for reactor_data in data.values():
            if reactor_data['operational']:
                assert reactor_data['density'] == 0.0
    
    def test_generate_single_year_stub(self, tmp_path):
        """Test single year generation (stub)"""
        generator = TemporalTileGenerator(output_base_dir=tmp_path)
        
        result = generator.generate_single_year(2026)
        
        assert result['year'] == 2026
        assert result['status'] == 'success'
        assert 'output_dir' in result


class TestConvenienceFunction:
    """Test convenience function"""
    
    def test_generate_temporal_tiles_historical_only(self, tmp_path):
        """Test generating only historical snapshots"""
        results = generate_temporal_tiles(
            output_dir=str(tmp_path),
            historical_only=True,
            max_workers=1
        )
        
        assert results['total_snapshots'] == 6  # Historical snapshots
        assert results['successful'] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

