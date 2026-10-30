import re
from dataclasses import dataclass

from fuel.geoutils import city_key
from fuel.models import City

LATLON_RE = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$")


class LocationError(ValueError):
    pass


@dataclass(frozen=True)
class Location:
    label: str
    lat: float
    lon: float


def resolve(text: str) -> Location:
    match = LATLON_RE.match(text)
    if match:
        lat, lon = float(match[1]), float(match[2])
        if not (24.0 <= lat <= 49.5 and -125.0 <= lon <= -66.5):
            raise LocationError(f"'{text}' is outside the contiguous USA.")
        return Location(text.strip(), lat, lon)
    if "," not in text:
        raise LocationError("Use 'City, ST' (e.g. 'Denver, CO') or 'lat,lon'.")
    city, state = (part.strip() for part in text.rsplit(",", 1))
    found = City.objects.filter(name_key=city_key(city), state=state.upper()).first()
    if found is None:
        raise LocationError(f"City not found in the USA: '{text}'.")
    return Location(f"{found.name}, {found.state}", found.location.y, found.location.x)