"""Reference data from IBGE's public APIs (two requests, cached for a year).

- Localidades: the 645 municipalities of São Paulo with their official IBGE code and name.
- Malhas: the municipality polygons; we keep only each polygon's centroid (lat/lon) for the map and
  the radius filter. One request, no third-party geocoder needed.

    python -m corridas.enrich
"""

from __future__ import annotations

import json
import logging
from itertools import pairwise

import pyarrow as pa
import pyarrow.parquet as pq

from corridas.http import PoliteClient
from corridas.ingest import DATA, load_config

log = logging.getLogger("enrich")
REF = DATA / "reference"


def ring_centroid(ring: list[list[float]]) -> tuple[float, float]:
    """Area-weighted centroid of a closed ring (shoelace formula). Returns (lon, lat)."""
    area = cx = cy = 0.0
    for (x0, y0), (x1, y1) in pairwise(ring):
        cross = x0 * y1 - x1 * y0
        area += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    if area == 0:
        xs, ys = zip(*ring, strict=True)
        return sum(xs) / len(xs), sum(ys) / len(ys)
    return cx / (3 * area), cy / (3 * area)


def centroid(geometry: dict) -> tuple[float, float]:
    """Centroid of a Polygon, or of the largest ring of a MultiPolygon (islands are ignored)."""
    coords = geometry["coordinates"]
    ring = coords[0] if geometry["type"] == "Polygon" else max((p[0] for p in coords), key=len)
    return ring_centroid(ring)


def build(localidades: list[dict], malhas: dict) -> list[dict]:
    centroids = {f["properties"]["codarea"]: centroid(f["geometry"]) for f in malhas["features"]}
    rows = []
    for m in localidades:
        code = str(m["id"])
        lon, lat = centroids.get(code, (None, None))
        rows.append({"ibge_code": code, "name": m["nome"], "uf": "SP", "lat": lat, "lon": lon})
    return rows


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    cfg = load_config()["enrichment"]
    client = PoliteClient(load_config()["user_agent"], DATA / "http_cache", cache_ttl_hours=24 * 365)
    localidades = json.loads(client.get_api(cfg["ibge_municipalities"]).text)
    malhas = json.loads(client.get_api(cfg["ibge_meshes"]).text)
    rows = build(localidades, malhas)
    REF.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(rows), REF / "municipalities_sp.parquet")
    log.info("municipalities: %d (%d with centroid)", len(rows), sum(r["lat"] is not None for r in rows))


if __name__ == "__main__":
    main()
