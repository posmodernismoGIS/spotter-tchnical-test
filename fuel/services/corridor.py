import json
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.db import connection
from fuel.models import FuelStation
from .optimizer import Station

METERS_PER_MILE = 1609.344

CORRIDOR_SQL = """
WITH r AS (
    SELECT ST_Simplify(ST_SetSRID(ST_GeomFromGeoJSON(%(geojson)s), 4326), 0.005)::geography AS g
)
SELECT s.id, s.name, s.address, s.city, s.state, s.price::float,
       ST_Y(s.location::geometry) AS lat,
       ST_X(s.location::geometry) AS lon,
       ST_LineLocatePoint(r.g, s.location) AS fraction
FROM fuel_station s, r
WHERE ST_DWithin(s.location, r.g, %(radius_m)s)
ORDER BY fraction;
"""

def stations_along_route(geometry: dict, total_miles: float, radius_miles: float) -> list[Station]:
    with connection.cursor() as cur:
        cur.execute(CORRIDOR_SQL, {"geojson": json.dumps(geometry),
                                   "radius_m": radius_miles * METERS_PER_MILE})
        rows = cur.fetchall()
    return [Station(id=r[0], name=r[1], address=r[2], city=r[3], state=r[4], price=r[5],
                    lat=r[6], lon=r[7], mile=r[8] * total_miles) for r in rows]


def nearest_station(lat: float, lon: float) -> Station:
    """Closest station to the origin: the first purchase, because the tank starts empty."""
    s = (FuelStation.objects
         .annotate(d=Distance("location", Point(lon, lat, srid=4326)))
         .order_by("d").first())
    return Station(id=s.id, name=s.name, address=s.address, city=s.city, state=s.state,
                   price=float(s.price), lat=s.location.y, lon=s.location.x, mile=0.0)