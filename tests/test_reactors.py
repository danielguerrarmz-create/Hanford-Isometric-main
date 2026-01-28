"""Tests for Hanford reactor data and temporal calculations"""
import pytest
from datetime import datetime
from src.isometric_hanford.data.reactors import (
    Reactor,
    REACTORS,
    get_reactors_by_status,
    calculate_manifestation_density,
    get_manifestation_radius,
)


class TestReactorDataIntegrity:
    """Test reactor data structure and integrity"""
    
    def test_all_reactors_loaded(self):
        """Verify all 9 Hanford reactors are present"""
        assert len(REACTORS) == 9
        expected_designations = {'B', 'C', 'D', 'F', 'H', 'DR', 'KE', 'KW', 'N'}
        assert set(REACTORS.keys()) == expected_designations
    
    def test_reactor_coordinates_valid(self):
        """Verify all coordinates are within Hanford Site bounds"""
        for reactor in REACTORS.values():
            assert 46.56 <= reactor.latitude <= 46.68, f"{reactor.name} latitude out of bounds"
            assert -119.65 <= reactor.longitude <= -119.45, f"{reactor.name} longitude out of bounds"
    
    def test_reactor_dates_logical(self):
        """Verify operational dates are chronologically valid"""
        for reactor in REACTORS.values():
            assert reactor.construction_year <= reactor.operational_start
            assert reactor.operational_start <= reactor.operational_end
            if reactor.cocooned_year:
                assert reactor.cocooned_year >= reactor.operational_end


class TestReactorProperties:
    """Test reactor calculated properties"""
    
    def test_operational_duration(self):
        """Test operational duration calculation"""
        b_reactor = REACTORS['B']
        assert b_reactor.operational_duration == 24  # 1944-1968
    
    def test_years_since_shutdown(self):
        """Test years since shutdown calculation"""
        b_reactor = REACTORS['B']
        current_year = datetime.now().year
        expected = current_year - 1968
        assert b_reactor.years_since_shutdown == expected
    
    def test_manifestation_age(self):
        """Test manifestation age is never negative"""
        for reactor in REACTORS.values():
            assert reactor.manifestation_age >= 0


class TestStatusCategorization:
    """Test reactor status categorization by year"""
    
    def test_1960_status(self):
        """In 1960, most reactors operational"""
        status = get_reactors_by_status(1960)
        assert len(status['operational']) == 8
        assert len(status['shutdown']) == 0
        assert len(status['cocooned']) == 0
    
    def test_1990_status(self):
        """In 1990, all shutdown, some cocooned"""
        status = get_reactors_by_status(1990)
        assert len(status['operational']) == 0
        assert len(status['shutdown']) + len(status['cocooned']) == 9
    
    def test_2026_status(self):
        """In 2026, most cocooned"""
        status = get_reactors_by_status(2026)
        assert len(status['operational']) == 0
        assert len(status['cocooned']) >= 7


class TestManifestationCalculations:
    """Test radiation manifestation density calculations"""
    
    def test_no_manifestation_during_operation(self):
        """Manifestation should be zero during operational period"""
        b_reactor = REACTORS['B']
        density = calculate_manifestation_density(b_reactor, 1960)
        assert density == 0.0
    
    def test_manifestation_grows_over_time(self):
        """Manifestation should increase as time passes"""
        b_reactor = REACTORS['B']
        density_1970 = calculate_manifestation_density(b_reactor, 1970)
        density_2000 = calculate_manifestation_density(b_reactor, 2000)
        density_2026 = calculate_manifestation_density(b_reactor, 2026)
        
        assert 0.0 < density_1970 < density_2000 < density_2026 <= 1.0
    
    def test_manifestation_bounded(self):
        """Manifestation density should never exceed 1.0"""
        b_reactor = REACTORS['B']
        # Test far future
        density_future = calculate_manifestation_density(b_reactor, 3000)
        assert 0.0 <= density_future <= 1.0
    
    def test_older_reactors_stronger_manifestation(self):
        """Older shutdown reactors should have stronger manifestation"""
        b_reactor = REACTORS['B']  # Shutdown 1968
        n_reactor = REACTORS['N']  # Shutdown 1987
        
        density_b = calculate_manifestation_density(b_reactor, 2026)
        density_n = calculate_manifestation_density(n_reactor, 2026)
        
        assert density_b > density_n


class TestManifestationRadius:
    """Test spatial extent of manifestation"""
    
    def test_radius_scales_with_density(self):
        """Radius should increase with manifestation density"""
        b_reactor = REACTORS['B']
        
        radius_1970 = get_manifestation_radius(b_reactor, 1970)
        radius_2026 = get_manifestation_radius(b_reactor, 2026)
        
        assert radius_1970 < radius_2026
    
    def test_radius_maximum_bound(self):
        """Radius should not exceed maximum of 500m"""
        for reactor in REACTORS.values():
            radius = get_manifestation_radius(reactor, 3000)
            assert radius <= 500.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

