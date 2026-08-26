from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import random

app = FastAPI(
    title="MineLand Nexus API",
    description="AI-powered rural landscape intelligence platform",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data endpoints
@app.get("/")
async def root():
    return {
        "message": "MineLand Nexus API v2",
        "status": "running",
        "data_sources": [
            "Mock Data (Sentinel-2, NASA POWER, DMPR Mining)",
            "Ready for real data integration"
        ],
        "endpoints": [
            "/api/data/ndvi",
            "/api/data/solar",
            "/api/data/mining-applications",
            "/api/data/combined-analysis"
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/data/ndvi")
async def get_ndvi():
    """Get mock NDVI data"""
    return {
        "status": "success",
        "date": datetime.now().strftime('%Y-%m-%d'),
        "ndvi_mean": round(random.uniform(0.1, 0.5), 3),
        "ndvi_min": round(random.uniform(-0.2, 0.1), 3),
        "ndvi_max": round(random.uniform(0.5, 0.8), 3),
        "source": "mock",
        "note": "Mock data - install sentinelhub for real data"
    }

@app.get("/api/data/solar")
async def get_solar():
    """Get mock solar data"""
    return {
        "status": "success",
        "location": {"lat": -23.45, "lon": 27.45},
        "solar_suitability_score": round(random.uniform(70, 95), 1),
        "parameters": {
            "solar_radiation": {
                "mean": round(random.uniform(5.0, 7.5), 2),
                "min": round(random.uniform(3.0, 5.0), 2),
                "max": round(random.uniform(8.0, 10.0), 2),
                "unit": "kWh/m²/day"
            },
            "temperature": {
                "mean": round(random.uniform(22, 32), 2),
                "min": round(random.uniform(12, 20), 2),
                "max": round(random.uniform(35, 42), 2),
                "unit": "°C"
            }
        },
        "source": "mock"
    }

@app.get("/api/data/mining-applications")
async def get_mining_applications():
    """Get mock mining data"""
    return {
        "status": "success",
        "total_features": 15,
        "data": {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [27.4, -23.5],
                            [27.55, -23.5],
                            [27.55, -23.38],
                            [27.4, -23.38],
                            [27.4, -23.5]
                        ]]
                    },
                    "properties": {
                        "name": "Sishen Mine",
                        "type": "mining"
                    }
                }
            ]
        },
        "source": "mock"
    }

@app.get("/api/data/combined-analysis")
async def get_combined_analysis():
    """Get combined mock analysis"""
    return {
        "status": "success",
        "area": "Sishen/Kathu",
        "ndvi": {
            "ndvi_mean": round(random.uniform(0.1, 0.5), 3)
        },
        "solar": {
            "solar_suitability_score": round(random.uniform(70, 95), 1)
        },
        "mining": {
            "total_features": 15
        },
        "timestamp": datetime.now().isoformat(),
        "source": "mock"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)