"""Plain-language decisions grounded in retrieved evidence, not generated facts."""
from math import asin, cos, radians, sin, sqrt


def mean(rows, key):
    values = [r[key] for r in rows if r.get(key) is not None]
    return sum(values) / len(values) if values else None


def photo_match(photo, site):
    if not photo:
        return {"status": "map_selected", "explanation": "This assessment uses the land boundary you selected on the map."}
    gps = photo.get("gps")
    if not gps:
        return {"status": "user_located", "explanation": "The photograph has no usable GPS. Its connection to this land is based on your map confirmation; the image has not independently identified the location."}
    lat, lon = site["center"]["lat"], site["center"]["lon"]
    a = sin(radians(gps["lat"] - lat) / 2) ** 2 + cos(radians(lat)) * cos(radians(gps["lat"])) * sin(radians(gps["lon"] - lon) / 2) ** 2
    distance = 6371000 * 2 * asin(sqrt(min(1, a)))
    from shapely.geometry import Point, shape
    inside = shape(site["geometry"]).covers(Point(gps["lon"], gps["lat"]))
    return {"status": "gps_inside_boundary" if inside else "gps_outside_boundary", "gps": gps,
            "distance_to_centre_m": round(distance),
            "explanation": "Photo GPS lies inside the selected boundary. GPS metadata can be edited and is not independent proof." if inside else f"Photo GPS lies outside the selected boundary ({distance / 1000:.2f} km from its centre). Check whether the camera was outside the land or the wrong area was selected."}


