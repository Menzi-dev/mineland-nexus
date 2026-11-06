"""Free public data adapters. Failed providers return missing evidence, never invented values."""
import calendar
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import time
from datetime import date, timedelta
from threading import Lock
from uuid import uuid4

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.features import geometry_mask
from rasterio.transform import from_bounds
from rasterio.vrt import WarpedVRT
import requests

from .geometry import DATA_DIR
from .store import now

STAC = "https://earth-search.aws.element84.com/v1"
COLLECTION = "sentinel-2-c1-l2a"
CACHE = DATA_DIR / "cache"
CACHE.mkdir(exist_ok=True)
HTTP_HEADERS = {"User-Agent": "MineLandNexus/5.0 (local noncommercial land research)"}
_osm_lock = Lock()
_last_osm = 0.0


def fetch(url, params=None, ttl=86400, read_timeout=45):
    key = hashlib.sha256(json.dumps([url, params], sort_keys=True).encode()).hexdigest()
    path = CACHE / (key + ".json")
    if path.exists() and time.time() - path.stat().st_mtime < ttl:
        return json.loads(path.read_text(encoding="utf-8"))
    response = requests.get(url, params=params, headers=HTTP_HEADERS, timeout=(10, read_timeout))
    response.raise_for_status()
    result = response.json()
    temporary = path.with_name(f".{key}.{uuid4().hex}.tmp")
    temporary.write_text(json.dumps(result), encoding="utf-8")
    temporary.replace(path)
    return result


def search_places(query):
    global _last_osm
    with _osm_lock:
        time.sleep(max(0, 1.1 - (time.monotonic() - _last_osm)))
        try:
            data = fetch("https://nominatim.openstreetmap.org/search", {
                "q": query, "format": "jsonv2", "countrycodes": "za", "limit": 5,
            }, ttl=30 * 86400)
        finally:
            _last_osm = time.monotonic()
    return [{"name": row["display_name"], "lat": float(row["lat"]), "lon": float(row["lon"])} for row in data]


def identify_place(lat, lon):
    """Nearest mapped address, never a claim of parcel identity."""
    global _last_osm
    with _osm_lock:
        time.sleep(max(0, 1.1 - (time.monotonic() - _last_osm)))
        try:
            data = fetch("https://nominatim.openstreetmap.org/reverse", {
                "lat": lat, "lon": lon, "format": "jsonv2", "zoom": 16, "addressdetails": 1,
            }, ttl=30 * 86400, read_timeout=15)
        finally:
            _last_osm = time.monotonic()
    if data.get("error") or not data.get("display_name"):
        raise ValueError("No mapped address found. The selected coordinates still define the assessment.")
    return {"status": "available", "name": data["display_name"], "address": data.get("address", {}),
            "source": "OpenStreetMap / Nominatim", "retrieved_at": now(),
            "source_url": f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=16/{lat}/{lon}",
            "note": "Nearest mapped address to the assessment centre, not a verified property name or boundary."}


def public_history(site):
    """Geographically constrained background reading with explicit distance and scope."""
    from math import radians, sin, cos, asin, sqrt
    lat, lon = site["center"]["lat"], site["center"]["lon"]
    data = fetch("https://en.wikipedia.org/w/api.php", {
        "action": "query", "generator": "geosearch", "ggscoord": f"{lat}|{lon}", "ggsradius": 10000,
        "ggslimit": 5, "prop": "extracts|coordinates|info", "exintro": 1, "explaintext": 1,
        "exsentences": 2, "inprop": "url", "format": "json",
    }, ttl=7 * 86400, read_timeout=20)
    articles = []
    for row in data.get("query", {}).get("pages", {}).values():
        coords = row.get("coordinates", [])
        if not coords or not row.get("extract"):
            continue
        p = coords[0]
        a = sin(radians(p["lat"] - lat) / 2) ** 2 + cos(radians(lat)) * cos(radians(p["lat"])) * sin(radians(p["lon"] - lon) / 2) ** 2
        distance = 6371 * 2 * asin(sqrt(min(1, a)))
        # Keep short, attributed excerpts; articles describe their subject, not this parcel.
        excerpt = " ".join(row["extract"].split()[:65])
        articles.append({"title": row["title"], "excerpt": excerpt, "distance_km": round(distance, 2),
                         "source_url": row["fullurl"], "revision_id": row.get("lastrevid"), "scope": "nearby_area_only"})
    return {"status": "available", "source": "Wikipedia geosearch / contributors (CC BY-SA)",
            "source_url": "https://en.wikipedia.org/", "retrieved_at": now(),
            "articles": sorted(articles, key=lambda r: r["distance_km"]), "radius_km": 10,
            "note": "Background about nearby places, not verified history or ownership of the selected land. Empty results do not mean there is no history."}


