import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sentinelhub import (
    SHConfig,
    BBox,
    CRS,
    SentinelHubRequest,
    MimeType,
    DataCollection,
    bbox_to_dimensions,
    DownloadRequest,
)
import numpy as np
from PIL import Image
import io
import base64
from app.config import settings

class SentinelService:
    def __init__(self):
        self.config = SHConfig()
        self.config.sh_client_id = os.getenv('SENTINEL_CLIENT_ID')
        self.config.sh_client_secret = os.getenv('SENTINEL_CLIENT_SECRET')
        
        # Sishen/Kathu area bounds
        self.sishen_bbox = BBox(
            bbox=[27.3, -23.6, 27.7, -23.3],  # [min_lon, min_lat, max_lon, max_lat]
            crs=CRS.WGS84
        )
        
    def get_ndvi(self, date: datetime) -> Dict:
        """
        Get NDVI for Sishen/Kathu area for a specific date
        """
        evalscript = """
        //VERSION=3
        function setup() {
            return {
                input: ["B04", "B08"],
                output: { bands: 1 }
            };
        }

        function evaluatePixel(sample) {
            let ndvi = (sample.B08 - sample.B04) / (sample.B08 + sample.B04);
            return [ndvi];
        }
        """
        
        request = SentinelHubRequest(
            evalscript=evalscript,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DataCollection.SENTINEL2_L2A,
                    time_interval=(date.strftime('%Y-%m-%d'), date.strftime('%Y-%m-%d')),
                    maxcc=0.15  # Max cloud coverage 15%
                )
            ],
            responses=[
                SentinelHubRequest.output_response('default', MimeType.TIFF)
            ],
            bbox=self.sishen_bbox,
            size=bbox_to_dimensions(self.sishen_bbox, 10),
            config=self.config
        )
        
        try:
            data = request.get_data()[0]
            ndvi_array = data[:, :, 0]
            
            # Convert to base64 for frontend display
            ndvi_normalized = ((ndvi_array + 1) * 127).astype(np.uint8)
            img = Image.fromarray(ndvi_normalized)
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return {
                "status": "success",
                "date": date.isoformat(),
                "ndvi": ndvi_array.tolist(),
                "ndvi_min": float(np.nanmin(ndvi_array)),
                "ndvi_max": float(np.nanmax(ndvi_array)),
                "ndvi_mean": float(np.nanmean(ndvi_array)),
                "image_base64": img_base64,
                "bbox": self.sishen_bbox.get_lower_left() + self.sishen_bbox.get_upper_right()
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def get_ndwi(self, date: datetime) -> Dict:
        """
        Get NDWI (Normalized Difference Water Index) for Sishen/Kathu area
        """
        evalscript = """
        //VERSION=3
        function setup() {
            return {
                input: ["B03", "B08"],
                output: { bands: 1 }
            };
        }

        function evaluatePixel(sample) {
            let ndwi = (sample.B03 - sample.B08) / (sample.B03 + sample.B08);
            return [ndwi];
        }
        """
        
        request = SentinelHubRequest(
            evalscript=evalscript,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DataCollection.SENTINEL2_L2A,
                    time_interval=(date.strftime('%Y-%m-%d'), date.strftime('%Y-%m-%d')),
                    maxcc=0.15
                )
            ],
            responses=[
                SentinelHubRequest.output_response('default', MimeType.TIFF)
            ],
            bbox=self.sishen_bbox,
            size=bbox_to_dimensions(self.sishen_bbox, 10),
            config=self.config
        )
        
        try:
            data = request.get_data()[0]
            ndwi_array = data[:, :, 0]
            
            # Convert to base64
            ndwi_normalized = ((ndwi_array + 1) * 127).astype(np.uint8)
            img = Image.fromarray(ndwi_normalized)
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return {
                "status": "success",
                "date": date.isoformat(),
                "ndwi": ndwi_array.tolist(),
                "ndwi_min": float(np.nanmin(ndwi_array)),
                "ndwi_max": float(np.nanmax(ndwi_array)),
                "ndwi_mean": float(np.nanmean(ndwi_array)),
                "image_base64": img_base64
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def get_true_color(self, date: datetime) -> Dict:
        """
        Get true color RGB image for Sishen/Kathu area
        """
        evalscript = """
        //VERSION=3
        function setup() {
            return {
                input: ["B02", "B03", "B04"],
                output: { bands: 3 }
            };
        }

        function evaluatePixel(sample) {
            return [sample.B04, sample.B03, sample.B02];
        }
        """
        
        request = SentinelHubRequest(
            evalscript=evalscript,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DataCollection.SENTINEL2_L2A,
                    time_interval=(date.strftime('%Y-%m-%d'), date.strftime('%Y-%m-%d')),
                    maxcc=0.15
                )
            ],
            responses=[
                SentinelHubRequest.output_response('default', MimeType.PNG)
            ],
            bbox=self.sishen_bbox,
            size=bbox_to_dimensions(self.sishen_bbox, 10),
            config=self.config
        )
        
        try:
            data = request.get_data()[0]
            # Normalize to 0-255 for display
            rgb = (data * 255).astype(np.uint8)
            img = Image.fromarray(rgb, 'RGB')
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return {
                "status": "success",
                "date": date.isoformat(),
                "image_base64": img_base64
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def get_available_dates(self, days_back: int = 30) -> List[str]:
        """
        Get available Sentinel-2 dates for the Sishen/Kathu area
        """
        from sentinelhub import SentinelHubCatalog, DataCollection
        
        catalog = SentinelHubCatalog(config=self.config)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        search = catalog.search(
            collection=DataCollection.SENTINEL2_L2A.value,
            bbox=self.sishen_bbox,
            time=(start_date.isoformat(), end_date.isoformat()),
            filter="eo:cloud_cover < 15",
            fields={
                'include': ['id', 'properties.datetime', 'properties.eo:cloud_cover'],
                'exclude': []
            },
            limit=50
        )
        
        dates = []
        for item in search:
            if 'datetime' in item['properties']:
                dates.append(item['properties']['datetime'])
        
        return dates

    def get_sishen_boundary(self) -> Dict:
        """
        Get the Sishen mining area boundary from available geojson or create one
        """
        # Simplified polygon for Sishen area (you should replace with actual mining boundary)
        return {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [27.45, -23.55],
                    [27.65, -23.55],
                    [27.65, -23.40],
                    [27.45, -23.40],
                    [27.45, -23.55]
                ]]
            },
            "properties": {
                "name": "Sishen Mine Area",
                "type": "mining"
            }
        }