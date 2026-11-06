import json
from pathlib import Path

from pyproj import Geod
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "national"
DATA_DIR.mkdir(parents=True, exist_ok=True)
GEOD = Geod(ellps="WGS84")


def validate_boundary(geometry):
    if geometry.get("type") == "Feature":
        geometry = geometry.get("geometry") or {}
    if geometry.get("type") not in ("Polygon", "MultiPolygon"):
        raise ValueError("Provide a GeoJSON Polygon or MultiPolygon in WGS84 longitude, latitude.")
    land = shape(geometry)
    if land.is_empty or not land.is_valid:
        raise ValueError("The boundary is empty or crosses itself. Draw a valid land boundary.")
    if sum(len(r.coords) for p in ([land] if land.geom_type == "Polygon" else land.geoms) for r in [p.exterior, *p.interiors]) > 5000:
        raise ValueError("Use a boundary with at most 5,000 vertices.")
    west, south, east, north = land.bounds
    if not (16 <= west < east <= 33.1 and -35 <= south < north <= -22):
        raise ValueError("Select land within mainland South Africa.")
    country_file = DATA_DIR / "south_africa.geojson"
    if not country_file.exists():
        raise ValueError("South Africa boundary is missing. Run python backend/bootstrap_data.py first.")
    country = json.loads(country_file.read_text(encoding="utf-8"))
    country_shape = unary_union([shape(f["geometry"]) for f in country["features"]])
    if not country_shape.covers(land):
        raise ValueError("The whole assessment boundary must be inside South Africa, excluding neighbouring countries.")
    area_ha = abs(GEOD.geometry_area_perimeter(land)[0]) / 10000
    if not 1 <= area_ha <= 2500:
        raise ValueError("Assess 1–2,500 hectares at a time so free satellite processing stays practical.")
    return {"geometry": mapping(land), "bbox": list(land.bounds), "area_ha": round(area_ha, 2),
            "center": {"lat": land.centroid.y, "lon": land.centroid.x}}
