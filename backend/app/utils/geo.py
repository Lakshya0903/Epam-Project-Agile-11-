"""
Geographic Distance & Location Normalization Utilities
Primary Maintainer: Hemant Yadav (Backend Developer 3)
"""

import math
import hashlib
from typing import Optional


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on the Earth (km)."""
    r = 6371.0  # Earth radius in kilometers
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def estimate_distance_km(
    lat1: Optional[float], lon1: Optional[float],
    lat2: Optional[float], lon2: Optional[float],
    fallback_seed_a: str = "", fallback_seed_b: str = "",
) -> float:
    """
    Use real coordinates when both origin and destination have them; otherwise derive
    a stable pseudo-distance from the locality names so development proceeds smoothly
    without requiring a paid geocoding API key.
    """
    if None not in (lat1, lon1, lat2, lon2):
        return round(haversine_km(lat1, lon1, lat2, lon2), 2)

    combined = f"{fallback_seed_a}|{fallback_seed_b}".lower().strip()
    digest = hashlib.md5(combined.encode("utf-8")).hexdigest()
    # Map hash into plausible local delivery range: 2.0 to 40.0 km
    pseudo_km = 2.0 + (int(digest[:6], 16) % 3800) / 100.0
    return round(pseudo_km, 2)


def area_key(location_text: str) -> str:
    """
    Normalize free-text address into coarse area key for grouping orders into
    regional delivery batches (e.g. 'Andheri West, Mumbai' -> 'andheri west').
    """
    return location_text.strip().lower().split(",")[0].strip()