def soil_moisture(site, start_year, end_year):
    fields = {"surface_m3_m3": "soil_moisture_0_to_7cm_mean", "shallow_subsurface_m3_m3": "soil_moisture_7_to_28cm_mean"}
    def year_data(year):
        try:
            data = fetch("https://archive-api.open-meteo.com/v1/archive", {
                "latitude": site["center"]["lat"], "longitude": site["center"]["lon"],
                "start_date": f"{year}-01-01", "end_date": f"{year}-12-31", "models": "era5_land",
                "daily": ",".join(fields.values()), "timezone": "Africa/Johannesburg",
            }, ttl=30 * 86400)
            return year, data.get("daily", {}), None
        except Exception as exc:
            return year, {}, str(exc)[:200]
    daily = {"time": [], **{field: [] for field in fields.values()}}
    gaps = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        for year, values, failure in pool.map(year_data, range(start_year, end_year + 1)):
            if failure:
                gaps.append({"year": year, "reason": failure})
            times = values.get("time", [])
            daily["time"].extend(times)
            for field in fields.values():
                samples = values.get(field, [])
                daily[field].extend((samples + [None] * len(times))[:len(times)])
    def aggregate(prefix, expected):
        indices = [i for i, day in enumerate(daily.get("time", [])) if day.startswith(prefix)]
        row = {}
        for key, field in fields.items():
            values = [daily[field][i] for i in indices if i < len(daily.get(field, [])) and daily[field][i] is not None]
            row[key] = round(float(np.mean(values)), 4) if len(values) >= .9 * expected else None
        return row
    annual = [{"year": year, **aggregate(str(year), 366 if calendar.isleap(year) else 365)} for year in range(start_year, end_year + 1)]
    monthly = [{"month": m, **aggregate(f"{end_year}-{m:02}", calendar.monthrange(end_year, m)[1])} for m in range(1, 13)]
    return {"status": "available" if any(r["surface_m3_m3"] is not None for r in annual) else "unavailable",
            "source": "Open-Meteo / ECMWF ERA5-Land", "source_url": "https://open-meteo.com/en/docs/historical-weather-api",
            "retrieved_at": now(), "annual": annual, "monthly": monthly, "monthly_year": end_year, "gaps": gaps,
            "resolution": "Approximately 11 km model grid; not a soil measurement on this plot",
            "note": "Volumetric water content in m³/m³. Surface: 0–7 cm; shallow subsurface: 7–28 cm, not the full plant root zone. Multiply by 100 for volume percent. Not relative saturation, irrigation advice or a laboratory soil test."}


def _read_band(asset, bbox, size, categorical=False, physical=False):
    href = asset["href"]
    if href.startswith("s3://copernicus-dem-30m/"):
        href = href.replace("s3://copernicus-dem-30m/", "https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com/", 1)
    if not href.startswith("https://"):
        raise ValueError("This raster requires an account; it was excluded from this free assessment.")
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_TIMEOUT="25",
                      GDAL_HTTP_CONNECTTIMEOUT="10", GDAL_HTTP_MAX_RETRY="1",
                      CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif", VSI_CACHE=True):
        with rasterio.open(href) as source:
            with WarpedVRT(source, crs="EPSG:4326", transform=from_bounds(*bbox, size, size),
                           width=size, height=size, resampling=Resampling.nearest if categorical else Resampling.bilinear,
                           nodata=float('nan'), dtype="float32") as vrt:
                raw = vrt.read(1, masked=True).astype("float32").filled(np.nan)
    if categorical or physical:
        return raw
    band = asset.get("raster:bands", [{}])[0]
    if "scale" not in band:
        raise ValueError("Reflectance calibration metadata is absent; scene excluded.")
    return raw * band["scale"] + band.get("offset", 0)


