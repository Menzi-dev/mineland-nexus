from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from PIL import Image, ImageStat
import os
import shutil
from datetime import datetime

router = APIRouter(prefix="/api/uploads", tags=["uploads"])

# Create uploads directory if it doesn't exist
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

REFERENCE_SITE = {
    "id": "nababeep-historic-copper-mine",
    "name": "Nababeep Historic Copper Mine",
    "description": "Historic copper-mining landscape near Springbok, Northern Cape",
    "coordinates": {"lat": -29.77, "lon": 17.82},
    "source": "Reference location for this assessment workflow; confirm the exact pit or shaft boundary in the field.",
}


def analyse_image(filepath: str):
    """Return transparent, local image signals for the selected reference site."""
    with Image.open(filepath) as image:
        rgb_image = image.convert("RGB")
        width, height = rgb_image.size
        red, green, blue = (value / 255 for value in ImageStat.Stat(rgb_image).mean)

    brightness = (red + green + blue) / 3
    features = []
    if green > red * 1.08 and green > blue * 1.05:
        features.append("Vegetation signal detected")
    if blue > red * 1.12 and blue > green * 1.02:
        features.append("Possible water or blue-sky signal detected")
    if red > blue * 1.12 and red > green * 1.03:
        features.append("Exposed soil or iron-rich ground signal detected")
    if brightness < 0.25:
        features.append("Low-light image; ground condition confidence is limited")
    elif brightness > 0.78:
        features.append("Bright image; shadows and surface detail may be limited")
    if not features:
        features.append("Mixed surface colours detected; field review recommended")

    return {
        "method": "Local image signal analysis",
        "dimensions": {"width": width, "height": height},
        "average_rgb": {"red": round(red, 3), "green": round(green, 3), "blue": round(blue, 3)},
        "brightness": round(brightness, 3),
        "features": features,
        "note": "Signals are indicative and should be confirmed with field evidence and geospatial data.",
    }

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    site_id: str = Form("nababeep-historic-copper-mine"),
):
    """Upload an image file for analysis"""
    try:
        # Validate file type
        allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Only image files are allowed")

        if file.filename is None:
            raise HTTPException(status_code=400, detail="A filename is required")

        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{os.path.basename(file.filename)}"
        filepath = os.path.join(UPLOAD_DIR, filename)

        # Save file
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        size = os.path.getsize(filepath)
        if size > 10 * 1024 * 1024:
            os.remove(filepath)
            raise HTTPException(status_code=413, detail="Images must be 10MB or smaller")

        analysis = analyse_image(filepath)

        return {
            "status": "success",
            "message": "File uploaded and analysed successfully",
            "filename": filename,
            "filepath": filepath,
            "size": size,
            "content_type": file.content_type,
            "analysis_status": "complete",
            "site": {**REFERENCE_SITE, "id": site_id},
            "analysis": analysis,
            "features": analysis["features"],
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reference-site")
async def get_reference_site():
    """Return the Northern Cape site used by the image assessment workflow."""
    return {"status": "success", "site": REFERENCE_SITE}

@router.get("/files")
async def list_uploaded_files():
    """List all uploaded files"""
    try:
        files = []
        for filename in os.listdir(UPLOAD_DIR):
            filepath = os.path.join(UPLOAD_DIR, filename)
            if os.path.isfile(filepath):
                files.append({
                    "name": filename,
                    "size": os.path.getsize(filepath),
                    "modified": datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
                })

        return {
            "status": "success",
            "files": files,
            "count": len(files)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/files/{filename}")
async def delete_file(filename: str):
    """Delete an uploaded file"""
    try:
        filepath = os.path.join(UPLOAD_DIR, filename)
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="File not found")

        os.remove(filepath)
        return {
            "status": "success",
            "message": f"File '{filename}' deleted successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    app.include_router(uploads.router)
