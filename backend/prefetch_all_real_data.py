"""
Pre-fetch ALL real data sources for Northern Cape
Run this once to cache all real data
"""
import os
import json
import sys
from datetime import datetime

# Add app to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.satellite_service import SatelliteService
from app.services.nasa_service import NASAService
from app.services.mining_service import MiningService
from app.services.community_service import CommunityService
from app.services.infrastructure_service import InfrastructureService
from app.services.dem_service import DEMService
from app.services.landcover_service import LandCoverService
from app.services.protected_service import ProtectedAreasService
from app.services.climate_service import ClimateService

class RealDataPreFetcher:
    def __init__(self):
        self.data_dir = "data/cached_real_data"
        os.makedirs(self.data_dir, exist_ok=True)

        # Initialize all services
        self.satellite = SatelliteService()
        self.nasa = NASAService()
        self.mining = MiningService()
        self.community = CommunityService()
        self.infrastructure = InfrastructureService()
        self.dem = DEMService()
        self.landcover = LandCoverService()
        self.protected = ProtectedAreasService()
        self.climate = ClimateService()

    def fetch_and_cache(self):
        """Fetch all real data and cache it"""
        print("🚀 Pre-fetching ALL real data for Northern Cape...\n")
        print("📍 Location: Sishen/Kathu - Northern Cape\n")

        results = {}

        # 1. Satellite Data (NDVI, NDWI)
        print("📡 Fetching Satellite Data (Sentinel-2)...")
        try:
            results["satellite"] = self.satellite.get_ndvi(use_cache=False)
            print("   ✅ NDVI fetched")
            results["ndwi"] = self.satellite.get_ndwi(use_cache=False)
            print("   ✅ NDWI fetched")
        except Exception as e:
            print(f"   ❌ Satellite error: {e}")
            results["satellite"] = {"status": "error", "message": str(e)}

        # 2. Solar Data (NASA POWER)
        print("\n☀️ Fetching Solar Data (NASA POWER)...")
        try:
            results["solar"] = self.nasa.get_solar_data()
            print("   ✅ Solar data fetched")
        except Exception as e:
            print(f"   ❌ Solar error: {e}")
            results["solar"] = {"status": "error", "message": str(e)}

        # 3. Mining Data (DPME GIS)
        print("\n⛏️ Fetching Mining Data (DPME GIS)...")
        try:
            results["mining"] = self.mining.get_mining_areas()
            print("   ✅ Mining areas fetched")
            results["degraded_land"] = self.mining.get_degraded_land()
            print("   ✅ Degraded land fetched")
        except Exception as e:
            print(f"   ❌ Mining error: {e}")
            results["mining"] = {"status": "error", "message": str(e)}

        # 4. Community Data (OpenStreetMap)
        print("\n👥 Fetching Community Data (OSM)...")
        try:
            results["community"] = self.community.get_community_data()
            print("   ✅ Community data fetched")
        except Exception as e:
            print(f"   ❌ Community error: {e}")
            results["community"] = {"status": "error", "message": str(e)}

        # 5. Infrastructure Data (Eskom GIS)
        print("\n🏗️ Fetching Infrastructure Data (Eskom)...")
        try:
            results["infrastructure"] = self.infrastructure.get_substations()
            print("   ✅ Infrastructure data fetched")
        except Exception as e:
            print(f"   ❌ Infrastructure error: {e}")
            results["infrastructure"] = {"status": "error", "message": str(e)}

        # 6. DEM Data (Copernicus DEM)
        print("\n🏔️ Fetching DEM Data (Copernicus)...")
        try:
            results["dem"] = self.dem.get_dem_data()
            print("   ✅ DEM data fetched")
        except Exception as e:
            print(f"   ❌ DEM error: {e}")
            results["dem"] = {"status": "error", "message": str(e)}

        # 7. Land Cover Data (SANLC 2022)
        print("\n🌿 Fetching Land Cover Data (SANLC 2022)...")
        try:
            results["landcover"] = self.landcover.get_landcover()
            print("   ✅ Land cover data fetched")
        except Exception as e:
            print(f"   ❌ Land cover error: {e}")
            results["landcover"] = {"status": "error", "message": str(e)}

        # 8. Protected Areas Data (SAPAD)
        print("\n🛡️ Fetching Protected Areas Data (SAPAD)...")
        try:
            results["protected"] = self.protected.get_protected_areas()
            print("   ✅ Protected areas fetched")
        except Exception as e:
            print(f"   ❌ Protected areas error: {e}")
            results["protected"] = {"status": "error", "message": str(e)}

        # 9. Climate Projections
        print("\n🌡️ Fetching Climate Projections...")
        try:
            results["climate"] = self.climate.get_climate_projections(5)
            print("   ✅ Climate projections fetched")
        except Exception as e:
            print(f"   ❌ Climate error: {e}")
            results["climate"] = {"status": "error", "message": str(e)}

        # Save all results
        cache_file = os.path.join(self.data_dir, "all_real_data.json")
        with open(cache_file, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "location": "Sishen/Kathu - Northern Cape",
                "data": results
            }, f, indent=2)

        print(f"\n✅ ALL data cached to: {cache_file}")
        print("\n📊 Summary:")
        for key, value in results.items():
            status = value.get("status", "unknown")
            print(f"   {key}: {status}")

        return results

if __name__ == "__main__":
    fetcher = RealDataPreFetcher()
    fetcher.fetch_and_cache()
