import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Database
    postgres_host: str = os.getenv('POSTGRES_HOST', 'localhost')
    postgres_port: int = int(os.getenv('POSTGRES_PORT', '5432'))
    postgres_user: str = os.getenv('POSTGRES_USER', 'mineland')
    postgres_password: str = os.getenv('POSTGRES_PASSWORD', 'mineland123')
    postgres_db: str = os.getenv('POSTGRES_DB', 'mineland')
    
    timescale_host: str = os.getenv('TIMESCALE_HOST', 'localhost')
    timescale_port: int = int(os.getenv('TIMESCALE_PORT', '5433'))
    timescale_user: str = os.getenv('TIMESCALE_USER', 'mineland')
    timescale_password: str = os.getenv('TIMESCALE_PASSWORD', 'mineland123')
    timescale_db: str = os.getenv('TIMESCALE_DB', 'iot_data')
    
    # MinIO
    minio_host: str = os.getenv('MINIO_HOST', 'localhost')
    minio_port: int = int(os.getenv('MINIO_PORT', '9000'))
    minio_access_key: str = os.getenv('MINIO_ACCESS_KEY', 'mineland')
    minio_secret_key: str = os.getenv('MINIO_SECRET_KEY', 'mineland123')
    minio_bucket: str = os.getenv('MINIO_BUCKET', 'uploads')
    
    # Copernicus
    sentinel_client_id: Optional[str] = os.getenv('SENTINEL_CLIENT_ID')
    sentinel_client_secret: Optional[str] = os.getenv('SENTINEL_CLIENT_SECRET')
    
    # Sishen study area
    sishen_min_lon: float = 27.3
    sishen_min_lat: float = -23.6
    sishen_max_lon: float = 27.7
    sishen_max_lat: float = -23.3

settings = Settings()