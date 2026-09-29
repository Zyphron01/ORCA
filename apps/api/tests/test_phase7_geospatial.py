import pytest
from packages.geospatial.h3_utils import (
    is_valid_coordinate,
    point_to_h3,
    h3_to_point,
    get_h3_neighbors,
    calculate_distance_nm,
    calculate_bearing
)
from packages.marine_data.providers.demo import DemoGeospatialProvider

def test_is_valid_coordinate():
    assert is_valid_coordinate(10.0, 80.0) is True
    assert is_valid_coordinate(91.0, 80.0) is False
    assert is_valid_coordinate(10.0, 181.0) is False
    assert is_valid_coordinate(-91.0, 80.0) is False

def test_point_to_h3_and_back():
    lat = 10.0
    lon = 80.0
    cell = point_to_h3(lat, lon, resolution=9)
    assert cell is not None
    assert type(cell) == str
    
    back_lat, back_lon = h3_to_point(cell)
    # The center of the hex should be close to the original point
    assert abs(back_lat - lat) < 0.1
    assert abs(back_lon - lon) < 0.1

def test_get_h3_neighbors():
    lat = 10.0
    lon = 80.0
    cell = point_to_h3(lat, lon, resolution=9)
    neighbors = get_h3_neighbors(cell, ring_size=1)
    # A single ring size=1 usually returns 7 cells (center + 6 neighbors)
    assert len(neighbors) == 7
    assert cell in neighbors

def test_distance_and_bearing():
    lat1, lon1 = 10.0, 80.0
    lat2, lon2 = 11.0, 80.0
    
    # 1 degree of latitude is roughly 60 nautical miles
    dist = calculate_distance_nm(lat1, lon1, lat2, lon2)
    assert 59.0 < dist < 61.0
    
    bearing = calculate_bearing(lat1, lon1, lat2, lon2)
    assert abs(bearing - 0.0) < 0.1 # North

@pytest.mark.asyncio
async def test_demo_geospatial_provider():
    provider = DemoGeospatialProvider()
    
    # Test nearby zones
    zones = await provider.get_nearby_zones(10.0, 80.0, radius_nm=500.0)
    assert type(zones) == list
    
    # Test spatial context
    context = await provider.get_spatial_context(10.0, 80.0)
    assert "h3_cell" in context
    assert "nearby_zones" in context
    assert "in_zones" in context
