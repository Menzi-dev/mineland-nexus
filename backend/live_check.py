"""Real-data smoke check; downloads small public raster windows, not whole scenes."""
import json
import sys
from app.national.geometry import validate_boundary, DATA_DIR
from app.national.providers import satellite_history, weather_history, climate_future, terrain
from app.national import store
from app.national.engine import execute

def main():
    # An assessment extent near Johannesburg; no claim that this land is abandoned.
    site = validate_boundary({"type": "Polygon", "coordinates": [[[28.01, -26.23], [28.025, -26.23], [28.025, -26.215], [28.01, -26.215], [28.01, -26.23]]]})
    if "--full" in sys.argv:
        record = store.save("assessment", {"name": "Johannesburg real-data verification", "created_at": store.now(), "status": "queued", "progress": 0,
            "stage": "Verification queued", "site": site, "photo_id": None, "location_confirmed": True,
            "user_notes": "Engineering verification extent only. Abandonment is not asserted.",
            "options": {"start_year": 2019, "end_year": 2025, "season_month": 6, "horizon": 5}})
        print("ASSESSMENT_ID=" + record["id"], flush=True)
        execute(record["id"])
        result = store.get(record["id"], "assessment")
        print(json.dumps({"status": result["status"], "stage": result["stage"], "sources": {k: v.get("status") for k, v in result.get("result", {}).items() if isinstance(v, dict)}, "error": result.get("error")}), flush=True)
        if result["status"] == "failed":
            sys.exit(1)
    else:
        satellite, overlay = satellite_history(site, 2025, 2025, 6, lambda text, percent: print(text, flush=True))
        print(json.dumps(satellite, indent=2), flush=True)
        if not satellite["observations"]:
            sys.exit(1)

if __name__ == "__main__":
    main()
