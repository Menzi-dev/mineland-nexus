import io
import json
from datetime import date
from threading import Lock
from uuid import uuid4
from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, Response
from PIL import Image, ImageOps, UnidentifiedImageError
from pydantic import BaseModel, Field
from . import store
from .engine import EXECUTOR, execute
from .geometry import DATA_DIR, validate_boundary
from .providers import search_places, identify_place
from . import local_ai
from .insights import build_brief, photo_match

router = APIRouter(prefix="/api", tags=["South Africa land intelligence"])
MEDIA = DATA_DIR / "media"
MEDIA.mkdir(exist_ok=True)
Image.MAX_IMAGE_PIXELS = 40_000_000
ADMISSION_LOCK = Lock()


class AssessmentRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    geometry: dict
    location_confirmed: bool = False
    photo_id: str | None = None
    start_year: int = Field(default=2018, ge=2017)
    end_year: int = Field(default_factory=lambda: date.today().year - 1)
    season_month: int = Field(default=1, ge=1, le=10)
    horizon: int = Field(default=5, ge=1, le=15)
    notes: str = Field(default="", max_length=3000)
    property_reference: str = Field(default="", max_length=250)


@router.get("/capabilities")
def capabilities():
    return {"country": "South Africa", "version": "5.0.0", "boundary_ready": (DATA_DIR / "south_africa.geojson").exists(),
        "earliest_satellite_year": 2017, "latest_complete_year": date.today().year - 1, "area_limits_ha": [1, 2500],
        "physical_sensors_required": False,
        "cost": "No paid APIs or API keys. Internet required; fair-use limits apply.",
        "usage": "Open-Meteo free hosted endpoints are for non-commercial use. Review source licences before commercial deployment.",
        "sources": [{"name": name, "url": url} for name, url in [
            ("Sentinel-2 / Earth Search", "https://github.com/Element84/earth-search"),
            ("ERA5 / Open-Meteo", "https://open-meteo.com/en/docs/historical-weather-api"),
            ("CMIP6 / Open-Meteo", "https://open-meteo.com/en/docs/climate-api"),
            ("Copernicus DEM", "https://registry.opendata.aws/copernicus-dem/"),
            ("Annual land cover / Impact Observatory", "https://planetarycomputer.microsoft.com/dataset/io-lulc-annual-v02"),
            ("OpenStreetMap", "https://www.openstreetmap.org/copyright"),
            ("geoBoundaries", "https://www.geoboundaries.org/")]]}


@router.get("/boundary")
def country_boundary():
    path = DATA_DIR / "south_africa.geojson"
    if not path.exists():
        raise HTTPException(503, "Run python backend/bootstrap_data.py to download the country boundary.")
    return FileResponse(path, media_type="application/geo+json")


@router.get("/places")
def places(q: str = Query(min_length=3, max_length=150)):
    try:
        return {"results": search_places(q), "attribution": "© OpenStreetMap contributors"}
    except Exception:
        raise HTTPException(503, "Place search is unavailable. Enter coordinates or select the location on the map.")


@router.get("/location")
def location(lat: float = Query(ge=-35, le=-22), lon: float = Query(ge=16, le=33.1)):
    try:
        return identify_place(lat, lon)
    except Exception:
        raise HTTPException(503, "Address lookup is unavailable. Your coordinates and drawn boundary can still be assessed.")


@router.get("/ai/status")
def ai_status():
    return local_ai.status()


@router.post("/photos/{identifier}/analyse")
def analyse_photo(identifier: str):
    photo = store.get(identifier, "photo")
    if photo is None:
        raise HTTPException(404, "Photo not found")
    photo["visual_analysis"] = local_ai.describe_photo(MEDIA / f"{photo['id']}.jpg")
    return store.save("photo", photo, identifier)


def photo_gps(image):
    try:
        gps = image.getexif().get_ifd(34853)
        def degrees(values):
            return float(values[0]) + float(values[1]) / 60 + float(values[2]) / 3600
        lat = degrees(gps[2]) * (-1 if gps.get(1) in ("S", b"S") else 1)
        lon = degrees(gps[4]) * (-1 if gps.get(3) in ("W", b"W") else 1)
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return None
        return {"lat": lat, "lon": lon, "source": "Photo EXIF GPS; user confirmation required"}
    except (KeyError, TypeError, ValueError, IndexError, ZeroDivisionError):
        return None


