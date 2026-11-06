from concurrent.futures import ThreadPoolExecutor
import logging
import numpy as np
from PIL import Image

from . import providers, store
from .analysis import trend_forecast, screening, evidence_summary
from .geometry import DATA_DIR
from .insights import build_brief

EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="assessment")
LOG = logging.getLogger(__name__)


def safe_source(name, call):
    try:
        return call()
    except Exception as exc:
        LOG.warning("%s unavailable: %s", name, exc)
        return {"status": "unavailable", "source": name, "reason": str(exc)[:300], "retrieved_at": store.now()}


def execute(record_id):
    record = store.get(record_id, "assessment")
    def progress(stage, percent):
        record.update(status="running", stage=stage, progress=percent)
        store.save("assessment", record, record_id)
    try:
        site, options = record["site"], record["options"]
        progress("Finding historical satellite scenes", 8)
        overlay = None
        try:
            satellite, overlay = providers.satellite_history(site, options["start_year"], options["end_year"], options["season_month"], progress)
        except Exception as exc:
            satellite = {"status": "unavailable", "source": "Sentinel-2", "reason": str(exc)[:300], "observations": []}
        progress("Retrieving historical weather and climate models", 68)
        with ThreadPoolExecutor(max_workers=8) as pool:
            tasks = {
                "weather": pool.submit(safe_source, "ERA5", lambda: providers.weather_history(site, options["start_year"], options["end_year"])),
                "climate": pool.submit(safe_source, "CMIP6", lambda: providers.climate_future(site, options["end_year"], options["horizon"])),
                "context": pool.submit(safe_source, "OpenStreetMap", lambda: providers.mapped_context(site)),
                "terrain": pool.submit(safe_source, "Copernicus DEM", lambda: providers.terrain(site)),
                "landcover": pool.submit(safe_source, "Annual land cover", lambda: providers.landcover_history(site, options["start_year"], options["end_year"])),
                "moisture": pool.submit(safe_source, "ERA5-Land soil moisture", lambda: providers.soil_moisture(site, options["start_year"], options["end_year"])),
                "place": pool.submit(safe_source, "Mapped address", lambda: providers.identify_place(site["center"]["lat"], site["center"]["lon"])),
                "research": pool.submit(safe_source, "Nearby public history", lambda: providers.public_history(site)),
            }
            sources = {name: future.result() for name, future in tasks.items()}
        progress("Evaluating trends, uncertainty and evidence", 92)
        forecast = trend_forecast(satellite.get("observations", []), options["horizon"])
        result = {"satellite": satellite, **sources, "forecast": forecast,
                  "history": evidence_summary(satellite, sources["context"], sources["landcover"]),
                  "screening": screening(satellite, sources["weather"], sources["climate"], sources["terrain"], forecast, sources["landcover"]),
                  "limitations": ["A photograph without GPS cannot identify its location reliably. The user-confirmed boundary defines this assessment.",
                    "The boundary is an assessment area, not a cadastral parcel or automated abandoned-land detection.",
                    "Clouds, mixed pixels, seasonal timing and sparse observations affect satellite estimates.",
                    "ERA5 and CMIP6 are gridded model products; no physical sensors are used on this site.",
                    "Ownership, abandonment, closure causes, contamination, groundwater, protected status and legal permission are not verified.",
                    "Forecasts and suitability rubrics require independent validation before real land-management decisions."],
                  "method_version": "national-evidence-v2", "completed_at": store.now()}
        photo = store.get(record.get("photo_id"), "photo") if record.get("photo_id") else None
        if photo:
            result["photo"] = photo
        result["brief"] = build_brief(result, site, photo)
        if overlay is not None:
            array, acquired, bbox = overlay
            normalized = np.clip((np.nan_to_num(array, nan=-1) + 0.2) / 1.0, 0, 1)
            rgba = np.zeros((*array.shape, 4), dtype="uint8")
            rgba[..., 0] = (190 * (1 - normalized)).astype("uint8")
            rgba[..., 1] = (90 + 110 * normalized).astype("uint8")
            rgba[..., 2] = 65
            rgba[..., 3] = np.where(np.isfinite(array), 210, 0)
            Image.fromarray(rgba).save(DATA_DIR / f"{record_id}_ndvi.png")
            result["overlay"] = {"url": f"/api/assessments/{record_id}/overlay", "date": acquired,
                "coordinates": [[bbox[0], bbox[3]], [bbox[2], bbox[3]], [bbox[2], bbox[1]], [bbox[0], bbox[1]]],
                "legend": {"minimum": -0.2, "maximum": 0.8, "note": "NDVI colour scale clipped to −0.2…0.8; transparent pixels were excluded."}}
        complete = (satellite.get("status") == "available" and not satellite.get("gaps")
                    and all(s.get("status") == "available" for s in sources.values())
                    and not sources["landcover"].get("missing_years") and not sources["climate"].get("gaps")
                    and not sources['moisture'].get('gaps'))
        record.update(status="complete" if complete else "partial", stage="Assessment ready" if complete else "Assessment ready with data gaps", progress=100, result=result)
        store.save("assessment", record, record_id)
    except Exception as exc:
        LOG.exception("Assessment failed")
        record.update(status="failed", stage="Assessment failed", error=str(exc)[:500])
        store.save("assessment", record, record_id)
