"""
Climate Projections Service - Northern Cape
Provides future climate predictions based on IPCC models
"""
from typing import Dict
import requests
from datetime import datetime

class ClimateService:
    def __init__(self):
        self.latitude = -23.45
        self.longitude = 27.45
        self.base_url = "https://climate-api.open-meteo.com/v1/climate"
        self.models = ["EC_Earth3P_HR", "MPI_ESM1_2_XR"]

    def get_climate_projections(self, years_ahead: int = 5) -> Dict:
        """Get climate projections for Northern Cape"""

        target_year = datetime.now().year + years_ahead
        temperatures = []
        rainfall = []
        for model in self.models:
            response = requests.get(self.base_url, params={
                "latitude": self.latitude, "longitude": self.longitude,
                "start_date": f"{datetime.now().year - 5}-01-01",
                "end_date": f"{target_year}-12-31",
                "models": model,
                "daily": "temperature_2m_mean,precipitation_sum",
                "timezone": "GMT",
            }, timeout=20)
            response.raise_for_status()
            daily = response.json().get("daily", {})
            temperatures.extend(value for value in daily.get("temperature_2m_mean", []) if value is not None)
            rainfall.extend(value for value in daily.get("precipitation_sum", []) if value is not None)
        if not temperatures or not rainfall:
            raise ValueError("Open-Meteo returned no climate observations")
        baseline_count = min(len(temperatures), 365 * 5)
        baseline_temperature = sum(temperatures[:baseline_count]) / baseline_count
        baseline_rainfall = sum(rainfall[:baseline_count]) / 5
        future_temperature = sum(temperatures[-365:]) / min(365, len(temperatures))
        future_rainfall = sum(rainfall[-365:])
        temperature_change = future_temperature - baseline_temperature
        rainfall_change = ((future_rainfall - baseline_rainfall) / baseline_rainfall * 100) if baseline_rainfall else 0

        return {
            "status": "success",
            "location": "Northern Cape, South Africa",
            "coordinates": {"lat": self.latitude, "lon": self.longitude},
            "years_ahead": years_ahead,
            "scenario": "Open-Meteo climate model ensemble",
            "current": {
                "temperature": round(baseline_temperature, 1),
                "rainfall": round(baseline_rainfall, 1)
            },
            "predicted": {
                "temperature": round(future_temperature, 1),
                "rainfall": round(future_rainfall, 1)
            },
            "changes": {
                "temperature": round(temperature_change, 1),
                "rainfall": round(rainfall_change, 1)
            },
            "timestamp": datetime.now().isoformat()
        }

    def get_climate_scenarios(self) -> Dict:
        """Get all climate scenarios"""
        return {
            "status": "success",
            "source": self.base_url,
            "models": self.models
        }
