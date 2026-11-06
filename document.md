# MineLand Nexus Project Documentation

> Historical prototype snapshot. The active South Africa-wide application, setup, sources and limitations are documented in [README.md](README.md). Several implementation statements below describe an earlier version.

## 1. Project Overview

MineLand Nexus is a geospatial intelligence prototype focused on the Sishen/Kathu mining region in the Northern Cape, South Africa.

The intended platform combines:

- Satellite vegetation analysis
- Water-presence analysis
- Solar-energy assessment
- Mining-area GIS data
- Future land suitability and environmental analysis
- Future IoT data, uploads, and persistent site records

The strongest implemented capability is satellite-based NDVI and NDWI analysis for the Sishen/Kathu study area.

The project currently contains multiple prototype paths. The active frontend uses a cached/openEO-style FastAPI entry point, while other backend routers and UI components represent additional, partially connected functionality.

## 2. Repository Structure

### Frontend

The `frontend` directory contains a React application built with Vite, Tailwind CSS, and MapLibre GL.

Important files:

- `frontend/src/main.jsx`: React entry point
- `frontend/src/App.jsx`: Main application shell
- `frontend/src/components/SatelliteDashboard.jsx`: Active satellite analysis UI
- `frontend/src/components/Map.jsx`: Separate, currently unused map UI
- `frontend/src/components/Dashboard.jsx`: Empty placeholder
- `frontend/src/components/Upload.jsx`: Empty placeholder
- `frontend/src/services/api.js`: Axios API client
- `frontend/vite.config.js`: Vite server and proxy configuration
- `frontend/package.json`: Frontend dependencies and scripts

### Backend

The `backend` directory contains a FastAPI application and supporting service classes.

Important files:

- `backend/app/main.py`: Main cached/openEO API entry point
- `backend/app/main_simple.py`: Older mock-data API entry point
- `backend/app/services/satellite_service.py`: openEO satellite processing
- `backend/app/services/sentinel_service.py`: Sentinel Hub satellite processing
- `backend/app/services/power_service.py`: NASA POWER integration
- `backend/app/services/mining_service.py`: DPME ArcGIS integration
- `backend/app/routers/satellite.py`: Satellite, solar, and mining routes
- `backend/app/models/site_models.py`: PostGIS-backed SQLAlchemy models
- `backend/app/database.py`: PostgreSQL and TimescaleDB connections
- `backend/docker-compose.yml`: Local database and object-storage infrastructure

### Data

The repository contains:

- `data/boundaries/sishen_kathu.geojson`: Simplified boundary source asset
- `data/boundaries/SA_NLC_2022_ALBERS.tif`: Raster source asset
- `backend/data/northern_cape`: Prefetched NDVI and NDWI JSON artifacts

## 3. Active Frontend Flow

The frontend starts in `frontend/src/main.jsx`, which renders `App` into the HTML root element.

`App.jsx` performs a health check against `http://localhost:8002/health`. It displays either a connected or disconnected API status and renders `SatelliteDashboard`.

The active screen provides:

- Sishen/Kathu location information
- Northern Cape project context
- Start and end date inputs
- NDVI request button
- NDWI request button
- Quick NDVI test button
- Clear-results button
- Loading indicator
- Error display
- NDVI and NDWI result cards
- Value interpretation guidance

The dashboard sends requests through `frontend/src/services/api.js`:

```text
GET http://localhost:8002/api/ndvi?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
GET http://localhost:8002/api/ndwi?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
```

The response is expected to contain a success status, summary statistics, processing period, source, study area, and raster shape.

## 4. Active Backend Flow

The primary backend entry point is `backend/app/main.py`.

It creates a FastAPI application named `app`, enables CORS for the local frontend, and creates one `SatelliteService` instance.

Its declared routes are:

