"""Auditable baseline forecasting and screening, with no fabricated training labels."""
import numpy as np


def trend_forecast(observations, horizon):
    rows = sorted(observations, key=lambda row: row["year"])
    if len(rows) < 5:
        return {"status": "insufficient_evidence", "reason": "At least five usable same-season years are required. No prediction was made."}
    x = np.array([r["year"] for r in rows], dtype=float)
    y = np.array([r["ndvi"] for r in rows], dtype=float)
    origin = x[0]
    t = x - origin
    slope, intercept = np.polyfit(t, y, 1)
    residuals = y - (slope * t + intercept)
    # Honest temporal evaluation: each holdout is later than every fitting sample.
    backtests = []
    for i in range(3, len(rows)):
        s, b = np.polyfit(t[:i], y[:i], 1)
        predicted = float(np.clip(s * t[i] + b, -1, 1))
        backtests.append({"year": int(x[i]), "predicted": round(predicted, 4), "observed": float(y[i]), "absolute_error": round(abs(predicted - y[i]), 4)})
    baseline_errors = [abs(y[i] - y[i-1]) for i in range(3, len(rows))]
    mae = float(np.mean([r["absolute_error"] for r in backtests]))
    baseline_mae = float(np.mean(baseline_errors))
    use_linear = mae < baseline_mae
    degrees = len(rows) - 2
    t_critical = {3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228}.get(degrees, 2.201)
    sigma = np.sqrt(np.sum(residuals ** 2) / degrees)
    denom = np.sum((t - t.mean()) ** 2)
    future = []
    for step in range(1, horizon + 1):
        year = int(x[-1]) + step
        target = year - origin
        predicted = float(slope * target + intercept) if use_linear else float(y[-1])
        if use_linear:
            margin = t_critical * sigma * np.sqrt(1 + 1 / len(t) + (target - t.mean()) ** 2 / denom)
            margin = max(float(margin), mae)
        else:
            margin = max(float(np.std(np.diff(y), ddof=1)) * 1.96 * np.sqrt(step), baseline_mae)
        future.append({"year": year, "ndvi": round(float(np.clip(predicted, -1, 1)), 4),
                       "lower": round(float(np.clip(predicted - margin, -1, 1)), 4),
                       "upper": round(float(np.clip(predicted + margin, -1, 1)), 4)})
    return {"status": "available", "method": "Linear same-season NDVI trend" if use_linear else "Persistence baseline (last observed seasonal NDVI)",
            "selection": "Selected by rolling-origin absolute error against a persistence baseline, using only preceding years for each evaluation.",
            "annual_slope": round(float(slope), 5), "backtest_mae": round(mae if use_linear else baseline_mae, 4),
            "linear_backtest_mae": round(mae, 4), "persistence_backtest_mae": round(baseline_mae, 4),
            "backtests": backtests, "predictions": future,
            "uncertainty": "Approximate 95% statistical prediction band under trend/persistence assumptions; not calibrated for land-use interventions, fires, future mining or climate regime shifts.",
            "climate_coupling": "NDVI extrapolation is separate from climate models. Climate evidence informs future screening but is not presented as a trained vegetation response model."}


def _average(rows, key):
    values = [r[key] for r in rows if r.get(key) is not None]
    return float(np.mean(values)) if values else None


