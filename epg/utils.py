from math import radians, sin, cos, sqrt, atan2

from epg.dependencies import storage


async def calculate_distance(lat1, lon1, lat2, lon2):
    cache_key = f"distance:{lat1}:{lon1}:{lat2}:{lon2}"
    cached_distance = await storage().get(cache_key)

    if cached_distance:
        return float(cached_distance)

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = 6371 * c

    await storage().set(cache_key, distance, ex=3600)

    return distance