def _ratio(a, b):
    return np.divide(a - b, a + b, out=np.full_like(a, np.nan), where=np.abs(a + b) > 0.00001)


def satellite_history(site, start_year, end_year, month, progress):
    """Sample the same 3-month season in each year; no annual mean claims."""
    bbox, geometry = site["bbox"], site["geometry"]
    # Keep ~20m resolution for smaller plots; cap bandwidth for larger plots.
    span_m = max((bbox[2] - bbox[0]) * 111320 * np.cos(np.deg2rad(site["center"]["lat"])), (bbox[3] - bbox[1]) * 111320)
    size = max(16, min(192, int(np.ceil(span_m / 20))))
    inside = geometry_mask([geometry], out_shape=(size, size), transform=from_bounds(*bbox, size, size), invert=True)
    if inside.sum() < 9:
        raise ValueError("Boundary is too narrow for reliable 20m satellite sampling.")
    observations, gaps = [], []
    latest_overlay = None
    for year in range(start_year, end_year + 1):
        progress(f"Reading Sentinel-2 observations for {year}", 12 + int(53 * (year - start_year) / (end_year - start_year + 1)))
        first = date(year, month, 1)
        last_month = min(12, month + 2)
        last = date(year, last_month, calendar.monthrange(year, last_month)[1])
        try:
            catalog = fetch(STAC + "/search", {
                "collections": COLLECTION, "bbox": ",".join(map(str, bbox)),
                "datetime": f"{first}T00:00:00Z/{last}T23:59:59Z", "limit": 100,
                "query": json.dumps({"eo:cloud_cover": {"lt": 60}}),
            }, ttl=30 * 86400)
            scenes = sorted(catalog.get("features", []), key=lambda f: f["properties"].get("eo:cloud_cover", 100))
            samples, arrays, used_days = [], [], set()
            for scene in scenes[:12]:
                day = scene["properties"]["datetime"][:10]
                if day in used_days:
                    continue
                try:
                    cache_key = hashlib.sha256(json.dumps([scene["id"], geometry, size, "c1-scaled-v1"], sort_keys=True).encode()).hexdigest()
                    cached_scene = CACHE / f"scene_{cache_key}.npz"
                    if cached_scene.exists():
                        with np.load(cached_scene, allow_pickle=False) as cache:
                            samples.append(json.loads(str(cache["summary"])))
                            arrays.append(cache["ndvi"].copy())
                        used_days.add(day)
                        if len(samples) == 3:
                            break
                        continue
                    assets = scene["assets"]
                    scl = _read_band(assets["scl"], bbox, size, True)
                    clear = inside & np.isin(scl, [4, 5, 6])
                    if clear.sum() / inside.sum() < 0.7:
                        continue
                    with ThreadPoolExecutor(max_workers=4) as pool:
                        pending = {key: pool.submit(_read_band, assets[key], bbox, size) for key in ("red", "green", "nir", "swir16")}
                        bands = {key: future.result() for key, future in pending.items()}
                    valid = clear.copy()
                    for band in bands.values():
                        valid &= np.isfinite(band) & (band >= 0) & (band <= 1.5)
                    if valid.sum() / inside.sum() < 0.7:
                        continue
                    ndvi = _ratio(bands["nir"], bands["red"])
                    ndwi = _ratio(bands["green"], bands["nir"])
                    ndbi = _ratio(bands["swir16"], bands["nir"])
                    indices = {"ndvi": ndvi, "ndwi": ndwi, "ndbi": ndbi}
                    samples.append({"scene_id": scene["id"], "date": day,
                                    "catalogue_url": STAC + f"/collections/{COLLECTION}/items/{scene['id']}",
                                    "tile_cloud_percent": scene["properties"].get("eo:cloud_cover"),
                                    "valid_fraction": round(float(valid.sum() / inside.sum()), 3),
                                    **{k: round(float(np.nanmedian(v[valid])), 4) for k, v in indices.items()}})
                    arrays.append(np.where(valid, ndvi, np.nan))
                    np.savez_compressed(cached_scene, summary=json.dumps(samples[-1]), ndvi=arrays[-1])
                    used_days.add(day)
                    if len(samples) == 3:
                        break
                except Exception as exc:
                    gaps.append({"year": year, "scene_id": scene["id"], "reason": str(exc)[:200]})
                    if len([g for g in gaps if g["year"] == year and "scene_id" in g]) >= 3:
                        break
            if samples:
                observations.append({"year": year, "season": f"{first} to {last}", "scene_count": len(samples),
                    **{key: round(float(np.median([s[key] for s in samples])), 4) for key in ("ndvi", "ndwi", "ndbi")},
                    "valid_fraction": round(float(np.mean([s["valid_fraction"] for s in samples])), 3), "scenes": samples})
                # Use the most recent actual observation, not a basemap capture date.
                latest_index = max(range(len(samples)), key=lambda i: samples[i]["date"])
                latest_overlay = (arrays[latest_index], samples[latest_index]["date"], bbox)
            else:
                gaps.append({"year": year, "reason": "No usable scenes covering at least 70% of the selected land in this season."})
        except Exception as exc:
            gaps.append({"year": year, "reason": str(exc)[:240]})
    return {"status": "available" if observations else "unavailable", "source": "Copernicus Sentinel-2 Collection 1 L2A / Element 84 Earth Search",
            "source_url": "https://registry.opendata.aws/sentinel-2-l2a-cogs/", "collection": COLLECTION,
            "retrieved_at": now(), "observations": observations, "gaps": gaps,
            "method": "Median of up to 3 distinct clear acquisition dates per year in the same 3-month season. SCL vegetation, bare ground and water only; clouds, shadows, snow and unclassified pixels excluded. Reflectance uses Collection 1 STAC scale/offset.",
            "grid_size": size, "approximate_grid_spacing_m": round(span_m / size, 1)}, latest_overlay


