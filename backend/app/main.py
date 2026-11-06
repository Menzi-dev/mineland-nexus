"""Active national application. Earlier fixed-site prototype is in legacy_main.py."""
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.national.router import router
from app.national.store import recover_interrupted


@asynccontextmanager
async def lifespan(app):
    recover_interrupted()
    yield


app = FastAPI(title="MineLand Nexus — South Africa", version="5.0.0",
    description="Evidence-led satellite land assessment for South Africa. No invented histories or sensor readings.", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"], allow_headers=["Content-Type"])
app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok", "region": "South Africa", "version": "5.0.0", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/")
def root():
    return {"name": "MineLand Nexus", "region": "South Africa", "docs": "/docs", "capabilities": "/api/capabilities"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000)
