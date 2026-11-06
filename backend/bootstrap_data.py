"""Download a free, attributed country boundary; never substitutes a bounding box."""
import json
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent / "data" / "national"
ROOT.mkdir(parents=True, exist_ok=True)

def main():
    endpoint = "https://www.geoboundaries.org/api/current/gbOpen/ZAF/ADM0/"
    response = requests.get(endpoint, timeout=60)
    response.raise_for_status()
    metadata = response.json()
    response = requests.get(metadata["gjDownloadURL"], timeout=90)
    response.raise_for_status()
    data = response.json()
    from shapely.geometry import shape, mapping
    for feature in data["features"]:
        feature["geometry"] = mapping(shape(feature["geometry"]).simplify(0.0002, preserve_topology=True))
    (ROOT / "south_africa.geojson").write_text(json.dumps(data), encoding="utf-8")
    (ROOT / "boundary_source.json").write_text(json.dumps({
        "source": endpoint, "download": metadata["gjDownloadURL"],
        "license": metadata.get("boundaryLicense"), "attribution": "geoBoundaries / original boundary contributors",
        "boundary_year": metadata.get("boundaryYearRepresented"),
        "note": "Simplified by 0.0002 degrees; assessment extent only, not a cadastral boundary."
    }, indent=2), encoding="utf-8")
    print("Downloaded South Africa boundary to", ROOT)

if __name__ == "__main__":
    main()
