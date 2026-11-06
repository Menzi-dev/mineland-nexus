"""
NASA POWER Service - Northern Cape only
Fetches solar radiation, temperature, wind, and humidity data for Sishen/Kathu
"""
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import os
from dotenv import load_dotenv

load_dotenv()

class NASAService:
    def __init__(self):
        self.base_url = os.getenv('NASA_POWER_URL', 'https://power.larc.nasa.gov/api')
        # Northern Cape - Sishen/Kathu coordinates
        self.lat = -23.45
        self.lon = 27.45

    def get_solar_data(self, start_date: str = None, end_date: str = None) -> Dict:
        """
        Get solar radiation and meteorological data for Northern Cape
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')

        url = f"{self.base_url}/temporal/daily/point"

        params = {
            'parameters': 'ALLSKY_SFC_SW_DWN,T2M,WS10M,RH2M,PRECTOTCORR',
            'community': 'RE',  # Renewable Energy
            'longitude': self.lon,
            'latitude': self.lat,
            'start': start_date,
            'end': end_date,
            'format': 'JSON'
        }

        try:
            print(f"☀️ Fetching NASA POWER solar data for Northern Cape ({self.lat}, {self.lon})")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            # Parse the response
            properties = data.get('properties', {})
            parameter_data = properties.get('parameter', {})

            results = {
                "status": "success",
                "source": "NASA POWER",
                "location": {
                    "lat": self.lat,
                    "lon": self.lon,
                    "area": "Sishen/Kathu - Northern Cape"
                },
                "period": {"start": start_date, "end": end_date},
                "parameters": {}
            }

            param_names = {
                'ALLSKY_SFC_SW_DWN': 'solar_radiation',
                'T2M': 'temperature',
                'WS10M': 'wind_speed',
                'RH2M': 'humidity',
                'PRECTOTCORR': 'precipitation'
            }

            param_units = {
                'solar_radiation': 'kWh/m²/day',
                'temperature': '°C',
                'wind_speed': 'm/s',
                'humidity': '%',
                'precipitation': 'mm/day'
            }

            for param_key, param_name in param_names.items():
                if param_key in parameter_data:
                    values = [
                        value for value in parameter_data[param_key].values()
                        if isinstance(value, (int, float)) and value > -900
                    ]
                    if values:
                        results["parameters"][param_name] = {
                            "mean": round(sum(values) / len(values), 2),
                            "min": round(min(values), 2),
                            "max": round(max(values), 2),
                            "unit": param_units.get(param_name, ""),
                            "data_points": len(values)
                        }

            # Calculate solar suitability score (for Northern Cape)
            if 'solar_radiation' in results["parameters"]:
                solar_mean = results["parameters"]['solar_radiation']["mean"]
                # Score based on average daily solar radiation (kWh/m²/day)
                # Northern Cape: 5-7 kWh/m²/day is good
                solar_score = max(0, min(100, (solar_mean / 6.5) * 100))
                results["solar_suitability_score"] = round(solar_score, 2)
                results["solar_potential"] = "High" if solar_score > 75 else "Medium" if solar_score > 50 else "Low"

            print(f"✅ Solar data fetched successfully for Northern Cape")
            return results

        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "message": "NASA POWER API timeout - please try again"
            }
        except requests.exceptions.RequestException as e:
            print(f"❌ NASA POWER error: {e}")
            return {
                "status": "error",
                "message": f"API request failed: {str(e)}"
            }
        except Exception as e:
            print(f"❌ NASA POWER unexpected error: {e}")
            return {
                "status": "error",
                "message": f"Unexpected error: {str(e)}"
            }

    def get_solar_suitability(self) -> Dict:
        """
        Quick method to get just the solar suitability score for Northern Cape
        """
        result = self.get_solar_data()
        if result["status"] == "success":
            return {
                "status": "success",
                "location": "Sishen/Kathu - Northern Cape",
                "coordinates": {"lat": self.lat, "lon": self.lon},
                "solar_suitability_score": result.get("solar_suitability_score", 0),
                "solar_potential": result.get("solar_potential", "Unknown"),
                "daily_radiation": result["parameters"].get("solar_radiation", {}).get("mean", 0),
                "unit": "kWh/m²/day"
            }
        return {"status": "error", "message": "Could not fetch solar data"}
