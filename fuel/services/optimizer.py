from dataclasses import dataclass


@dataclass(frozen=True)
class Station:
    id: int
    name: str
    address: str
    city: str
    state: str
    price: float
    lat: float
    lon: float
    mile: float


@dataclass(frozen=True)
class FuelStop:
    station: Station
    gallons: float
    cost: float


class UnreachableRouteError(Exception):
    pass


def plan_fuel_stops(stations: list[Station], total_miles: float,
                    max_range: float = 500.0, mpg: float = 10.0) -> list[FuelStop]:

    if not stations or stations[0].mile > 1e-6:
        raise ValueError("A station at mile 0 is required.")

    marks = [s.mile for s in stations] + [total_miles]
    for a, b in zip(marks, marks[1:]):
        if b - a > max_range:
            raise UnreachableRouteError(
                f"No fuel station between mile {a:.0f} and mile {b:.0f} "
                f"(more than {max_range:.0f} miles).")

    stops: list[FuelStop] = []
    n, i, fuel = len(stations), 0, 0.0
    while True:
        cur = stations[i]
        reach = cur.mile + max_range

        nxt = None
        for j in range(i + 1, n):
            if stations[j].mile > reach:
                break
            if stations[j].price < cur.price:
                nxt = j
                break

        if nxt is not None:
            target = stations[nxt].mile     
        elif reach >= total_miles:
            target = total_miles           
        else:
            nxt = min((j for j in range(i + 1, n) if stations[j].mile <= reach),
                      key=lambda j: stations[j].price)
            target = reach               

        need = target - cur.mile - fuel
        if need > 1e-9:
            gallons = need / mpg
            stops.append(FuelStop(cur, gallons, gallons * cur.price))
            fuel += need

        if nxt is None:
            return stops
        fuel -= stations[nxt].mile - cur.mile
        i = nxt