def weather_history(site, start_year, end_year):
    data = fetch("https://archive-api.open-meteo.com/v1/archive", {
        "latitude": site["center"]["lat"], "longitude": site["center"]["lon"],
        "start_date": f"{start_year}-01-01", "end_date": f"{end_year}-12-31", "models": "era5",
        "daily": "temperature_2m_mean,precipitation_sum,shortwave_radiation_sum,et0_fao_evapotranspiration", "timezone": "Africa/Johannesburg",
    }, ttl=30 * 86400)
    daily = data.get("daily", {})
    annual = []
    for year in range(start_year, end_year + 1):
        indices = [i for i, day in enumerate(daily.get("time", [])) if day.startswith(str(year))]
        row = {"year": year}
        for key, field, aggregate in [("temperature_c", "temperature_2m_mean", "mean"), ("rainfall_mm", "precipitation_sum", "sum"),
                                      ("solar_kwh_m2_day", "shortwave_radiation_sum", "solar"), ("evapotranspiration_mm", "et0_fao_evapotranspiration", "sum")]:
            values = [daily.get(field, [])[i] for i in indices if i < len(daily.get(field, [])) and daily[field][i] is not None]
            if len(values) < 0.9 * (366 if calendar.isleap(year) else 365):
                row[key] = None
            else:
                result = sum(values) if aggregate == "sum" else float(np.mean(values)) / (3.6 if aggregate == "solar" else 1)
                row[key] = round(result, 2)
        annual.append(row)
    return {"status": "available" if any(r["temperature_c"] is not None for r in annual) else "unavailable",
            "source": "Open-Meteo / ECMWF ERA5", "source_url": "https://open-meteo.com/en/docs/historical-weather-api",
            "retrieved_at": now(), "resolution": "Approximately 25 km; reanalysis, not an on-site sensor", "annual": annual}


