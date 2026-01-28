"""Hanford Site reactor data and temporal calculations"""
import math
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List


@dataclass
class Reactor:
    """Represents a Hanford plutonium production reactor"""
    name: str
    designation: str  # B, C, D, F, H, DR, KE, KW, N
    latitude: float
    longitude: float
    construction_year: int
    operational_start: int
    operational_end: int
    cocooned_year: int | None
    plutonium_production_kg: float | None = None

    @property
    def operational_duration(self) -> int:
        """Years reactor was operational"""
        return self.operational_end - self.operational_start

    @property
    def years_since_shutdown(self) -> int:
        """Years since reactor shutdown"""
        return datetime.now().year - self.operational_end

    @property
    def manifestation_age(self) -> int:
        """Years of radiation manifestation (since shutdown)"""
        return max(0, self.years_since_shutdown)


# Reactor instances with accurate Hanford Site coordinates
REACTORS: Dict[str, Reactor] = {
    'B': Reactor(
        name='B Reactor',
        designation='B',
        latitude=46.6284,
        longitude=-119.6442,
        construction_year=1943,
        operational_start=1944,
        operational_end=1968,
        cocooned_year=1995,
    ),
    'C': Reactor(
        name='C Reactor',
        designation='C',
        latitude=46.5844,
        longitude=-119.6183,
        construction_year=1952,
        operational_start=1952,
        operational_end=1969,
        cocooned_year=1998,
    ),
    'D': Reactor(
        name='D Reactor',
        designation='D',
        latitude=46.6625,
        longitude=-119.6056,
        construction_year=1944,
        operational_start=1944,
        operational_end=1967,
        cocooned_year=2004,
    ),
    'F': Reactor(
        name='F Reactor',
        designation='F',
        latitude=46.6453,
        longitude=-119.4628,
        construction_year=1945,
        operational_start=1945,
        operational_end=1965,
        cocooned_year=2003,
    ),
    'H': Reactor(
        name='H Reactor',
        designation='H',
        latitude=46.6015,
        longitude=-119.6325,
        construction_year=1949,
        operational_start=1949,
        operational_end=1965,
        cocooned_year=2005,
    ),
    'DR': Reactor(
        name='DR Reactor',
        designation='DR',
        latitude=46.6625,
        longitude=-119.6300,
        construction_year=1950,
        operational_start=1950,
        operational_end=1964,
        cocooned_year=2002,
    ),
    'KE': Reactor(
        name='K-East Reactor',
        designation='KE',
        latitude=46.5644,
        longitude=-119.5938,
        construction_year=1955,
        operational_start=1955,
        operational_end=1971,
        cocooned_year=None,  # Not yet cocooned
    ),
    'KW': Reactor(
        name='K-West Reactor',
        designation='KW',
        latitude=46.5655,
        longitude=-119.5950,
        construction_year=1955,
        operational_start=1955,
        operational_end=1970,
        cocooned_year=2022,
    ),
    'N': Reactor(
        name='N Reactor',
        designation='N',
        latitude=46.6659,
        longitude=-119.5841,
        construction_year=1963,
        operational_start=1964,
        operational_end=1987,
        cocooned_year=2012,
    ),
}


def get_reactors_by_status(year: int) -> Dict[str, List[Reactor]]:
    """Categorize reactors by operational status in a given year"""
    result = {
        'construction': [],
        'operational': [],
        'shutdown': [],
        'cocooned': []
    }

    for reactor in REACTORS.values():
        if year < reactor.operational_start:
            result['construction'].append(reactor)
        elif reactor.operational_start <= year <= reactor.operational_end:
            result['operational'].append(reactor)
        elif reactor.cocooned_year and year >= reactor.cocooned_year:
            result['cocooned'].append(reactor)
        else:
            result['shutdown'].append(reactor)

    return result


def calculate_manifestation_density(reactor: Reactor, year: int) -> float:
    """
    Calculate radiation manifestation density for visualization.
    Returns value 0.0-1.0 representing shard formation intensity.

    Based on conceptual model where radiation "protects" the reactor
    by manifesting as physical metal shard formations over time.
    """
    if year < reactor.operational_end:
        return 0.0  # No manifestation during operation

    years_since_shutdown = year - reactor.operational_end

    # Exponential growth model inspired by Pu-239 decay characteristics
    # Manifestation becomes visible over decades, approaching asymptote
    growth_rate = 0.03  # Tunable parameter for visualization
    max_density = 1.0

    density = max_density * (1 - math.exp(-growth_rate * years_since_shutdown))

    return min(density, max_density)


def get_manifestation_radius(reactor: Reactor, year: int) -> float:
    """
    Calculate manifestation radius in meters.
    Older reactors have larger manifestation fields.
    """
    density = calculate_manifestation_density(reactor, year)

    # Base radius scales with density
    # Maximum radius of ~500m for fully manifested reactor
    max_radius = 500.0  # meters

    return density * max_radius

