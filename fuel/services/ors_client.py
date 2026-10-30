import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)
ORS_URL = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"

class RoutingError(Exception):
    pass


def get_route(start, finish) -> dict:
    logger.info("ORS directions call %s > %s", start.label, finish.label)
    try:
        resp = requests.post(
            ORS_URL,
            json={"coordinates": [[start.lon, start.lat], [finish.lon, finish.lat]],
                "radiuses": [5000, 5000]},
            headers={"Authorization": settings.ORS_APY_KEY},
            timeout=20
        )
    except requests.RequestException as exc:
        raise RoutingError(f"Routing service unaviable: {exc}") from exc
    if resp.status_code != 200:
        raise RoutingError(f"Routing failed ({resp.status_code}): {resp.text[:200]}")
    feature = resp.json()["features"][0]
    summary = feature["properties"]["summary"]
    return {"geometry": feature["geometry"], "distance_m": summary["distance"], "duration_s": summary["duration"]}