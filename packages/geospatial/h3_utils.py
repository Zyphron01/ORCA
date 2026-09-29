import h3
import math
from typing import Tuple

def is_valid_coordinate(lat: float, lon: float) -> bool:
    """Validate latitude and longitude."""
    if lat is None or lon is None:
        return False
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        return False
    if not (-90 <= lat <= 90):
        return False
    if not (-180 <= lon <= 180):
        return False
    return True

def point_to_h3(lat: float, lon: float, resolution: int = 9) -> str:
    """Convert a latitude and longitude to an H3 cell index."""
    if not is_valid_coordinate(lat, lon):
        raise ValueError(f"Invalid coordinates: lat={lat}, lon={lon}")
    return h3.latlng_to_cell(lat, lon, resolution)

def h3_to_point(h3_cell: str) -> Tuple[float, float]:
    """Convert an H3 cell index back to its representative center coordinates."""
    if not h3.is_valid_cell(h3_cell):
        raise ValueError(f"Invalid H3 cell: {h3_cell}")
    return h3.cell_to_latlng(h3_cell)

def get_h3_neighbors(h3_cell: str, ring_size: int = 1) -> list[str]:
    """Get the neighboring H3 cells within a given ring size (k-ring)."""
    if not h3.is_valid_cell(h3_cell):
        raise ValueError(f"Invalid H3 cell: {h3_cell}")
    return list(h3.grid_disk(h3_cell, ring_size))

def calculate_distance_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the haversine distance between two points in nautical miles."""
    if not is_valid_coordinate(lat1, lon1) or not is_valid_coordinate(lat2, lon2):
        raise ValueError("Invalid coordinates for distance calculation")
    R = 3440.065 # Earth radius in nautical miles
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the initial bearing from point 1 to point 2."""
    if not is_valid_coordinate(lat1, lon1) or not is_valid_coordinate(lat2, lon2):
        raise ValueError("Invalid coordinates for bearing calculation")
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(dlon))
    initial_bearing = math.atan2(x, y)
    initial_bearing = math.degrees(initial_bearing)
    bearing = (initial_bearing + 360) % 360
    return bearing
