"""
Pre-fetch Northern Cape satellite data and store in database
Run this once to cache the data
"""
import os
import sys
import json
import numpy as np
import rasterio
from datetime import datetime
import openeo
from dotenv import load_dotenv

# Add app to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.services.satellite_service import SatelliteService

# Load environment
load_dotenv()

class NorthernCapeDataPreFetcher:
    def __init__(self):
        self.service = SatelliteService()
        self.data_dir = "data/northern_cape"
        os.makedirs(self.data_dir, exist_ok=True)

    def fetch_and_save(self):
        """Fetch Northern Cape satellite data and save"""
        print("🚀 Pre-fetching Northern Cape satellite data...")
        print("📍 Area: Sishen/Kathu - Northern Cape")

        # Fetch NDVI
        print("\n📡 Fetching NDVI for Northern Cape...")
        ndvi_result = self.service.get_ndvi("2026-08-15", "2026-08-20")

        if ndvi_result["status"] == "success":
            # Save NDVI data
            ndvi_file = os.path.join(self.data_dir, "ndvi_data.json")
            with open(ndvi_file, "w") as f:
                json.dump(ndvi_result, f, indent=2)
            print(f"✅ NDVI data saved to {ndvi_file}")

            # Save statistics separately
            stats_file = os.path.join(self.data_dir, "ndvi_stats.json")
            with open(stats_file, "w") as f:
                json.dump(ndvi_result["statistics"], f, indent=2)
            print(f"✅ NDVI stats saved to {stats_file}")
        else:
            print(f"❌ NDVI fetch failed: {ndvi_result.get('message', 'Unknown error')}")

        # Fetch NDWI
        print("\n📡 Fetching NDWI for Northern Cape...")
        ndwi_result = self.service.get_ndwi("2026-08-15", "2026-08-20")

        if ndwi_result["status"] == "success":
            # Save NDWI data
            ndwi_file = os.path.join(self.data_dir, "ndwi_data.json")
            with open(ndwi_file, "w") as f:
                json.dump(ndwi_result, f, indent=2)
            print(f"✅ NDWI data saved to {ndwi_file}")

            # Save statistics separately
            stats_file = os.path.join(self.data_dir, "ndwi_stats.json")
            with open(stats_file, "w") as f:
                json.dump(ndwi_result["statistics"], f, indent=2)
            print(f"✅ NDWI stats saved to {stats_file}")
        else:
            print(f"❌ NDWI fetch failed: {ndwi_result.get('message', 'Unknown error')}")

        # Create summary
        summary = {
            "province": "Northern Cape",
            "area": "Sishen/Kathu",
            "coordinates": {
                "west": 27.45,
                "east": 27.55,
                "south": -23.50,
                "north": -23.40
            },
            "fetch_date": datetime.now().isoformat(),
            "data_sources": {
                "ndvi": "Sentinel-2 L2A",
                "ndwi": "Sentinel-2 L2A"
            },
            "status": "pre-fetched"
        }

        summary_file = os.path.join(self.data_dir, "summary.json")
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"\n✅ Summary saved to {summary_file}")

        print("\n🎉 Pre-fetch complete! Data is ready for use.")

if __name__ == "__main__":
    fetcher = NorthernCapeDataPreFetcher()
    fetcher.fetch_and_save()
