"""Tests for manifestation visualization renderer"""
import pytest
from PIL import Image
from src.isometric_hanford.rendering.manifestation_renderer import (
    ManifestationRenderer,
    ShardPattern,
    ManifestationField,
)


class TestManifestationRenderer:
    """Test manifestation rendering"""
    
    def test_renderer_initialization(self):
        """Test renderer can be initialized"""
        renderer = ManifestationRenderer()
        assert renderer.image_width == 1024
        assert renderer.image_height == 1024
    
    def test_generate_field_zero_density(self):
        """Test field with zero density has no shards"""
        renderer = ManifestationRenderer()
        field = renderer.generate_manifestation_field(
            center_x=512, center_y=512,
            radius=200, density=0.0,
            seed=42
        )
        assert len(field.shards) == 0
    
    def test_generate_field_with_density(self):
        """Test field generation with density"""
        renderer = ManifestationRenderer()
        field = renderer.generate_manifestation_field(
            center_x=512, center_y=512,
            radius=200, density=0.8,
            seed=42
        )
        assert len(field.shards) > 0
        assert field.density == 0.8
        assert field.radius == 200
    
    def test_shard_properties(self):
        """Test generated shards have valid properties"""
        renderer = ManifestationRenderer()
        field = renderer.generate_manifestation_field(
            center_x=512, center_y=512,
            radius=200, density=0.5,
            seed=42
        )
        
        for shard in field.shards:
            assert 0 <= shard.intensity <= 1.0
            assert shard.length > 0
            assert shard.thickness > 0
    
    def test_render_field_to_image(self):
        """Test rendering field to image"""
        renderer = ManifestationRenderer(image_width=512, image_height=512)
        field = renderer.generate_manifestation_field(
            center_x=256, center_y=256,
            radius=150, density=0.6,
            seed=42
        )
        
        img = renderer.render_field_to_image(field)
        
        assert isinstance(img, Image.Image)
        assert img.size == (512, 512)
        assert img.mode == 'RGB'
    
    def test_render_multiple_reactors(self):
        """Test rendering multiple reactor fields"""
        renderer = ManifestationRenderer(image_width=800, image_height=800)
        
        # Create two fields
        field1 = renderer.generate_manifestation_field(
            center_x=300, center_y=400, radius=150, density=0.7, seed=1
        )
        field2 = renderer.generate_manifestation_field(
            center_x=500, center_y=400, radius=120, density=0.5, seed=2
        )
        
        img = renderer.render_multiple_reactors([field1, field2])
        
        assert isinstance(img, Image.Image)
        total_shards = len(field1.shards) + len(field2.shards)
        assert total_shards > 0
    
    def test_reproducible_generation(self):
        """Test generation is reproducible with same seed"""
        renderer = ManifestationRenderer()
        
        field1 = renderer.generate_manifestation_field(
            center_x=512, center_y=512,
            radius=200, density=0.7,
            seed=123
        )
        
        field2 = renderer.generate_manifestation_field(
            center_x=512, center_y=512,
            radius=200, density=0.7,
            seed=123
        )
        
        assert len(field1.shards) == len(field2.shards)
        # First shard should be identical
        assert abs(field1.shards[0].x - field2.shards[0].x) < 0.01
        assert abs(field1.shards[0].y - field2.shards[0].y) < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

