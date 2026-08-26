import requests
import geopandas as gpd
from shapely.geometry import shape, Polygon
from typing import Dict, List, Optional, Any
import json

class MiningService:
    def __init__(self):
        # DPME GIS Service URL
        self.base_url = "https://dpmegis.dpme.gov.za/arcgis/rest/services"
        
    def get_mining_areas(self, limit: int = 1000) -> Dict:
        """
        Get mining areas from DPME GIS service
        """
        url = f"{self.base_url}/Hosted/service_be328c9b172644d1923dbe44a6198593/FeatureServer/0/query"
        
        params = {
            'where': '1=1',
            'outFields': '*',
            'f': 'geojson',
            'outSR': '4326',
            'resultRecordCount': limit
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Filter to Sishen/Kathu area if possible
            # For demo, we'll keep all and filter in code
            features = data.get('features', [])
            
            # Add names to features if missing
            for feature in features:
                properties = feature.get('properties', {})
                if 'name' not in properties:
                    properties['name'] = f"Mining Area {feature.get('id', 'unknown')}"
                if 'type' not in properties:
                    properties['type'] = 'mining'
            
            return {
                "status": "success",
                "total_features": len(features),
                "data": data
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def get_degraded_land(self) -> Dict:
        """
        Get degraded land data
        """
        url = f"{self.base_url}/DPME_EnterpriseSQL_GDB/Demographics/MapServer/0/query"
        
        params = {
            'where': '1=1',
            'outFields': '*',
            'f': 'geojson',
            'outSR': '4326'
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return {
                "status": "success",
                "data": response.json()
            }
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def get_sishen_geology(self) -> Dict:
        """
        Get simplified geology data for Sishen area
        """
        url = f"{self.base_url}/DPME_EnterpriseSQL_GDB/Geology/MapServer/0/query"
        
        params = {
            'where': "1=1",
            'outFields': '*',
            'f': 'geojson',
            'outSR': '4326',
            'geometry': '27.45, -23.55, 27.65, -23.40',
            'geometryType': 'esriGeometryEnvelope'
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return {
                "status": "success",
                "data": response.json()
            }
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": str(e)
            }