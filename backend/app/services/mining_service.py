"""
Mining Data Service - DPME GIS Integration
Fetches mining boundaries, degraded land, geology, and soils
"""
import requests
import geopandas as gpd
from typing import Dict, List, Optional
from shapely.geometry import box

class MiningService:
    def __init__(self):
        # DPME GIS Service URLs
        self.base_url = "https://dpmegis.dpme.gov.za/arcgis/rest/services"
        # Northern Cape - Sishen/Kathu bounds
        self.bbox = {
            "west": 27.45,
            "east": 27.55,
            "south": -23.50,
            "north": -23.40
        }
        self.bbox_str = f"{27.45},{23.50},{27.55},{23.40}"

    def get_mining_areas(self) -> Dict:
        """Get mining areas from DPME GIS"""
        url = f"{self.base_url}/Hosted/service_be328c9b172644d1923dbe44a6198593/FeatureServer/0/query"

        params = {
            'where': '1=1',
            'outFields': '*',
            'f': 'geojson',
            'outSR': '4326',
            'geometry': self.bbox_str,
            'geometryType': 'esriGeometryEnvelope'
        }

        try:
            response = requests.get(url, params=params, timeout=12)
            response.raise_for_status()
            data = response.json()

            features = data.get('features', [])

            # Calculate mining impact score
            mining_score = min(100, 50 + len(features) * 2)

            return {
                "status": "success",
                "source": "DPME GIS",
                "total_features": len(features),
                "mining_impact_score": mining_score,
                "mining_present": len(features) > 0,
                "data": data
            }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "mining_present": True,  # Sishen is a mining area
                "mining_impact_score": 70
            }

    def get_degraded_land(self) -> Dict:
        """Get degraded land data"""
        url = f"{self.base_url}/DPME_EnterpriseSQL_GDB/Demographics/MapServer/0/query"

        params = {
            'where': '1=1',
            'outFields': '*',
            'f': 'geojson',
            'outSR': '4326',
            'geometry': self.bbox_str,
            'geometryType': 'esriGeometryEnvelope'
        }

        try:
            response = requests.get(url, params=params, timeout=12)
            response.raise_for_status()
            data = response.json()

            features = data.get('features', [])

            # Degraded land extent
            degraded_score = min(100, 30 + len(features) * 5)

            return {
                "status": "success",
                "source": "DPME GIS",
                "total_features": len(features),
                "degraded_score": degraded_score,
                "data": data
            }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "degraded_score": 60  # Mining area - degraded
            }

    def get_geology(self) -> Dict:
        """Get geology data"""
        url = f"{self.base_url}/DPME_EnterpriseSQL_GDB/Geology/MapServer/0/query"

        params = {
            'where': '1=1',
            'outFields': '*',
            'f': 'geojson',
            'outSR': '4326',
            'geometry': self.bbox_str,
            'geometryType': 'esriGeometryEnvelope'
        }

        try:
            response = requests.get(url, params=params, timeout=12)
            response.raise_for_status()
            data = response.json()

            return {
                "status": "success",
                "source": "DPME GIS",
                "geology_present": True,
                "data": data
            }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "geology_present": True
            }
