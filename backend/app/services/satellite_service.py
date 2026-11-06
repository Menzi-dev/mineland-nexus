import os
import json
import numpy as np
import rasterio
from datetime import datetime
import openeo
from fastapi import HTTPException

class SatelliteService:
    def __init__(self):
        self.connection = None
        self.cache_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "data", "northern_cape")
        )
        # NORTHERN CAPE - Sishen/Kathu area only
        self.bbox = {
            "west": 27.45,
            "east": 27.55,
            "south": -23.50,
            "north": -23.40
        }

    def _connect(self):
        """Connect to openEO"""
        if not self.connection:
            self.connection = openeo.connect("https://openeo.dataspace.copernicus.eu/")
            self.connection.authenticate_oidc()
        return self.connection

    def get_ndvi(self, start_date=None, end_date=None, use_cache=False):
        """Get NDVI for Northern Cape - Sishen/Kathu area"""
        try:
            if use_cache:
                cached = self.get_cached_ndvi()
                if cached:
                    return cached
                return {
                    "status": "error",
                    "message": "No cached NDVI data found"
                }

            if not start_date:
                start_date = "2026-08-15"
            if not end_date:
                end_date = "2026-08-20"

            cached = self.get_cached_ndvi()
            if cached and cached.get("period") == {"start": start_date, "end": end_date}:
                cached["mode"] = "local-fallback"
                return cached

            connection = self._connect()

            # Load Sentinel-2 data for Northern Cape
            s2 = connection.load_collection(
                "SENTINEL2_L2A",
                spatial_extent=self.bbox,
                temporal_extent=[start_date, end_date],
                bands=["B04", "B08"]
            )

            # Force low resolution for speed
            s2_resampled = s2.resample_spatial(resolution=50)

            # Calculate NDVI
            ndvi = (s2_resampled.band("B08") - s2_resampled.band("B04")) / (s2_resampled.band("B08") + s2_resampled.band("B04"))

            # Download to temp file
            temp_file = "temp_ndvi.tif"
            ndvi.download(temp_file)

            # Read the file
            with rasterio.open(temp_file) as src:
                data = src.read(1)
                stats = {
                    "mean": float(np.nanmean(data)),
                    "min": float(np.nanmin(data)),
                    "max": float(np.nanmax(data)),
                    "shape": data.shape
                }

            # Clean up
            if os.path.exists(temp_file):
                os.remove(temp_file)

            return {
                "status": "success",
                "area": "Sishen/Kathu - Northern Cape",
                "province": "Northern Cape",
                "country": "South Africa",
                "period": {"start": start_date, "end": end_date},
                "statistics": stats,
                "timestamp": datetime.now().isoformat(),
                "source": "Copernicus Sentinel-2",
                "coordinates": self.bbox
            }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def get_ndwi(self, start_date=None, end_date=None, use_cache=False):
        """Get NDWI for Northern Cape - Sishen/Kathu area"""
        try:
            if use_cache:
                cached = self.get_cached_ndwi()
                if cached:
                    return cached
                return {
                    "status": "error",
                    "message": "No cached NDWI data found"
                }

            if not start_date:
                start_date = "2026-08-15"
            if not end_date:
                end_date = "2026-08-20"

            cached = self.get_cached_ndwi()
            if cached and cached.get("period") == {"start": start_date, "end": end_date}:
                cached["mode"] = "local-fallback"
                return cached

            connection = self._connect()

            # Load Sentinel-2 data for Northern Cape
            s2 = connection.load_collection(
                "SENTINEL2_L2A",
                spatial_extent=self.bbox,
                temporal_extent=[start_date, end_date],
                bands=["B03", "B08"]
            )

            # Force low resolution
            s2_resampled = s2.resample_spatial(resolution=50)

            # Calculate NDWI
            ndwi = (s2_resampled.band("B03") - s2_resampled.band("B08")) / (s2_resampled.band("B03") + s2_resampled.band("B08"))

            temp_file = "temp_ndwi.tif"
            ndwi.download(temp_file)

            with rasterio.open(temp_file) as src:
                data = src.read(1)
                stats = {
                    "mean": float(np.nanmean(data)),
                    "min": float(np.nanmin(data)),
                    "max": float(np.nanmax(data)),
                    "shape": data.shape
                }

            if os.path.exists(temp_file):
                os.remove(temp_file)

            return {
                "status": "success",
                "area": "Sishen/Kathu - Northern Cape",
                "province": "Northern Cape",
                "country": "South Africa",
                "period": {"start": start_date, "end": end_date},
                "statistics": stats,
                "timestamp": datetime.now().isoformat(),
                "source": "Copernicus Sentinel-2",
                "coordinates": self.bbox
            }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def _get_cached_index(self, filename):
        """Load a prefetched index result from the project data directory."""
        cache_file = os.path.join(self.cache_dir, filename)
        if not os.path.isfile(cache_file):
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as file:
                return json.load(file)
        except (OSError, json.JSONDecodeError):
            return None

    def get_cached_ndvi(self):
        return self._get_cached_index("ndvi_data.json")

    def get_cached_ndwi(self):
        return self._get_cached_index("ndwi_data.json")

    def is_cached(self):
        return self.get_cached_ndvi() is not None and self.get_cached_ndwi() is not None