def climate_future(site, end_year, horizon):
    target = end_year + horizon
    baseline = (end_year - 9, end_year)
    future = (target, min(target + 9, 2050))
    results, failures = [], []
    for model in ("EC_Earth3P_HR", "MRI_AGCM3_2_S"):
        try:
            daily = fetch("https://climate-api.open-meteo.com/v1/climate", {
                "latitude": site["center"]["lat"], "longitude": site["center"]["lon"],
                "start_date": f"{baseline[0]}-01-01", "end_date": f"{future[1]}-12-31", "models": model,
                "daily": "temperature_2m_mean,precipitation_sum", "timezone": "GMT",
            }, ttl=90 * 86400).get("daily", {})
            def period(lo, hi):
                idx = [i for i, day in enumerate(daily.get("time", [])) if lo <= int(day[:4]) <= hi]
                temperatures = [daily["temperature_2m_mean"][i] for i in idx if daily["temperature_2m_mean"][i] is not None]
                rain = [daily["precipitation_sum"][i] for i in idx if daily["precipitation_sum"][i] is not None]
                if min(len(temperatures), len(rain)) < 0.9 * 365 * (hi - lo + 1):
                    raise ValueError("Incomplete climate-model period")
                return float(np.mean(temperatures)), sum(rain) / (hi - lo + 1)
            bt, br = period(*baseline)
            ft, fr = period(*future)
            results.append({"model": model, "temperature_change_c": round(ft - bt, 2),
                            "rainfall_change_percent": round(100 * (fr - br) / br, 2) if br > 0 else None})
        except Exception as exc:
            failures.append({"model": model, "reason": str(exc)[:200]})
    return {"status": "available" if results else "unavailable", "source": "Open-Meteo / CMIP6 HighResMIP",
            "source_url": "https://open-meteo.com/en/docs/climate-api", "retrieved_at": now(),
            "baseline_period": list(baseline), "future_period": list(future), "models": results, "gaps": failures,
            "interpretation": "Model-specific decadal climate changes under HighResMIP forcings, not a weather forecast or a multi-emissions-scenario comparison. Model spread is not a calibrated confidence interval."}


def mapped_context(site):
    west, south, east, north = site["bbox"]
    query = f'[out:json][timeout:20];nwr["landuse"]({south},{west},{north},{east});out tags center 80;'
    data = None
    failure = None
    for endpoint in ("https://overpass.private.coffee/api/interpreter", "https://overpass-api.de/api/interpreter"):
        try:
            data = fetch(endpoint, {"data": query}, ttl=7 * 86400, read_timeout=25)
            break
        except Exception as exc:
            failure = exc
    if data is None:
        raise failure
    features = [{"osm_type": f["type"], "osm_id": f["id"], "tags": f.get("tags", {}),
                 "source_url": f"https://www.openstreetmap.org/{f['type']}/{f['id']}"} for f in data.get("elements", [])]
    return {"status": "available", "source": "OpenStreetMap contributors (ODbL)", "source_url": "https://www.openstreetmap.org/copyright",
            "retrieved_at": now(), "features": features,
            "note": "Mapped land-use tags intersecting the search rectangle; not verified ownership, exact parcel overlap, activity dates, or proof of abandonment."}


def terrain(site):
    catalog = fetch(STAC + "/search", {"collections": "cop-dem-glo-30", "bbox": ",".join(map(str, site["bbox"])), "limit": 6}, ttl=90 * 86400)
    arrays, scenes = [], []
    size = 96
    for feature in catalog.get("features", []):
        asset = feature["assets"].get("data")
        if asset:
            arrays.append(_read_band(asset, site["bbox"], size, physical=True))
            scenes.append(feature["id"])
    if not arrays:
        raise ValueError("No public Copernicus DEM tile found")
    with np.errstate(invalid="ignore"):
        elevation = np.nanmax(np.stack(arrays), axis=0)
    mask = geometry_mask([site["geometry"]], out_shape=(size, size), transform=from_bounds(*site["bbox"], size, size), invert=True)
    west, south, east, north = site["bbox"]
    dy = (north - south) * 111320 / size
    dx = (east - west) * 111320 * np.cos(np.deg2rad(site["center"]["lat"])) / size
    gy, gx = np.gradient(elevation, dy, dx)
    slope = np.rad2deg(np.arctan(np.hypot(gx, gy)))
    valid = mask & np.isfinite(elevation) & np.isfinite(slope)
    if valid.sum() / mask.sum() < 0.9:
        raise ValueError("Incomplete terrain coverage")
    return {"status": "available", "source": "Copernicus DEM GLO-30", "source_url": "https://registry.opendata.aws/copernicus-dem/",
            "retrieved_at": now(), "elevation_mean_m": round(float(np.mean(elevation[valid])), 1),
            "slope_median_degrees": round(float(np.median(slope[valid])), 1), "tiles": scenes,
            "note": "Approximately 30m surface elevation; slope is a screening estimate, not an engineering survey."}


