from math import radians, sin, cos, sqrt, atan2

from epg.dependencies import storage


async def calculate_distance(lat1, lon1, lat2, lon2):
    """
        Вычисляет расстояние по дуге большого круга между двумя точками на поверхности Земли,
        указанными их широтой и долготой в градусах. Кэширует результат в Redis
        для будущих запросов с теми же координатами.

        Args:
            lat1 (float): Широта первой точки в градусах.
            lon1 (float): Долгота первой точки в градусах.
            lat2 (float): Широта второй точки в градусах.
            lon2 (float): Долгота второй точки в градусах.

        Returns:
            float: Расстояние между двумя точками в километрах.
        """

    cache_key = f"distance:{lat1}:{lon1}:{lat2}:{lon2}"
    if await storage():
        cached_distance = await (await storage()).get(cache_key)
        if cached_distance:
            return float(cached_distance)

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = 6371 * c

    if await storage():
        await (await storage()).set(cache_key, distance, ex=3600)

    return distance
