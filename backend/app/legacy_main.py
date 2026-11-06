from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
import time
import uvicorn

# Import routers
from app.routers import uploads

# Import all services
from app.services.satellite_service import SatelliteService
from app.services.nasa_service import NASAService
from app.services.suitability_service import SuitabilityService
from app.services.mining_service import MiningService
from app.services.community_service import CommunityService
from app.services.infrastructure_service import InfrastructureService
from app.services.trend_service import TrendService
from app.services.data_service import DataService
from app.services.dem_service import DEMService
from app.services.landcover_service import LandCoverService
from app.services.protected_service import ProtectedAreasService
from app.services.climate_service import ClimateService
from app.services.cached_data_service import CachedDataService

app = FastAPI(
    title="MineLand Nexus API",
    description="AI-powered rural landscape intelligence platform - Northern Cape",
    version="4.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize all services
satellite = SatelliteService()
nasa = NASAService()
suitability = SuitabilityService()
mining = MiningService()
community = CommunityService()
infrastructure = InfrastructureService()
trend = TrendService()
data_service = DataService()
dem_service = DEMService()
landcover_service = LandCoverService()
protected_service = ProtectedAreasService()
climate_service = ClimateService()
cached_data = CachedDataService()

# Include routers
app.include_router(uploads.router)

_analysis_cache = None
_analysis_cache_time = 0.0
_analysis_lock = Lock()

# ==================== ROOT & HEALTH ====================
@app.get("/")
async def root():
    return {
        "message": "MineLand Nexus API v4",
        "status": "running",
        "region": "Northern Cape, South Africa",
        "data_cached": cached_data.cache is not None,
        "data_sources": [
            "Sentinel-2 (NDVI, NDWI)",
            "NASA POWER (Solar, Weather)",
            "DPME GIS (Mining, Degraded Land, Geology)",
            "OpenStreetMap (Community, Roads)",
            "Eskom GIS (Substations, Grid)",
            "Copernicus DEM (Elevation, Slope)",
            "SANLC 2022 (Land Cover)",
            "SAPAD (Protected Areas)",
            "Climate Projections (Future)"
        ],
        "endpoints": {
            "satellite": [
                "/api/ndvi - Vegetation Health Index",
                "/api/ndwi - Water Presence Index"
            ],
            "solar": [
                "/api/solar - Solar Radiation Data",
                "/api/solar-suitability - Solar Suitability Score"
            ],
            "suitability": [
                "/api/suitability - All Land Suitability Scores",
                "/api/recommendation - Best Land Use Recommendation"
            ],
            "mining": [
                "/api/mining-areas - Mining Boundaries",
                "/api/degraded-land - Degraded Land Data",
                "/api/geology - Geology Data"
            ],
            "community": [
                "/api/community - Community Infrastructure Data",
                "/api/community/roads - Road Network"
            ],
            "infrastructure": [
                "/api/substations - Electricity Substations",
                "/api/transmission-lines - Transmission Lines"
            ],
            "terrain": [
                "/api/dem - Copernicus DEM (Elevation, Slope)"
            ],
            "landcover": [
                "/api/landcover - SANLC 2022 Land Cover"
            ],
            "protected": [
                "/api/protected-areas - Protected Areas (SAPAD)"
            ],
            "climate": [
                "/api/climate/projections - Climate Projections",
                "/api/climate/scenarios - Climate Scenarios"
            ],
            "trends": [
                "/api/trend/historical - Historical Trend Analysis",
                "/api/trend/future - Future Prediction",
                "/api/trend/full - Complete Timeline Analysis"
            ],
            "combined": [
                "/api/complete-data - All Data Sources Combined",
                "/api/comprehensive-recommendation - Full Recommendation"
            ],
            "cached_instant": [
                "/api/cached/all - ALL Data (Instant)",
                "/api/cached/ndvi - Cached NDVI (Instant)",
                "/api/cached/ndwi - Cached NDWI (Instant)",
                "/api/cached/solar - Cached Solar (Instant)",
                "/api/cached/mining - Cached Mining (Instant)",
                "/api/cached/community - Cached Community (Instant)",
                "/api/cached/infrastructure - Cached Infrastructure (Instant)",
                "/api/cached/dem - Cached DEM (Instant)",
                "/api/cached/landcover - Cached Land Cover (Instant)",
                "/api/cached/protected - Cached Protected Areas (Instant)",
                "/api/cached/climate - Cached Climate (Instant)"
            ]
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "region": "Northern Cape",
        "services": {
            "satellite": "active",
            "solar": "active",
            "mining": "active",
            "community": "active",
            "infrastructure": "active",
            "terrain": "active",
            "landcover": "active",
            "protected": "active",
            "climate": "active",
            "trends": "active",
            "cached_data": "active" if cached_data.cache else "empty"
        },
        "timestamp": datetime.now().isoformat()
    }

# ==================== CACHED REAL DATA ENDPOINTS (INSTANT) ====================
@app.get("/api/cached/all")
async def get_cached_all():
    """Get ALL cached real data (instant response)"""
    result = cached_data.get_all_data()
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@app.get("/api/cached/ndvi")
async def get_cached_ndvi():
    """Get cached NDVI data (instant)"""
    result = cached_data.get_ndvi()
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@app.get("/api/cached/ndwi")
async def get_cached_ndwi():
    """Get cached NDWI data (instant)"""
    result = cached_data.get_ndwi()
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@app.get("/api/cached/solar")
async def get_cached_solar():
    """Get cached solar data (instant)"""
    result = cached_data.get_solar()
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@app.get("/api/cached/mining")
async def get_cached_mining():
    """Get cached mining data (instant)"""
    result = cached_data.get_mining()
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@app.get("/api/cached/community")
async def get_cached_community():
    """Get cached community data (instant)"""
    result = cached_data.get_community()
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@app.get("/api/cached/infrastructure")
async def get_cached_infrastructure():
    """Get cached infrastructure data (instant)"""
    result = cached_data.get_infrastructure()
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@app.get("/api/cached/dem")
async def get_cached_dem():
    """Get cached DEM data (instant)"""
    result = cached_data.get_dem()
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@app.get("/api/cached/landcover")
async def get_cached_landcover():
    """Get cached land cover data (instant)"""
    result = cached_data.get_landcover()
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@app.get("/api/cached/protected")
async def get_cached_protected():
    """Get cached protected areas data (instant)"""
    result = cached_data.get_protected()
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@app.get("/api/cached/climate")
async def get_cached_climate():
    """Get cached climate data (instant)"""
    result = cached_data.get_climate()
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

# ==================== SATELLITE ENDPOINTS ====================
@app.get("/api/ndvi")
async def get_ndvi(
    start_date: str = Query("2026-08-15", description="Start date YYYY-MM-DD"),
    end_date: str = Query("2026-08-20", description="End date YYYY-MM-DD")
):
    """Get NDVI for Northern Cape"""
    result = satellite.get_ndvi(start_date, end_date)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@app.get("/api/ndwi")
async def get_ndwi(
    start_date: str = Query("2026-08-15", description="Start date YYYY-MM-DD"),
    end_date: str = Query("2026-08-20", description="End date YYYY-MM-DD")
):
    """Get NDWI for Northern Cape"""
    result = satellite.get_ndwi(start_date, end_date)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

# ==================== SOLAR ENDPOINTS ====================
@app.get("/api/solar")
async def get_solar():
    """Get NASA POWER solar data for Northern Cape"""
    result = nasa.get_solar_data()
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@app.get("/api/solar-suitability")
async def get_solar_suitability():
    """Get solar suitability score for Northern Cape"""
    result = nasa.get_solar_suitability()
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

# ==================== SUITABILITY & RECOMMENDATION ====================
def get_all_data():
    """Collect ALL data sources for comprehensive analysis"""
    global _analysis_cache, _analysis_cache_time
    with _analysis_lock:
        if _analysis_cache is not None and time.monotonic() - _analysis_cache_time < 30:
            return _analysis_cache

        jobs = {
            "satellite": lambda: satellite.get_ndvi(use_cache=True),
            "ndwi": lambda: satellite.get_ndwi(use_cache=True),
            "solar": nasa.get_solar_data,
            "mining": mining.get_mining_areas,
            "degraded_land": mining.get_degraded_land,
            "geology": mining.get_geology,
            "community": community.get_community_data,
            "infrastructure": infrastructure.get_substations,
            "dem": dem_service.get_dem_data,
            "landcover": landcover_service.get_landcover,
            "protected": protected_service.get_protected_areas,
            "climate": lambda: climate_service.get_climate_projections(5),
        }
        with ThreadPoolExecutor(max_workers=len(jobs)) as executor:
            futures = {name: executor.submit(job) for name, job in jobs.items()}
            result = {}
            for name, future in futures.items():
                try:
                    result[name] = future.result()
                except Exception as error:
                    result[name] = {"status": "error", "message": str(error)}
        _analysis_cache = result
        _analysis_cache_time = time.monotonic()
        return result

def get_comprehensive_result():
    """Get comprehensive suitability scores with ALL data"""
    data = get_all_data()
    trend_data = trend.analyze_trend(5)
    return suitability.calculate_comprehensive_scores(data, trend_data)

@app.get("/api/suitability")
async def get_suitability():
    """Get all land suitability scores with ALL data sources"""
    result = get_comprehensive_result()
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message", "Analysis failed"))
    return result

@app.get("/api/recommendation")
async def get_recommendation():
    """Get best land use recommendation with ALL data sources"""
    result = get_comprehensive_result()
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message", "Analysis failed"))
    return {
        "status": "success",
        "location": result.get("location", "Sishen/Kathu - Northern Cape"),
        "coordinates": result.get("coordinates", {"lat": -23.45, "lon": 27.45}),
        "recommendation": result.get("recommendation", "Battery Storage"),
        "recommendation_score": result.get("recommendation_score", 72.2),
        "reason": result.get("recommendation_reason", "Based on comprehensive analysis"),
        "all_scores": result.get("all_scores_sorted", []),
        "evidence": result.get("evidence", {}),
        "data_sources": result.get("data_sources", []),
        "timestamp": result.get("timestamp", datetime.now().isoformat())
    }

# ==================== MINING ENDPOINTS ====================
@app.get("/api/mining-areas")
async def get_mining_areas():
    """Get mining boundaries from DPME GIS"""
    result = mining.get_mining_areas()
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@app.get("/api/degraded-land")
async def get_degraded_land():
    """Get degraded land data"""
    result = mining.get_degraded_land()
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@app.get("/api/geology")
async def get_geology():
    """Get geology data"""
    result = mining.get_geology()
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

# ==================== COMMUNITY ENDPOINTS ====================
@app.get("/api/community")
async def get_community_data():
    """Get community infrastructure from OpenStreetMap"""
    result = community.get_community_data()
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@app.get("/api/community/roads")
async def get_roads():
    """Get road network data"""
    result = community.get_road_network()
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

# ==================== INFRASTRUCTURE ENDPOINTS ====================
@app.get("/api/substations")
async def get_substations():
    """Get electricity substation data"""
    result = infrastructure.get_substations()
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@app.get("/api/transmission-lines")
async def get_transmission_lines():
    """Get transmission line data"""
    result = infrastructure.get_transmission_lines()
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

# ==================== TERRAIN / DEM ENDPOINTS ====================
@app.get("/api/dem")
async def get_dem():
    """Get Copernicus DEM data for Northern Cape"""
    result = dem_service.get_dem_data()
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

# ==================== LAND COVER ENDPOINTS ====================
@app.get("/api/landcover")
async def get_landcover():
    """Get SANLC 2022 land cover data for Northern Cape"""
    result = landcover_service.get_landcover()
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

# ==================== PROTECTED AREAS ENDPOINTS ====================
@app.get("/api/protected-areas")
async def get_protected_areas():
    """Get protected areas data for Northern Cape"""
    result = protected_service.get_protected_areas()
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

# ==================== CLIMATE ENDPOINTS ====================
@app.get("/api/climate/projections")
async def get_climate_projections(
    years: int = Query(5, description="Years ahead for projection")
):
    """Get climate projections for Northern Cape"""
    result = climate_service.get_climate_projections(years)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@app.get("/api/climate/scenarios")
async def get_climate_scenarios():
    """Get all climate scenarios"""
    result = climate_service.get_climate_scenarios()
    return result

# ==================== TREND ANALYSIS ENDPOINTS ====================
@app.get("/api/trend/historical")
async def get_historical_trend():
    """Get historical trend analysis (past to present)"""
    result = trend.get_historical_comparison()
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@app.get("/api/trend/future")
async def get_future_trend(years: int = Query(5, description="Years ahead to predict")):
    """Get future prediction for given years ahead"""
    result = trend.analyze_trend(years)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@app.get("/api/trend/full")
async def get_full_trend_analysis(years: int = Query(5, description="Years ahead to predict")):
    """Get complete trend analysis (past, present, future)"""
    historical = trend.get_historical_comparison()
    future = trend.analyze_trend(years)

    return {
        "status": "success",
        "location": "Sishen/Kathu - Northern Cape",
        "past": historical,
        "future": future,
        "timestamp": datetime.now().isoformat()
    }

# ==================== COMBINED DATA ENDPOINT ====================
@app.get("/api/complete-data")
async def get_complete_data():
    """Get ALL data sources combined for comprehensive analysis"""
    result = data_service.get_complete_analysis()
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

# ==================== ALL DATA ENDPOINT ====================
@app.get("/api/all-data")
async def get_all_data_endpoint():
    """Get ALL data sources combined (may take time)"""

    # Get all data
    ndvi_data = satellite.get_ndvi(use_cache=True)
    solar_data = nasa.get_solar_data()
    mining_data = mining.get_mining_areas()
    community_data = community.get_community_data()
    infrastructure_data = infrastructure.get_substations()
    dem_data = dem_service.get_dem_data()
    landcover_data = landcover_service.get_landcover()
    protected_data = protected_service.get_protected_areas()
    climate_data = climate_service.get_climate_projections(5)

    return {
        "status": "success",
        "location": "Sishen/Kathu - Northern Cape",
        "timestamp": datetime.now().isoformat(),
        "data_sources": {
            "satellite": ndvi_data,
            "solar": solar_data,
            "mining": mining_data,
            "community": community_data,
            "infrastructure": infrastructure_data,
            "terrain": dem_data,
            "landcover": landcover_data,
            "protected_areas": protected_data,
            "climate": climate_data
        }
    }

# ==================== COMPREHENSIVE RECOMMENDATION ====================
@app.get("/api/comprehensive-recommendation")
async def get_comprehensive_recommendation(years: int = Query(5, description="Years ahead")):
    """Get comprehensive recommendation using ALL data sources"""

    data = get_all_data()
    mining_data = data.get("mining", {})
    community_data = data.get("community", {})
    infrastructure_data = data.get("infrastructure", {})
    ndvi_result = data.get("satellite", {})
    solar_result = data.get("solar", {})
    trend_result = trend.analyze_trend(years)
    dem_result = data.get("dem", {})
    landcover_result = data.get("landcover", {})
    protected_result = data.get("protected", {})
    climate_result = data.get("climate", {})

    # Extract scores with safe defaults
    mining_score = mining_data.get("mining_impact_score", 50)
    community_score = community_data.get("community_score", 40)
    grid_score = infrastructure_data.get("grid_proximity_score", 70)
    solar_score = solar_result.get("solar_suitability_score", 50)
    ndvi_value = ndvi_result.get("statistics", {}).get("mean", 0.25)
    flat_land_score = dem_result.get("suitability_factors", {}).get("flat_land_score", 70)
    vegetation_score = landcover_result.get("vegetation_score", 40)
    protection_score = protected_result.get("protection_score", 0)
    future_temperature = climate_result.get("predicted", {}).get("temperature", 29)

    # Future predictions
    future_mining = trend_result.get("predictions", {}).get("mining_extent_in_5_years", 60)
    future_ndvi = trend_result.get("predictions", {}).get("ndvi_in_5_years", 0.24)

    # Determine best use based on ALL factors
    scores = {
        "solar_energy": round(40 + (solar_score * 0.4) + (flat_land_score * 0.2), 1),
        "battery_storage": round(45 + (solar_score * 0.3) + (grid_score * 0.25) + (flat_land_score * 0.1), 1),
        "agriculture": round(20 + (ndvi_value * 150) + (vegetation_score * 0.2), 1),
        "grazing": round(30 + (ndvi_value * 120) + (vegetation_score * 0.15), 1),
        "conservation": round(25 + (ndvi_value * 140) + (vegetation_score * 0.2) - (mining_score * 0.2), 1),
        "mining_rehabilitation": round(60 + (mining_score * 0.3) - (ndvi_value * 50), 1),
        "community_development": round(30 + (community_score * 0.5) + (grid_score * 0.2), 1)
    }

    # Apply protection constraint
    if protection_score > 50:
        scores["conservation"] = min(100, scores["conservation"] + 20)
        scores["solar_energy"] = max(0, scores["solar_energy"] - 15)
        scores["mining_rehabilitation"] = max(0, scores["mining_rehabilitation"] - 10)

    # Get best recommendation
    best_use = max(scores, key=scores.get)
    best_score = scores[best_use]

    # Generate comprehensive reason
    reasons = {
        "solar_energy": f"High solar potential ({solar_score}%), flat terrain ({flat_land_score}%), grid accessible ({grid_score}%)",
        "battery_storage": f"Solar potential ({solar_score}%), grid access ({grid_score}%), flat terrain ({flat_land_score}%)",
        "agriculture": f"NDVI {ndvi_value:.3f}, vegetation score {vegetation_score}, limited water in arid climate",
        "grazing": f"Moderate vegetation (NDVI {ndvi_value:.3f}), vegetation score {vegetation_score}",
        "conservation": f"Vegetation score {vegetation_score}, protection score {protection_score}, rehabilitation potential",
        "mining_rehabilitation": f"Mining presence ({mining_score}%), future mining {future_mining}%, NDVI {ndvi_value:.3f}",
        "community_development": f"Community score {community_score}, grid access ({grid_score}%)"
    }

    return {
        "status": "success",
        "location": "Sishen/Kathu - Northern Cape",
        "years_ahead": years,
        "data_sources_used": [
            "Sentinel-2 (NDVI: {:.3f})".format(ndvi_value),
            "NASA POWER (Solar: {:.0f}%)".format(solar_score),
            "DPME GIS (Mining: {:.0f}%)".format(mining_score),
            "OpenStreetMap (Community: {:.0f}%)".format(community_score),
            "Eskom GIS (Grid: {:.0f}%)".format(grid_score),
            "Copernicus DEM (Flat land: {:.0f}%)".format(flat_land_score),
            "SANLC 2022 (Vegetation: {:.0f}%)".format(vegetation_score),
            "SAPAD (Protection: {:.0f}%)".format(protection_score),
            "Climate Projections (Temperature: {:.1f}°C)".format(future_temperature)
        ],
        "comprehensive_scores": scores,
        "recommendation": best_use.replace("_", " ").title(),
        "recommendation_score": best_score,
        "reason": reasons.get(best_use, "Based on comprehensive analysis"),
        "future_outlook": {
            "future_mining_extent": future_mining,
            "future_vegetation": "improving" if future_ndvi > ndvi_value else "declining",
            "future_temperature": future_temperature,
            "climate_impact": trend_result.get("climate_impact", {})
        },
        "evidence": {
            "ndvi": ndvi_value,
            "solar_radiation": solar_result.get("parameters", {}).get("solar_radiation", {}).get("mean", 5.33),
            "mining_impact": mining_score,
            "grid_access": grid_score,
            "community_access": community_score,
            "flat_land": flat_land_score,
            "vegetation_cover": vegetation_score,
            "protection_status": protection_score
        },
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