def landcover_history(site, start_year, end_year):
    """Published annual classifier outputs, never claimed as actual activity records."""
    endpoint = "https://planetarycomputer.microsoft.com/api/stac/v1"
    collection = "io-lulc-annual-v02"
    catalog = fetch(endpoint + "/search", {"collections": collection,
        "bbox": ",".join(map(str, site["bbox"])), "limit": 100,
        "datetime": f"{start_year}-01-01T00:00:00Z/{end_year}-12-31T23:59:59Z"}, ttl=30 * 86400)
    classes = {1: "Water", 2: "Trees", 4: "Flooded vegetation", 5: "Crops", 7: "Built area", 8: "Bare ground", 9: "Snow / ice", 11: "Rangeland"}
    size = 128
    inside = geometry_mask([site["geometry"]], out_shape=(size, size), transform=from_bounds(*site["bbox"], size, size), invert=True)
    by_year = {}
    gaps = []
    for feature in catalog.get("features", []):
        props = feature["properties"]
        stamp = props.get("start_datetime") or props.get("datetime") or feature["id"].split("-")[-1]
        year = int(stamp[:4])
        if not start_year <= year <= end_year:
            continue
        by_year.setdefault(year, []).append(feature)
    years = []
    for year, features in sorted(by_year.items()):
        combined = np.full((size, size), np.nan)
        ids = []
        try:
            for feature in features:
                href = feature["assets"]["data"]["href"]
                response = requests.get("https://planetarycomputer.microsoft.com/api/sas/v1/sign", params={"href": href}, headers=HTTP_HEADERS, timeout=(10, 30))
                response.raise_for_status()
                array = _read_band({"href": response.json()["href"]}, site["bbox"], size, True)
                valid = np.isin(array, list(classes))
                take = ~np.isfinite(combined) & valid
                combined[take] = array[take]
                ids.append(feature["id"])
            valid = inside & np.isfinite(combined)
            coverage = float(valid.sum() / inside.sum())
            if coverage < 0.7:
                raise ValueError("Less than 70% valid classified land coverage")
            fractions = [{"class": label, "percent": round(float(np.sum(combined[valid] == key) / valid.sum() * 100), 1)} for key, label in classes.items()]
            fractions.sort(key=lambda item: item["percent"], reverse=True)
            years.append({"year": year, "dominant_class": fractions[0]["class"], "fractions": fractions,
                          "valid_fraction": round(coverage, 3), "item_ids": ids,
                          "catalogue_urls": [endpoint + f"/collections/{collection}/items/{identifier}" for identifier in ids]})
        except Exception as exc:
            gaps.append({"year": year, "reason": str(exc)[:200]})
    missing_years = sorted(set(range(start_year, end_year + 1)) - {row["year"] for row in years})
    return {"status": "available" if years else "unavailable", "source": "Impact Observatory / Esri / Microsoft annual 10m land cover v2",
            "source_url": "https://planetarycomputer.microsoft.com/dataset/io-lulc-annual-v02", "retrieved_at": now(),
            "years": years, "missing_years": missing_years, "gaps": gaps,
            "note": "Published satellite-derived classes sampled within the land boundary. Classification errors and mixed pixels remain; bare ground is not proof of mining or abandonment, and a crops class is not a dated activity record. Missing product years are not filled in."}