@router.post("/photos", status_code=201)
async def upload_photo(file: UploadFile = File(...)):
    content = bytearray()
    while chunk := await file.read(1024 * 1024):
        content.extend(chunk)
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(413, "Use a JPEG, PNG or WebP image no larger than 10 MB.")
    try:
        with Image.open(io.BytesIO(content)) as source:
            if source.format not in ("JPEG", "PNG", "WEBP"):
                raise HTTPException(415, "Supported image formats: JPEG, PNG and WebP.")
            if source.width * source.height > 40_000_000:
                raise HTTPException(413, "Use an image with at most 40 megapixels.")
            source.verify()
        with Image.open(io.BytesIO(content)) as source:
            gps = photo_gps(source)
            captured = source.getexif().get(36867) or source.getexif().get(306)
            dimensions = {"width": source.width, "height": source.height}
            image = ImageOps.exif_transpose(source).convert("RGB")
            image.thumbnail((1600, 1600))
            identifier = uuid4().hex
            image.save(MEDIA / f"{identifier}.jpg", quality=88)
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise HTTPException(415, "The file could not be decoded as a supported image.") from exc
    return store.save("photo", {"created_at": store.now(), "original_name": (file.filename or "photo")[:200],
        "dimensions": dimensions, "gps": gps, "captured_at": str(captured) if captured else None,
        "preview_url": f"/api/photos/{identifier}/preview", "location_status": "gps_unconfirmed" if gps else "location_required",
        "interpretation": "GPS locates the camera, not the land boundary. Without GPS, use a place name, coordinates or the map. Optional local AI describes visible clues; it cannot guarantee a location from a small land photo."}, identifier)


@router.get("/photos/{identifier}/preview")
def preview(identifier: str):
    photo = store.get(identifier, "photo")
    if photo is None:
        raise HTTPException(404, "Photo not found")
    return FileResponse(MEDIA / f"{photo['id']}.jpg", media_type="image/jpeg")


@router.post("/assessments", status_code=202)
def create_assessment(body: AssessmentRequest):
    if not body.name.strip():
        raise HTTPException(422, "Enter an assessment name.")
    if not body.location_confirmed:
        raise HTTPException(422, "Confirm the selected land location and assessment boundary first.")
    if not (body.start_year <= body.end_year < date.today().year and body.end_year - body.start_year >= 4):
        raise HTTPException(422, "Choose at least five complete years, starting in 2017 or later and ending before the current year.")
    if body.end_year + body.horizon + 9 > 2050:
        raise HTTPException(422, "Choose a shorter horizon: the climate comparison must end by 2050.")
    if body.photo_id and not store.get(body.photo_id, "photo"):
        raise HTTPException(422, "The selected photo does not exist.")
    try:
        site = validate_boundary(body.geometry)
    except (ValueError, TypeError, KeyError) as exc:
        raise HTTPException(422, str(exc))
    with ADMISSION_LOCK:
        if sum(row["status"] in ("queued", "running") for row in store.listing("assessment")) >= 3:
            raise HTTPException(429, "Three assessments are queued. Wait for one to finish.")
        record = store.save("assessment", {"name": body.name.strip(), "created_at": store.now(), "status": "queued",
            "stage": "Queued for satellite processing", "progress": 0, "site": site, "photo_id": body.photo_id,
            "location_confirmed": True, "user_notes": body.notes,
            "property_reference": body.property_reference.strip(),
            "options": {key: getattr(body, key) for key in ("start_year", "end_year", "season_month", "horizon")}})
        EXECUTOR.submit(execute, record["id"])
    return record


@router.get("/assessments")
def assessments():
    return {"assessments": [{key: value for key, value in row.items() if key != "result"} for row in store.listing("assessment")]}


@router.get("/assessments/{identifier}")
def assessment(identifier: str):
    record = store.get(identifier, "assessment")
    if record is None:
        raise HTTPException(404, "Assessment not found")
    # Give existing reports the readable summary without rewriting their historical evidence.
    if record.get("result") and "brief" not in record["result"]:
        photo = store.get(record.get("photo_id"), "photo") if record.get("photo_id") else None
        record["result"]["brief"] = build_brief(record["result"], record["site"], photo)
        if photo:
            record["result"]["photo"] = photo
    return record


@router.get("/assessments/{identifier}/report")
def report(identifier: str):
    record = assessment(identifier)
    return Response(json.dumps(record, indent=2, ensure_ascii=False, allow_nan=False), media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="mineland-{record["id"]}.json"'})


@router.get("/assessments/{identifier}/overlay")
def overlay(identifier: str):
    record = assessment(identifier)
    path = DATA_DIR / f"{record['id']}_ndvi.png"
    if not path.exists():
        raise HTTPException(404, "No satellite overlay available.")
    return FileResponse(path, media_type="image/png")
