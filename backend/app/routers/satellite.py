from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta
from typing import Optional
from app.services.sentinel_service import SentinelService
from app.services.power_service import PowerService
from app.services.mining_service import MiningService

router = APIRouter(prefix="/api/satellite", tags=["satellite"])

sentinel_service = SentinelService()
power_service = PowerService()
mining_service = MiningService()

@router.get("/ndvi")
async def get_ndvi(date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format")):
    """Get NDVI for Sishen/Kathu area"""
    if date:
        try:
            dt = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        dt = datetime.now() - timedelta(days=1)
    
    result = sentinel_service.get_ndvi(dt)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@router.get("/ndwi")
async def get_ndwi(date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format")):
    """Get NDWI for Sishen/Kathu area"""
    if date:
        try:
            dt = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        dt = datetime.now() - timedelta(days=1)
    
    result = sentinel_service.get_ndwi(dt)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@router.get("/true-color")
async def get_true_color(date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format")):
    """Get true color image for Sishen/Kathu area"""
    if date:
        try:
            dt = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        dt = datetime.now() - timedelta(days=1)
    
    result = sentinel_service.get_true_color(dt)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@router.get("/available-dates")
async def get_available_dates(days_back: int = Query(30, description="Days to look back")):
    """Get available Sentinel-2 dates"""
    dates = sentinel_service.get_available_dates(days_back)
    return {"status": "success", "dates": dates}

@router.get("/solar")
async def get_solar_data(lat: float = -23.45, lon: float = 27.45):
    """Get NASA POWER solar data"""
    result = power_service.get_solar_data(lat, lon)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@router.get("/hourly-solar")
async def get_hourly_solar(lat: float = -23.45, lon: float = 27.45, 
                           date: Optional[str] = Query(None, description="Date in YYYYMMDD format")):
    """Get hourly solar data"""
    result = power_service.get_hourly_solar(lat, lon, date)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@router.get("/mining-areas")
async def get_mining_areas():
    """Get mining areas from DPME GIS"""
    result = mining_service.get_mining_areas()
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@router.get("/sishen-boundary")
async def get_sishen_boundary():
    """Get Sishen study area boundary"""
    boundary = sentinel_service.get_sishen_boundary()
    return boundary

@router.get("/combined-analysis")
async def get_combined_analysis():
    """Get combined satellite and solar analysis for Sishen"""
    # Get latest NDVI
    ndvi_result = sentinel_service.get_ndvi(datetime.now() - timedelta(days=1))
    
    # Get solar data
    solar_result = power_service.get_solar_data()
    
    # Get mining areas
    mining_result = mining_service.get_mining_areas()
    
    # Combine results
    return {
        "status": "success",
        "area": "Sishen/Kathu",
        "ndvi": ndvi_result if ndvi_result["status"] == "success" else None,
        "solar": solar_result if solar_result["status"] == "success" else None,
        "mining": mining_result if mining_result["status"] == "success" else None,
        "timestamp": datetime.now().isoformat()
    }