import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import json

class PowerService:
    def __init__(self):
        self.base_url = "https://power.larc.nasa.gov/api"
        
    def get_solar_data(self, lat: float = -23.45, lon: float = 27.45, 
                       start_date: str = None, end_date: str = None) -> Dict:
        """
        Get solar radiation and meteorological data from NASA POWER
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        
        parameters = [
            'ALLSKY_SFC_SW_DWN',  # Solar radiation
            'T2M',                # Temperature at 2m
            'PRECTOT',            # Precipitation
            'WS2M',               # Wind speed at 2m
            'RH2M',               # Relative humidity
            'ALLSKY_SFC_LW_DWN',  # Longwave radiation
        ]
        
        url = f"{self.base_url}/temporal/daily/point"
        
        params = {
            'parameters': ','.join(parameters),
            'community': 'RE',  # Renewable Energy
            'longitude': lon,
            'latitude': lat,
            'start': start_date,
            'end': end_date,
            'format': 'JSON'
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Extract time series
            properties = data['properties']
            parameter_data = properties['parameter']
            
            # Calculate averages for the period
            results = {
                "status": "success",
                "location": {"lat": lat, "lon": lon},
                "period": {"start": start_date, "end": end_date},
                "parameters": {}
            }
            
            for param in parameters:
                if param in parameter_data:
                    values = list(parameter_data[param].values())
                    results["parameters"][param] = {
                        "mean": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values),
                        "values": values
                    }
            
            # Calculate solar suitability score
            if 'ALLSKY_SFC_SW_DWN' in results["parameters"]:
                solar_mean = results["parameters"]['ALLSKY_SFC_SW_DWN']["mean"]
                # Score based on average daily solar radiation (kWh/m²/day)
                # Typical good solar: 5-7 kWh/m²/day
                solar_score = min(100, (solar_mean / 7) * 100)
                results["solar_suitability_score"] = round(solar_score, 2)
            
            return results
            
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def get_hourly_solar(self, lat: float = -23.45, lon: float = 27.45, 
                         date: str = None) -> Dict:
        """
        Get hourly solar radiation for a specific date
        """
        if not date:
            date = datetime.now().strftime('%Y%m%d')
            
        url = f"{self.base_url}/temporal/hourly/point"
        
        params = {
            'parameters': 'ALLSKY_SFC_SW_DWN',
            'community': 'RE',
            'longitude': lon,
            'latitude': lat,
            'start': date,
            'end': date,
            'format': 'JSON'
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Extract hourly values
            properties = data['properties']
            parameter_data = properties['parameter']
            
            if 'ALLSKY_SFC_SW_DWN' in parameter_data:
                hours = []
                values = []
                for hour_key, value in parameter_data['ALLSKY_SFC_SW_DWN'].items():
                    hours.append(hour_key)
                    values.append(value)
                
                return {
                    "status": "success",
                    "date": date,
                    "hours": hours,
                    "solar_values": values,
                    "peak_hour": max(values),
                    "total_daily": sum(values)
                }
            else:
                return {
                    "status": "error",
                    "message": "No solar data available for this date"
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": str(e)
            }