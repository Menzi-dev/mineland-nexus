"""
Unified Data Service
Combines all data sources for comprehensive analysis
"""
from typing import Dict
from datetime import datetime
from app.services.mining_service import MiningService
from app.services.community_service import CommunityService
from app.services.infrastructure_service import InfrastructureService
from app.services.satellite_service import SatelliteService
from app.services.nasa_service import NASAService

class DataService:
    def __init__(self):
        self.mining = MiningService()
        self.community = CommunityService()
        self.infrastructure = InfrastructureService()
        self.satellite = SatelliteService()
        self.nasa = NASAService()

    def get_complete_analysis(self) -> Dict:
        """Get all data sources combined"""

        # Fetch all data
        mining_data = self.mining.get_mining_areas()
        degraded_data = self.mining.get_degraded_land()
        community_data = self.community.get_community_data()
        infrastructure_data = self.infrastructure.get_substations()
        ndvi_data = self.satellite.get_ndvi(use_cache=True)
        solar_data = self.nasa.get_solar_data()

        # Combined data
        return {
            "status": "success",
            "location": "Sishen/Kathu - Northern Cape",
            "timestamp": datetime.now().isoformat(),
            "data_sources": {
                "mining": mining_data,
                "degraded_land": degraded_data,
                "community": community_data,
                "infrastructure": infrastructure_data,
                "satellite": ndvi_data,
                "solar": solar_data
            },
            "summary": {
                "mining_present": mining_data.get("mining_present", False),
                "community_score": community_data.get("community_score", 0),
                "grid_access": infrastructure_data.get("grid_accessible", False),
                "solar_potential": solar_data.get("solar_suitability_score", 0),
                "degraded_score": degraded_data.get("degraded_score", 0)
            }
        }
