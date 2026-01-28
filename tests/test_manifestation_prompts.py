"""Tests for manifestation prompt generation"""
import pytest
from src.isometric_hanford.prompts.manifestation_prompts import (
    ManifestationPromptGenerator,
    IsometricPromptConfig,
    ReactorState,
    ManifestationIntensity,
)


class TestPromptGeneration:
    """Test AI prompt generation"""
    
    def test_generator_initialization(self):
        """Test generator can be initialized"""
        generator = ManifestationPromptGenerator()
        assert generator.style_base is not None
        assert generator.negative is not None
    
    def test_basic_prompt_generation(self):
        """Test basic prompt generation"""
        generator = ManifestationPromptGenerator()
        
        config = IsometricPromptConfig(
            reactor_state=ReactorState.COCOONED,
            manifestation_intensity=ManifestationIntensity.MATURE,
            density=0.6,
            year=2026,
            reactor_name="B Reactor"
        )
        
        prompt = generator.generate_prompt(config)
        
        assert 'positive' in prompt
        assert 'negative' in prompt
        assert 'config' in prompt
        assert len(prompt['positive']) > 100
        assert 'isometric' in prompt['positive'].lower()
        assert 'black and white' in prompt['positive'].lower()
    
    def test_config_from_density(self):
        """Test creating config from density value"""
        config = IsometricPromptConfig.from_density(
            density=0.75,
            reactor_state=ReactorState.COCOONED,
            year=2026,
            reactor_name="Test"
        )
        
        assert config.manifestation_intensity == ManifestationIntensity.INTENSE
        assert config.density == 0.75
    
    def test_density_intensity_mapping(self):
        """Test density maps to correct intensity levels"""
        test_cases = [
            (0.05, ManifestationIntensity.NONE),
            (0.15, ManifestationIntensity.NASCENT),
            (0.35, ManifestationIntensity.EMERGING),
            (0.55, ManifestationIntensity.MATURE),
            (0.75, ManifestationIntensity.INTENSE),
            (0.95, ManifestationIntensity.MAXIMUM),
        ]
        
        for density, expected_intensity in test_cases:
            config = IsometricPromptConfig.from_density(
                density=density,
                reactor_state=ReactorState.COCOONED,
                year=2026,
                reactor_name="Test"
            )
            assert config.manifestation_intensity == expected_intensity
    
    def test_temporal_progression(self):
        """Test prompts change appropriately over time"""
        generator = ManifestationPromptGenerator()
        
        years = [1960, 1990, 2026]
        prompts = []
        
        for year in years:
            config = IsometricPromptConfig.from_density(
                density=0.5,
                reactor_state=ReactorState.SHUTDOWN,
                year=year,
                reactor_name="B Reactor"
            )
            prompt = generator.generate_prompt(config)
            prompts.append(prompt['positive'])
        
        # Each prompt should be unique
        assert len(set(prompts)) == 3
    
    def test_negative_prompt_excludes_unwanted(self):
        """Test negative prompt excludes color and other unwanted elements"""
        generator = ManifestationPromptGenerator()
        negative = generator.negative.lower()
        
        assert 'color' in negative
        assert 'photograph' in negative or 'photographic' in negative
        assert 'blur' in negative
    
    def test_tile_prompt_generation(self):
        """Test tile-specific prompt generation"""
        generator = ManifestationPromptGenerator()
        
        reactor_data = [{
            'name': 'B Reactor',
            'state': 'cocooned',
            'manifestation_density': 0.8
        }]
        
        prompt = generator.generate_tile_prompt(
            tile_x=100,
            tile_y=200,
            tile_z=14,
            year=2026,
            reactors_in_tile=reactor_data
        )
        
        assert 'tile_metadata' in prompt
        assert prompt['tile_metadata']['x'] == 100
        assert prompt['tile_metadata']['reactor_count'] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