| Route | Purpose |
| --- | --- |
| `GET /` | API status, region, cache information, and endpoint list |
| `GET /health` | Health check |
| `GET /api/ndvi` | NDVI for a requested date range |
| `GET /api/ndwi` | NDWI for a requested date range |
| `GET /api/cached/ndvi` | Intended cached NDVI response |
| `GET /api/cached/ndwi` | Intended cached NDWI response |

When run directly, `main.py` starts Uvicorn on port `8000`.

## 5. Satellite Processing

`SatelliteService` connects to the Copernicus openEO endpoint:

```text
https://openeo.dataspace.copernicus.eu/
```

The configured study bounding box is:

```text
West:  27.45
East:  27.55
South: -23.50
North: -23.40
```

### NDVI

The service loads Sentinel-2 L2A data using bands B04 and B08, resamples it to 50-meter resolution, and calculates:

```text
NDVI = (B08 - B04) / (B08 + B04)
```

The resulting process graph is downloaded as `temp_ndvi.tif`. Rasterio reads the first band and NumPy calculates:

- Mean
- Minimum
- Maximum
- Raster shape

The temporary file is then deleted and the statistics are returned as JSON.

### NDWI

NDWI follows the same process using B03 and B08:

```text
NDWI = (B03 - B08) / (B03 + B08)
```

NDVI is used as an indicator of vegetation health. NDWI is used as an indicator of water or moisture presence.

## 6. Alternative Sentinel Hub Service

`SentinelService` is a second satellite implementation based on the Sentinel Hub Python client rather than openEO.

It supports:

- NDVI imagery and statistics
- NDWI imagery and statistics
- True-color RGB imagery
- Available Sentinel-2 dates
- A simplified Sishen mining boundary

This implementation generates base64-encoded PNG images for display and uses Sentinel Hub evalscripts to calculate indices.

It is used by `backend/app/routers/satellite.py`, but that router is not registered in the current `main.py`. Consequently, these routes are not reachable through the shown primary application unless another entry point registers them.

## 7. Mock Backend

`backend/app/main_simple.py` is an older demonstration API.

It returns randomly generated values for:

- NDVI
- Solar conditions
- Mining applications
- Combined analysis

Its endpoints are:

```text
GET /api/data/ndvi
GET /api/data/solar
GET /api/data/mining-applications
GET /api/data/combined-analysis
```

These responses are explicitly marked as mock data and do not represent live satellite, solar, or mining information.

When run directly, this application uses port `8001`.

## 8. Solar Analysis

`PowerService` integrates with the NASA POWER API at:

```text
https://power.larc.nasa.gov/api
```

It can retrieve daily values for:

- Surface solar radiation
- Two-meter temperature
- Precipitation
- Two-meter wind speed
- Relative humidity
- Longwave radiation

It calculates period-level mean, minimum, maximum, and raw values.

The solar suitability score is calculated from mean daily solar radiation:

```text
score = min(100, (mean solar radiation / 7) * 100)
```

Hourly solar data is also supported, including hourly values, peak hour, and total daily radiation.

## 9. Mining and GIS Integration

`MiningService` connects to DPME ArcGIS REST services.

It is designed to retrieve:

- Mining areas
- Degraded land
- Sishen geology

The mining-area response is converted/requested as GeoJSON. Missing feature names and types receive default values.

The map component is prepared to display these features as orange polygon fills and outlines using MapLibre GL.

## 10. Map Component

`frontend/src/components/Map.jsx` contains a separate map-oriented interface.

It:

1. Creates a MapLibre map centered on Sishen/Kathu.
2. Loads a public MapLibre demonstration style.
3. Requests mining areas after the map loads.
4. Adds mining GeoJSON as a fill and line layer.
5. Provides controls for NDVI, solar data, and combined analysis.
6. Displays basic NDVI and solar result panels.

This component is not rendered by the current `App.jsx`, so the active application does not currently show the map.

## 11. Prefetched Data

`backend/prefetch_northern_cape.py` is a batch utility intended to fetch NDVI and NDWI data once and save it locally.

It writes:

