import openeo
import numpy as np
from datetime import datetime
import time

print("🔐 Connecting to openEO...")

try:
    connection = openeo.connect("https://openeo.dataspace.copernicus.eu/")

    print("🔑 Authenticating...")
    connection.authenticate_oidc()

    print("✅ Connected to openEO!")

    # Load Sentinel-2 data for Sishen/Kathu
    print("📡 Loading Sentinel-2 data...")
    s2 = connection.load_collection(
        "SENTINEL2_L2A",
        spatial_extent={
            "west": 27.3,
            "east": 27.7,
            "south": -23.6,
            "north": -23.3
        },
        temporal_extent=["2026-08-01", "2026-08-26"],
        bands=["B04", "B08"]
    )

    print("🧮 Calculating NDVI with explicit bands...")
    ndvi = (s2.band("B08") - s2.band("B04")) / (s2.band("B08") + s2.band("B04"))

    print("📥 Downloading NDVI data (this may take 2-5 minutes)...")
    print("⏳ Please wait...")
    start_time = time.time()

    ndvi.download("sishen_ndvi.tif")

    elapsed = time.time() - start_time
    print(f"✅ Download completed in {elapsed:.1f} seconds!")

    print("📊 Reading downloaded file...")
    import rasterio
    with rasterio.open("sishen_ndvi.tif") as src:
        data = src.read(1)
        print("\n📊 NDVI Results for Sishen/Kathu:")
        print(f"   Mean: {np.nanmean(data):.3f}")
        print(f"   Min: {np.nanmin(data):.3f}")
        print(f"   Max: {np.nanmax(data):.3f}")
        print(f"   Shape: {data.shape}")

    print("\n✅ SUCCESS! NDVI data downloaded to sishen_ndvi.tif")
    print("💡 You can now use this data in your project!")

except Exception as e:
    print(f"❌ Error: {e}")
