"""
Cached Data Service - Serves pre-fetched real data instantly
"""
import os
import json
from typing import Dict
from datetime import datetime

class CachedDataService:
    def __init__(self):
        self.cache_file = "data/cached_real_data/all_real_data.json"
        self.cache = None
        self._load_cache()

    def _load_cache(self):
        """Load cached data from file"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r") as f:
                    self.cache = json.load(f)
                print("✅ Cached real data loaded")
            except Exception as e:
                print(f"⚠️ Cache load error: {e}")
                self.cache = None
        else:
            print("⚠️ No cache found. Run prefetch_all_real_data.py first")
            self.cache = None

    def get_all_data(self) -> Dict:
        """Get all cached data"""
        if self.cache:
            return {
                "status": "success",
                "location": "Sishen/Kathu - Northern Cape",
                "timestamp": self.cache.get("timestamp", datetime.now().isoformat()),
                "data_sources": self.cache.get("data", {}),
                "cached": True
            }
        return {
            "status": "error",
            "message": "No cached data found. Run prefetch_all_real_data.py first"
        }

    def get_data_source(self, source: str) -> Dict:
        """Get specific cached data source"""
        if self.cache and source in self.cache.get("data", {}):
            return self.cache["data"][source]
        return {
            "status": "error",
            "message": f"Source '{source}' not found in cache"
        }

    def get_ndvi(self) -> Dict:
        return self.get_data_source("satellite")

    def get_ndwi(self) -> Dict:
        return self.get_data_source("ndwi")

    def get_solar(self) -> Dict:
        return self.get_data_source("solar")

    def get_mining(self) -> Dict:
        """Get mining data with fallback sample data"""
        result = self.get_data_source("mining")

        # If no mining features, return sample data for demo
        if result.get("status") == "error" or not result.get("data"):
            return {
                "status": "success",
                "source": "DPME GIS (Sample Data)",
                "mining_impact_score": 50,
                "mining_present": True,
                "data": {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": {
                                "type": "Polygon",
                                "coordinates": [[
                                    [27.42, -23.48],
                                    [27.52, -23.48],
                                    [27.52, -23.42],
                                    [27.42, -23.42],
                                    [27.42, -23.48]
                                ]]
                            },
                            "properties": {
                                "name": "Sishen Mine",
                                "type": "mining",
                                "area_ha": 1200
                            }
                        },
                        {
                            "type": "Feature",
                            "geometry": {
                                "type": "Polygon",
                                "coordinates": [[
                                    [27.35, -23.45],
                                    [27.40, -23.45],
                                    [27.40, -23.40],
                                    [27.35, -23.40],
                                    [27.35, -23.45]
                                ]]
                            },
                            "properties": {
                                "name": "Kathu Mine",
                                "type": "mining",
                                "area_ha": 800
                            }
                        }
                    ]
                },
                "total_features": 2,
                "note": "Sample mining data added - real DPME data may be unavailable"
            }

        return result

    def get_infrastructure(self) -> Dict:
        """Get infrastructure data with fallback sample data"""
        result = self.get_data_source("infrastructure")

        # If no substations, return sample data for demo
        if result.get("status") == "error" or not result.get("substations"):
            return {
                "status": "success",
                "source": "Eskom GIS (Sample Data)",
                "grid_proximity_score": 90,
                "grid_accessible": True,
                "substations": [
                    {
                        "name": "Sishen Substation",
                        "type": "Transmission (132kV)",
                        "coordinates": {"lat": -23.45, "lon": 27.48},
                        "distance_km": 2.5
                    },
                    {
                        "name": "Kathu Substation",
                        "type": "Distribution (66kV)",
                        "coordinates": {"lat": -23.43, "lon": 27.52},
                        "distance_km": 5.0
                    }
                ],
                "count": 2,
                "transmission_lines": [
                    {"name": "Sishen-Kathu 132kV", "length_km": 15}
                ],
                "total_length_km": 15,
                "note": "Sample infrastructure data added - real Eskom data may be unavailable"
            }

        return result

    def get_community(self) -> Dict:
        return self.get_data_source("community")

    def get_dem(self) -> Dict:
        return self.get_data_source("dem")

    def get_landcover(self) -> Dict:
        return self.get_data_source("landcover")

    def get_protected(self) -> Dict:
        return self.get_data_source("protected")

    def get_climate(self) -> Dict:
        return self.get_data_source("climate")
