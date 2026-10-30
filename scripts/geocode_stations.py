import csv
from pathlib import Path    
from fuel.geoutils import US_STATES, city_key, read_gazetteer

DATA = Path("data")
SRC = DATA / "fuel-prices-for-be-assessment.csv"
OUT = DATA / "fuel_stations_geocoded.csv"
FIELDS = ["opis_id", "name", "address", "city", "state", "price", "lat", "lon", "geo_source"]


def load_unique_us_stations(stats):
    best = {}
    with SRC.open(encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            stats["rows"] += 1
            state = row["State"].strip().upper()
            if state not in US_STATES:
                stats["outside_usa"] += 1
                continue
            sid = row["OPIS Truckstop ID"].strip()
            price = float(row["Retail Price"])
            if sid not in best or price < best[sid]["price"]:
                best[sid] = {
                    "opis_id": sid,
                    "name": row["Truckstop Name"].strip(),
                    "address": row["Address"].strip(),
                    "city": row["City"].strip(),
                    "state": state,
                    "price": price,
                }
    return list(best.values())

def main():
    stats = {"rows": 0, "outside_usa": 0, "unique_us": 0, "geocoded": 0, "missing": 0}
    stations = load_unique_us_stations(stats)
    stats["unique_us"] = len(stations)

    centroids = {}
    for name, state, lat, lon in read_gazetteer(DATA / "gazetteer_places.txt"):
        centroids.setdefault((city_key(name), state), (lat, lon))

    missing = set()
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for s in stations:
            coords = centroids.get((city_key(s["city"]), s["state"]))
            if coords is None:
                stats["missing"] += 1
                missing.add(f"{s['city']}, {s['state']}")
                continue
            stats["geocoded"] += 1
            writer.writerow({**s, "lat": coords[0], "lon": coords[1], "geo_source": "city"})

    print(stats)
    print("Cities not found:", sorted(missing)[:30])


if __name__ == "__main__":
    main()