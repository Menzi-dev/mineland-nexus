from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import os
from dotenv import load_dotenv

load_dotenv()

# PostgreSQL for GIS data
POSTGRES_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"

# TimescaleDB for IoT data
TIMESCALE_URL = f"postgresql://{os.getenv('TIMESCALE_USER')}:{os.getenv('TIMESCALE_PASSWORD')}@{os.getenv('TIMESCALE_HOST')}:{os.getenv('TIMESCALE_PORT')}/{os.getenv('TIMESCALE_DB')}"

# PostgreSQL engine with PostGIS
pg_engine = create_engine(POSTGRES_URL, poolclass=NullPool)
pg_session = sessionmaker(autocommit=False, autoflush=False, bind=pg_engine)

# TimescaleDB engine
ts_engine = create_engine(TIMESCALE_URL, poolclass=NullPool)
ts_session = sessionmaker(autocommit=False, autoflush=False, bind=ts_engine)

Base = declarative_base()

def get_pg_session():
    db = pg_session()
    try:
        yield db
    finally:
        db.close()

def get_ts_session():
    db = ts_session()
    try:
        yield db
    finally:
        db.close()