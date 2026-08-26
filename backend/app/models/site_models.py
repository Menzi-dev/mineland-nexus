from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text
from sqlalchemy.dialects.postgresql import GEOMETRY
from geoalchemy2 import Geometry
from datetime import datetime
from app.database import Base

class Site(Base):
    __tablename__ = "sites"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    location = Column(Geometry('POLYGON', srid=4326))
    center_lat = Column(Float)
    center_lon = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata_json = Column(JSON)

class LandAnalysis(Base):
    __tablename__ = "land_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, nullable=False)
    analysis_type = Column(String(50))  # suitability, risk, change
    solar_score = Column(Float)
    agricultural_score = Column(Float)
    environmental_score = Column(Float)
    community_score = Column(Float)
    infrastructure_score = Column(Float)
    recommendations = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class SatelliteData(Base):
    __tablename__ = "satellite_data"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, nullable=False)
    satellite_type = Column(String(20))  # SENTINEL_2, SENTINEL_1, SENTINEL_5P
    acquisition_date = Column(DateTime)
    band_info = Column(JSON)
    ndvi = Column(Geometry('POLYGON', srid=4326), nullable=True)
    ndwi = Column(Geometry('POLYGON', srid=4326), nullable=True)
    file_path = Column(String(500))
    metadata_json = Column(JSON)