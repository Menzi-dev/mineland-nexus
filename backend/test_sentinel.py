from sentinelhub import SHConfig, BBox, CRS, SentinelHubRequest, DataCollection, MimeType
import numpy as np

# Optional legacy integration check. Never commit account credentials.
import os
CLIENT_ID = os.environ.get("SENTINEL_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("SENTINEL_CLIENT_SECRET", "")
if not CLIENT_ID or not CLIENT_SECRET:
    raise SystemExit("Set SENTINEL_CLIENT_ID and SENTINEL_CLIENT_SECRET to run this legacy check. The active national application needs neither.")

print("🔐 Configuring Sentinel Hub...")

config = SHConfig()
config.sh_client_id = CLIENT_ID
config.sh_client_secret = CLIENT_SECRET

# Sishen/Kathu area
bbox = BBox([27.3, -23.6, 27.7, -23.3], crs=CRS.WGS84)

print("📍 Area: Sishen/Kathu")
print("📡 Creating NDVI request...")

evalscript = """
//VERSION=3
function setup() {
    return {
        input: ["B04", "B08"],
        output: { bands: 1 }
    };
}
function evaluatePixel(sample) {
    let ndvi = (sample.B08 - sample.B04) / (sample.B08 + sample.B04);
    return [ndvi];
}
"""

try:
    request = SentinelHubRequest(
        evalscript=evalscript,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A,
                time_interval=("2026-08-01", "2026-08-26"),
                maxcc=0.15
            )
        ],
        responses=[
            SentinelHubRequest.output_response('default', MimeType.TIFF)
        ],
        bbox=bbox,
        size=(512, 512),
        config=config
    )

    print("✅ Request created successfully!")
    print("📥 Downloading data...")

    data = request.get_data()[0]

    print("\n📊 NDVI Results for Sishen/Kathu:")
    print(f"   Mean: {np.nanmean(data):.3f}")
    print(f"   Min: {np.nanmin(data):.3f}")
    print(f"   Max: {np.nanmax(data):.3f}")
    print(f"   Shape: {data.shape}")
    print("\n✅ SUCCESS! Your credentials are working!")

except Exception as e:
    print(f"❌ Error: {e}")