def build_brief(result, site, photo=None):
    obs = result.get("satellite", {}).get("observations", [])
    weather = result.get("weather", {}).get("annual", [])
    cover = result.get("landcover", {}).get("years", [])
    latest = obs[-1] if obs else {}
    rain = mean(weather[-5:], "rainfall_mm")
    et = mean(weather[-5:], "evapotranspiration_mm")
    water_pairs = [r for r in weather[-5:] if r.get("rainfall_mm") is not None and r.get("evapotranspiration_mm") is not None]
    water_balance = mean([{"balance": r["rainfall_mm"] - r["evapotranspiration_mm"]} for r in water_pairs], "balance")
    solar = mean(weather[-5:], "solar_kwh_m2_day")
    temperature = mean(weather[-5:], "temperature_c")
    slope = result.get("terrain", {}).get("slope_median_degrees")
    moisture = result.get("moisture", {}).get("annual", [])
    shallow = moisture[-1].get("surface_m3_m3") if moisture else None
    ndvi = latest.get("ndvi")
    ndmi = -latest["ndbi"] if latest.get("ndbi") is not None else None
    metrics = []
    def metric(id, title, value, unit, explanation, source, period):
        metrics.append({"id": id, "title": title, "value": round(value, 3) if value is not None else None,
                        "unit": unit, "explanation": explanation if value is not None else "No usable data returned. This condition is unknown.",
                        "source": source, "period": period})
    period = f"{latest.get('year', 'No year')} selected three-month season"
    metric("vegetation", "Vegetation", ndvi, "NDVI index",
           ("Strong" if ndvi is not None and ndvi >= .5 else "Moderate" if ndvi is not None and ndvi >= .2 else "Low") + " green vegetation signal in the sampled season. This does not identify plant species, soil fertility or whether the land is in use.", "satellite", period)
    metric("plant_moisture", "Vegetation moisture signal", ndmi, "NDMI index",
           "Near-infrared and shortwave-infrared contrast is sensitive to vegetation water content; bare ground and mixed surfaces affect it. This is not a soil-water percentage.", "satellite", period)
    metric("soil_moisture", "Surface soil moisture", shallow * 100 if shallow is not None else None, "% water by volume",
           "Average modelled water content in the top 0–7 cm. The regional grid cannot resolve individual patches; a field test is needed before irrigation decisions.", "moisture", str(moisture[-1]["year"]) if moisture else "No year")
    weather_years = [r["year"] for r in weather[-5:]]
    wp = f"Available years {min(weather_years)}–{max(weather_years)}" if weather_years else "No years"
    metric("rainfall", "Rainfall", rain, "mm per year", "Average annual rainfall in recent available years. Rainfall varies between seasons and years; it does not establish usable water rights.", "weather", wp)
    metric("water_balance", "Rainfall minus water demand", water_balance, "mm per year",
           "Rainfall minus reference evapotranspiration (ET₀). Negative values indicate atmospheric demand exceeds rainfall for a reference crop. This is a climate indicator, not a measured water budget for this soil or crop.", "weather", wp)
    metric("temperature", "Average temperature", temperature, "°C", "Regional annual mean air temperature. Heat extremes and frost require a more detailed crop or engineering study.", "weather", wp)
    metric("solar", "Sunlight resource", solar, "kWh/m²/day", "Average daily incoming solar energy. A solar project still needs grid, land-use and engineering studies.", "weather", wp)
    metric("slope", "Land slope", slope, "degrees", "Median slope estimated from the terrain model. Steeper ground can make access, construction and erosion management harder.", "terrain", "Copernicus DEM")
    timeline = [{"year": r["year"], "title": f"Mostly {r['dominant_class'].lower()}",
                 "description": ", ".join(f"{f['class']} {f['percent']}%" for f in r["fractions"] if f["percent"] >= 5),
                 "source_urls": r.get("catalogue_urls", []), "evidence_type": "satellite_classification"} for r in cover]
    facts = []
    if cover:
        facts.append(f"Satellite classification shows mostly {cover[0]['dominant_class'].lower()} in {cover[0]['year']} and mostly {cover[-1]['dominant_class'].lower()} in {cover[-1]['year']}. This describes land cover, not a verified business or activity.")
    change = result.get("history", {}).get("vegetation_change")
    if change:
        facts.append(f"{change['description']} between {change['from_year']} and {change['to_year']} (NDVI change {change['ndvi_change']:+.3f}).")
    if rain is not None:
        facts.append(f"Recent available years averaged {rain:.0f} mm of rainfall per year.")
    screening = result.get("screening", {})
    candidates = screening.get("candidates", [])
    recommendations = []
    for candidate in candidates:
        is_solar = candidate["name"].startswith("Solar")
        reasons = ([f"The retrieved solar resource is {solar:.2f} kWh/m²/day.", f"The estimated median slope is {slope:.1f}°."] if is_solar else
                   [f"The latest seasonal vegetation index is {ndvi:.3f}.", f"Recent rainfall averages {rain:.0f} mm/year."])
        risks = ["Ownership, planning restrictions, biodiversity and contamination have not been verified."]
        if slope is not None and slope > 15:
            risks.append(f"The estimated median slope is {slope:.1f}°; check erosion, safe access and earthworks feasibility on site.")
        if candidate['score'] < 40:
            risks.append("This option has a low score under the preliminary rubric. Being first in this limited comparison does not establish good suitability.")
        if water_balance is not None and water_balance < 0:
            risks.append(f"Reference atmospheric water demand exceeds rainfall by about {-water_balance:.0f} mm/year; assess water supply and drought resilience.")
        recommendations.append({"title": candidate["name"], "status": "worth_investigating", "reasons": reasons,
                                "risks": risks, "action": candidate["next_steps"], "score": candidate["score"]})
    if recommendations:
        headline = f"First option to investigate: {recommendations[0]['title'].lower()}."
        verdict = "This ranks first among the options this system can currently compare. It is a preliminary study priority, not a confirmed best use."
    elif screening.get("status") == "constrained":
        headline = "Check existing land use before planning a new use."
        verdict = screening["reason"]
    else:
        headline = "More evidence is needed before choosing a future use."
        verdict = screening.get("reason", "The available evidence cannot support a comparison.")
    match = photo_match(photo, site)
    if match["status"] == "gps_outside_boundary":
        headline = "Check the photograph location before relying on this report."
        verdict = match["explanation"]
    checklist = ["Confirm the exact property or farm portion and cadastral boundary.",
                 "Request current and historical title records from the Deeds Registry or a conveyancer; verify the parcel identifier first.",
                 "Ask the municipality about zoning, approved uses, services and planning restrictions.",
                 "Arrange soil fertility and contamination tests, and verify water availability and rights before food production.",
                 "Visit the site to check current use, access, erosion, wetlands and local needs."]
    if not recommendations:
        checklist.insert(0, "Review the missing evidence and current built/water cover before comparing development options.")
    conditional = [
        {"title": "Agriculture or food growing", "possibility": "Assess crops suited to the local rainfall, heat and soil, while checking whether farming is already taking place.",
         "needed": "Soil fertility and contamination tests, reliable water supply and rights, seasonal crop needs, and market access."},
        {"title": "Managed grazing", "possibility": "Investigate grazing only if a field survey confirms suitable forage and a sustainable stocking rate.",
         "needed": "Native forage assessment, carrying capacity, livestock water, contamination checks and existing-use records."},
        {"title": "Community or small business use", "possibility": "Explore uses requested by nearby residents and businesses after checking the property's existing use and restrictions.",
         "needed": "Ownership, zoning, access, services, ground stability, community consultation and a demand study."},
    ]
    if cover and cover[-1]['dominant_class'] == 'Built area':
        conditional.insert(0, {"title": "Reuse of existing developed land", "possibility": "First establish whether the buildings and land are occupied or in active use. Reuse may be worth studying if suitable space is genuinely available.",
                              "needed": "Owner consent, occupancy and use records, building condition, contamination, zoning and service capacity."})
    return {"headline": headline, "verdict": verdict, "facts": facts, "metrics": metrics, "timeline": timeline,
            "recommendations": recommendations, "conditional_options": conditional, "next_steps": checklist, "photo_location": match,
            "ownership": {"status": "not_verified", "current_owner": None, "previous_owners": [],
                "explanation": "No verified parcel-specific title record is connected. Names from nearby articles, map tags or photographs are not evidence of ownership.",
                "required": "Property description (farm/erf name and number, portion and registration division) or a title-deed number.",
                "source_url": "https://www.gov.za/services/services-residents/place-live/get-deeds-registry-information"},
            "method": "Evidence rules and statistical baselines; not a trained land-use suitability model."}
