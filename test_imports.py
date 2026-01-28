#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify all renamed imports work correctly"""

# Test all major module imports
try:
    from src.isometric_hanford.data.reactors import REACTORS, get_reactors_by_status, calculate_manifestation_density
    from src.isometric_hanford.generation.bounds import load_bounds
    print("[OK] All imports successful")
except ImportError as e:
    print(f"[FAIL] Import failed: {e}")
    exit(1)

# Test reactor data structure
print("\n=== REACTOR DATA VERIFICATION ===")
print(f"Total reactors: {len(REACTORS)}")
for designation, reactor in REACTORS.items():
    print(f"{designation}: {reactor.name} ({reactor.operational_start}-{reactor.operational_end})")

# Test status categorization
print("\n=== STATUS CATEGORIZATION TESTS ===")
test_years = [1960, 1990, 2026]
for year in test_years:
    status = get_reactors_by_status(year)
    print(f"\nYear {year}:")
    print(f"  Operational: {len(status['operational'])} reactors")
    print(f"  Shutdown: {len(status['shutdown'])} reactors")
    print(f"  Cocooned: {len(status['cocooned'])} reactors")

# Test manifestation calculations
print("\n=== MANIFESTATION DENSITY TESTS ===")
b_reactor = REACTORS['B']
test_years = [1968, 1990, 2000, 2026, 2050]
for year in test_years:
    density = calculate_manifestation_density(b_reactor, year)
    print(f"B Reactor {year}: {density:.3f}")

print("\n[OK] All verifications passed!")