```text
backend/data/northern_cape/ndvi_data.json
backend/data/northern_cape/ndvi_stats.json
backend/data/northern_cape/ndwi_data.json
backend/data/northern_cape/ndwi_stats.json
backend/data/northern_cape/summary.json
```

The existing summary identifies the region as Northern Cape and the area as Sishen/Kathu. The stored NDVI statistics currently show:

- Mean: approximately `0.264`
- Minimum: approximately `-0.026`
- Maximum: approximately `0.586`
- Raster shape: `223 x 206`

The current `SatelliteService` does not read these JSON files. Its request methods perform new openEO downloads.

## 12. Database and Storage Design

`database.py` defines two SQLAlchemy database connections:

- PostgreSQL/PostGIS for GIS and site data
- TimescaleDB for IoT time-series data

The models in `site_models.py` are:

### Site

Stores a named polygon site, description, center coordinates, timestamps, and JSON metadata.

### LandAnalysis

Stores analysis scores for solar, agriculture, environment, community, and infrastructure, together with recommendations.

### SatelliteData

Stores satellite type, acquisition date, band metadata, files, and geometry columns for NDVI and NDWI.

`docker-compose.yml` provisions:

- PostGIS PostgreSQL on port `5432`
- TimescaleDB on port `5433`
- MinIO object storage on ports `9000` and `9001`

These services establish infrastructure for future functionality, but the current active routes do not create tables, persist analyses, or use MinIO for uploads.

## 13. Configuration

`config.py` loads environment variables for:

- PostgreSQL
- TimescaleDB
- MinIO
- Sentinel Hub credentials
- Study-area coordinates

Default local database and MinIO credentials are present for development. Production deployments should replace them with secrets supplied through the environment.

## 14. Tests and Utility Scripts

The backend contains two executable integration-style scripts:

- `test_openeo.py`: Connects to Copernicus openEO, downloads NDVI, and prints raster statistics.
- `test_sentinel.py`: Connects to Sentinel Hub, requests NDVI, and prints statistics.

These are manual verification scripts rather than automated tests. They do not use assertions or a test framework.

The backend Python files compile successfully, and the frontend production build succeeds.

## 15. Current Readiness Issues

The following issues currently prevent the repository from behaving as one coherent application:

1. `main.py` calls `is_cached()`, `get_cached_ndvi()`, and `get_cached_ndwi()`, but these methods are absent from `SatelliteService`.
2. The frontend uses port `8002`, while `main.py` starts on port `8000`.
3. The Vite proxy points to port `8000`, but absolute frontend URLs bypass that proxy.
4. The `openeo` package is used but is not listed in `requirements.txt`.
5. `sentinelhub` and Pillow are used by the alternative service but are not listed in `requirements.txt`.
6. The satellite router is not registered with the primary FastAPI application.
7. The active frontend does not render the map.
8. Dashboard and upload components are empty.
9. Prefetched data exists but is not consumed by the active service.
10. Database and MinIO infrastructure exists but is not connected to active business routes.
11. There is no implemented AI or machine-learning model yet.
12. `test_sentinel.py` contains Sentinel Hub credentials directly in source code. Those credentials should be revoked and replaced with environment variables.
13. The default satellite dates are fixed to August 2026 and should eventually be validated against available imagery.

## 16. End-to-End Status

The intended end-to-end path is:

```text
React interface
  -> FastAPI request
  -> Copernicus openEO
  -> Sentinel-2 data
  -> NDVI/NDWI calculation
  -> GeoTIFF download
  -> Raster statistics
  -> JSON response
  -> React result card
```

This path is represented in the code, but the current port mismatch, missing cache methods, and missing dependency declarations must be resolved before it can reliably run from a clean environment.

Overall, MineLand Nexus is a promising but incomplete prototype. Satellite index analysis is the clearest working feature, while mapping, solar analysis, mining GIS, persistence, uploads, IoT, and AI analysis are prepared as partially implemented extensions rather than a finished unified product.
