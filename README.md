
# Fuel Route API

A Django REST API that takes a start and a finish location in the USA and returns:

- the driving route,
- the most cost-effective fuel stops along the way,
- the total fuel cost,
- a link to an interactive map of the trip.

---

## Database (ER diagram)

```mermaid
erDiagram
    FUEL_STATION {
        bigint id PK
        varchar opis_id UK "OPIS truck stop ID"
        varchar name
        varchar address
        varchar city
        varchar state "2-letter code"
        decimal price "USD per gallon, lowest if duplicated"
        geography location "Point SRID 4326, GiST index"
        varchar geo_source "street or city"
    }

    CITY {
        bigint id PK
        varchar name "e.g. St. Louis"
        varchar name_key "normalized, e.g. ST LOUIS"
        varchar state "2-letter code"
        geography location "Point SRID 4326, GiST index"
    }
```

The two tables have no foreign key on purpose. They are related spatially, not by IDs:

- city resolves the user's input to a point, using the index.
- fuel_station is queried against the route line with spatial functions, using the GiST index on location.

---

## Architecture


### API flow

```mermaid
flowchart TD
    start(("Start"))
    req["GET /api/v1/route/<br/>start + finish"]
    view["RoutePlanView"]
    valid{"Valid params?<br/>serializer"}
    resolve["Resolve start and finish<br/>city table in PostGIS"]
    found{"Cities found?"}
    planCache{"Plan in Redis?"}
    routeCache{"Route in Redis?"}
    ors["Call OpenRouteService<br/>1 external call"]
    saveRoute["Save route in Redis"]
    corridor["Find stations near the route<br/>PostGIS: ST_DWithin + ST_LineLocatePoint"]
    optimizer["Optimizer<br/>cheapest fuel stops, 500 mi range, 10 MPG"]
    reachable{"Gaps under 500 mi?"}
    build["Build response<br/>summary + fuel_stops + GeoJSON map"]
    savePlan["Save plan in Redis"]
    ok["200 OK JSON"]
    e400["400 Bad Request"]
    e422["422 Unreachable route"]
    e502["502 Routing failed"]
    finish(("End"))

    start --> req --> view --> valid
    valid -- No --> e400
    valid -- Yes --> resolve --> found
    found -- No --> e400
    found -- Yes --> planCache
    planCache -- "Yes (cached: true)" --> ok
    planCache -- No --> routeCache
    routeCache -- Yes --> corridor
    routeCache -- No --> ors
    ors -- Error --> e502
    ors -- OK --> saveRoute --> corridor
    corridor --> optimizer --> reachable
    reachable -- No --> e422
    reachable -- Yes --> build --> savePlan --> ok
    ok --> finish
    e400 --> finish
    e422 --> finish
    e502 --> finish
```

**Errors:** invalid parameter or unknown city → `400` · gap longer than 500 miles → `422` · routing service failure → `502`.

### Components

```mermaid
flowchart LR
    client["Client<br/>Postman / client/index.html"]

    subgraph docker["Docker Compose"]
        subgraph web["web: Django + DRF"]
            view["views.py<br/>RoutePlanView"]
            ser["serializers.py<br/>validate start / finish"]
            planner["services/planner.py<br/>orchestrates + caches"]
            loc["services/locations.py<br/>City, ST or lat,lon → point"]
            ors["services/ors_client.py<br/>routing call"]
            cor["services/corridor.py<br/>spatial query"]
            optim["services/optimizer.py<br/>cheapest fuel stops"]
        end
        db[("PostGIS<br/>city, fuel_station")]
        redis[("Redis<br/>cache")]
    end

    ext["OpenRouteService<br/>(external)"]

    client -->|"GET /api/v1/route/"| view
    view --> ser
    view --> loc
    view --> planner
    loc --> db
    planner --> redis
    planner --> ors
    ors -->|"1 call per new route"| ext
    planner --> cor
    cor --> db
    planner --> optim
```

| Component | Responsibility |
| --- | --- |
| `views.py` | Validates input, maps errors to HTTP codes, returns JSON |
| `locations.py` | Turns `"Denver, CO"` or `"39.74,-104.99"` into coordinates |
| `planner.py` | Orchestrates the request and caches routes and plans in Redis |
| `ors_client.py` | The only external call: route line, distance and duration |
| `corridor.py` | One PostGIS query: stations within 10 miles of the route, with mile markers |
| `optimizer.py` | Pure Python greedy algorithm: where to buy fuel and how much |

### Offline data preparation (runs once)

```mermaid
flowchart LR
    csv["fuel-prices CSV<br/>prices, no coordinates"] --> script["scripts/geocode_stations.py<br/>US only, lowest price per station"]
    gaz["Census Gazetteer<br/>city centers"] --> script
    script --> out["data/fuel_stations_geocoded.csv"]
    out -->|"load_stations"| db[("PostGIS")]
    gaz -->|"load_cities"| db
```

The fuel CSV has prices but no coordinates, so stations are placed at their city center once, offline. At request time the API only reads PostGIS, which keeps it fast and limits external calls to one routing call per new route.