def screening(satellite, weather, climate, terrain, forecast, landcover=None):
    observations = satellite.get("observations", [])
    annual = weather.get("annual", [])
    if len(observations) < 4 or len([r for r in annual if r.get("rainfall_mm") is not None and r.get("solar_kwh_m2_day") is not None]) < 3:
        return {"status": "insufficient_evidence", "candidates": [], "reason": "Need four usable satellite years and three complete weather years to compare land-use options."}
    cover_years = (landcover or {}).get("years", [])
    if not cover_years:
        return {"status": "insufficient_evidence", "candidates": [], "reason": "Land-use scoring is withheld until actual land-cover evidence is available. Satellite indices alone cannot establish whether the land is developed or water-covered."}
    cover = {row["class"]: row["percent"] for row in cover_years[-1]["fractions"]}
    constraints = []
    if cover.get("Built area", 0) > 20 or cover.get("Water", 0) > 20:
        return {"status": "constrained", "candidates": [],
            "reason": f"The latest available land-cover classification ({cover_years[-1]['year']}) has {cover.get('Built area', 0)}% built area and {cover.get('Water', 0)}% water. Redevelopment screening is withheld; check that you selected the intended undeveloped land and verify current conditions.",
            "constraints": ["Existing built or water cover is not evidence of abandoned land. No pathway is recommended from these inputs."]}
    if cover.get("Crops", 0) > 20:
        constraints.append("Satellite classification indicates substantial cropland. Existing productive use and food-security impacts must be checked; abandonment is unverified.")
    if cover.get("Trees", 0) + cover.get("Flooded vegetation", 0) > 30:
        constraints.append("Substantial tree or flooded-vegetation cover is mapped. Biodiversity, wetland and protected-area checks are required before any development.")
    latest = observations[-1]
    solar = _average(annual[-5:], "solar_kwh_m2_day")
    rain = _average(annual[-5:], "rainfall_mm")
    slope = terrain.get("slope_median_degrees")
    bounded = lambda value: max(0.0, min(100.0, value))
    candidates = []
    if slope is not None and slope > 15:
        constraints.append("Median terrain slope exceeds 15 degrees. Solar scoring is withheld because this simple flatness rubric cannot establish engineering feasibility on steep ground.")
    if slope is not None and slope <= 15 and solar is not None:
        resource = bounded(solar / 7 * 100)
        flatness = bounded(100 - slope / 15 * 100)
        solar_score = 0.7 * resource + 0.3 * flatness
        candidates.append({"name": "Solar energy feasibility", "score": round(solar_score, 1),
            "basis": f"70% solar resource ({solar:.2f} kWh/m²/day; 7 is the screening reference) + 30% terrain flatness ({slope:.1f}° median; 15° gives zero flatness).",
            "next_steps": "Check grid capacity, protected-area restrictions, biodiversity, ownership, site access and engineering feasibility.",
            "future_score": None})
    vegetation = bounded((latest["ndvi"] + 0.1) / 0.9 * 100)
    moisture = bounded((rain or 0) / 800 * 100)
    restoration_score = 0.65 * vegetation + 0.35 * moisture
    future_rain = [m["rainfall_change_percent"] for m in climate.get("models", []) if m.get("rainfall_change_percent") is not None]
    warming = [m["temperature_change_c"] for m in climate.get("models", [])]
    future_score = None
    stress = None
    if future_rain and warming:
        # Deliberately a declared policy rubric, not a learned biological response.
        stress = min(20, max(0, float(np.mean(warming))) * 3 + max(0, -float(np.mean(future_rain))) * 0.2)
        future_score = round(bounded(restoration_score - stress), 1)
    candidates.append({"name": "Ecological restoration feasibility", "score": round(restoration_score, 1),
        "basis": f"65% vegetation signal (seasonal NDVI {latest['ndvi']:.3f}, scaled from −0.1 to 0.8) + 35% rainfall resource ({rain:.0f} mm/year, reference 800 mm).",
        "next_steps": "Survey native species, soil condition, contamination, erosion and water availability. This is regeneration potential, not restoration urgency.",
        "future_score": future_score,
        "future_basis": "Illustrative stress rubric: subtract 3 points per °C warming and 0.2 points per percent rainfall decline, capped at 20. These coefficients are not empirically calibrated." if stress is not None else "Future screening withheld because climate projections are missing."})
    return {"status": "preliminary", "candidates": sorted(candidates, key=lambda row: row["score"], reverse=True),
            "constraints": constraints,
            "meaning": "Transparent 0–100 comparative screening rubric, not probability, validated suitability, investment advice or permission to develop.",
            "withheld": [{"name": name, "reason": reason} for name, reason in [
                ("Agriculture and food production", "Soil fertility, contamination, water rights and irrigation suitability are unverified."),
                ("Grazing", "Forage species, carrying capacity, contamination and livestock water supply are unverified."),
                ("Battery storage", "Actual substation capacity, electrical connection study and site engineering are unverified."),
                ("Community development", "Tenure, planning permissions, ground stability and community requirements are unverified.")]],
            "forecast_available": forecast.get("status") == "available"}


def evidence_summary(satellite, context, landcover=None):
    observations = satellite.get("observations", [])
    change = None
    if len(observations) >= 2:
        first, last = observations[0], observations[-1]
        delta = last["ndvi"] - first["ndvi"]
        change = {"from_year": first["year"], "to_year": last["year"], "ndvi_change": round(delta, 4),
                  "description": "Higher vegetation signal" if delta > 0.05 else "Lower vegetation signal" if delta < -0.05 else "Limited net change in vegetation signal",
                  "caution": "A spectral change is not proof of abandonment, rehabilitation, productivity or a specific land use."}
    cover_years = (landcover or {}).get("years", [])
    cover_explanation = "Current OpenStreetMap tags are contextual evidence; a historical land-use classification has not been validated."
    if cover_years:
        cover_explanation = f"The published satellite classifier mapped the dominant cover as {cover_years[0]['dominant_class']} in {cover_years[0]['year']} and {cover_years[-1]['dominant_class']} in {cover_years[-1]['year']}. Land cover is not proof of a specific human activity or its cessation."
    return {"vegetation_change": change, "abandonment_status": "unverified",
            "last_used": {"status": "unknown", "explanation": "Satellite indices do not establish the last date of human use. Dated imagery and independent records need review."},
            "previous_use": {"status": "classified_cover_only" if cover_years else "unverified", "explanation": cover_explanation},
            "reason_abandoned": {"status": "unknown", "explanation": "Not inferable from a photograph or vegetation trend. Requires closure records, owner testimony or another documented source."}}
