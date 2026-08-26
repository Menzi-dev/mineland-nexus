from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.database import pg_engine, Base
from app.routers import satellite

# Create tables
Base.metadata.create_all(bind=pg_engine)

app = FastAPI(
    title="MineLand Nexus API",
    description="AI-powered rural landscape intelligence platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(satellite.router)

@app.get("/")
async def root():
    return {
        "message": "MineLand Nexus API",
        "status": "running",
        "version": "1.0.0",
        "endpoints": [
            "/api/satellite/ndvi",
            "/api/satellite/ndwi",
            "/api/satellite/true-color",
            "/api/satellite/available-dates",
            "/api/satellite/solar",
            "/api/satellite/hourly-solar",
            "/api/satellite/mining-areas",
            "/api/satellite/sishen-boundary",
            "/api/satellite/combined-analysis"
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )