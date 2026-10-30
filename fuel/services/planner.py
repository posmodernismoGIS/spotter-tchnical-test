import json 
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry
from django.core.cache import cache
from . import corridor, ors_client
from .locations import Location
from .optimizer import plan_fuel_stops

METERS_PER_MILE = 1609.344

def _key(prefix: str, a:Location, b:Location) -> str:
    return f"{prefix}:{a.lat:.5f},{a.lon:.5f}:{b.lat:.5f},{b.lon:.5f}"

def _route(start: Location, finish: Location) -> dict:
    key = _key("route", start, finish)
    route = cache.get(key)
    if route is None:
        route = ors_client.get_route(start, finish)
        cache.set(key, route)
    return route

def plan_trip(start: Location, finish: Location) -> dict:
    key = _key("plan:v1", start, finish)
    if (cached := cache.get(key)) is not None:
        return {**cached, "cached": True}

    route = _route(start, finish)
    total_miles = route["distance_m"] / METERS_PER_MILE
    origin = corridor.nearest_station(start.lat, start.lon)
    along = corridor.stations_along_route(route["geometry"], total_miles, settings.CORRIDOR_MILES)
    stations = [origin] + [s for s in along if s.id != origin.id]
    stops = plan_fuel_stops(stations, total_miles, settings.VEHICLE_RANGE_MILES, settings.VEHICLE_MPG)

    simplified = GEOSGeometry(json.dumps(route["geometry"])).simplify(0.001, preserve_topology=True)
    result = {
        "start": {"label": start.label, "lat": start.lat, "lon": start.lon},
        "finish": {"label": finish.label, "lat": finish.lat, "lon": finish.lon},
        "summary": {
            "total_distance_miles": round(total_miles, 1),
            "total_duration_hours": round(route["duration_s"] / 3600, 1),
            "total_gallons": round(sum(s.gallons for s in stops), 2),
            "total_fuel_cost_usd": round(sum(s.cost for s in stops), 2),
            "fuel_stops_count": len(stops),
        },
        "fuel_stops": [
            {"order": n, "station_id": s.station.id, "name": s.station.name,
             "address": s.station.address, "city": s.station.city, "state": s.station.state,
             "price_per_gallon": round(s.station.price, 3), "mile_marker": round(s.station.mile, 1),
             "gallons": round(s.gallons, 2), "cost": round(s.cost, 2),
             "location": {"lat": s.station.lat, "lon": s.station.lon}}
            for n, s in enumerate(stops, start=1)
        ],
        "route": {"type": "Feature", "geometry": json.loads(simplified.json), "properties": {}},
    }
    cache.set(key, result)
    return {**result, "cached": False}