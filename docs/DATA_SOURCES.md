# Data sources and interpretation

Every assessment should retain source links, retrieval times and explicit gaps. A provider being available does not mean every requested year is covered.

| Evidence | Provider | Interpretation |
| --- | --- | --- |
| Vegetation and surface-water signals | [Sentinel-2 / Earth Search](https://github.com/Element84/earth-search) | NDVI, NDWI and NDBI from calibrated surface reflectance; up to three clear acquisition dates per year in the same three-month season. NDMI uses the opposite order of the same NIR/SWIR pair as NDBI. These indices are not crop yields, chemical tests or proof of activity. |
| Rainfall, temperature, sunlight, reference evapotranspiration | [Open-Meteo historical weather / ERA5](https://open-meteo.com/en/docs/historical-weather-api) | Approximately 25 km reanalysis. Annual values require at least 90% daily completeness. Rainfall minus reference evapotranspiration is a climatic indicator, not the site's measured water balance. |
| Soil moisture | [Open-Meteo / ERA5-Land](https://open-meteo.com/en/docs/historical-weather-api) | Approximately 11 km model grid. Surface layer: 0–7 cm; shallow subsurface: 7–28 cm. Volume percent is not relative saturation or an irrigation prescription. Yearly retrieval avoids large-request timeouts. |
| Future climate | [Open-Meteo CMIP6](https://open-meteo.com/en/docs/climate-api) | EC_Earth3P_HR and MRI_AGCM3_2_S compare decadal periods. This is not a prediction of weather in a specific future year or a comparison across emissions scenarios. |
| Elevation and slope | [Copernicus DEM GLO-30](https://registry.opendata.aws/copernicus-dem/) | Approximately 30 m surface elevation and estimated terrain slope; not a survey or ground-stability assessment. |
| Historical land cover | [Impact Observatory / Esri / Microsoft annual land cover v2](https://planetarycomputer.microsoft.com/dataset/io-lulc-annual-v02) | Published 10 m classification sampled within the polygon. Product availability and classification errors limit the timeline. Later missing years remain missing. |
| Place search and nearest address | [OpenStreetMap / Nominatim](https://nominatim.org/release-docs/develop/api/Reverse/) | The nearest mapped address is context, not a verified cadastral identity. Requests are rate-limited and cached. |
| Mapped land use | [OpenStreetMap / Overpass](https://www.openstreetmap.org/copyright) | Volunteer map tags in the search rectangle. Exact parcel overlap, ownership and dates of activity are unverified. |
| Nearby public background | [Wikipedia geosearch](https://www.mediawiki.org/wiki/API:Geosearch) | Short attributed excerpts about places within 10 km, labelled with distance and scope. These are not verified histories of the selected parcel. |
| National extent | [geoBoundaries gbOpen ZAF ADM0](https://www.geoboundaries.org/api.html) | Attributed 2020 source boundary, simplified by 0.0002 degrees. The bundled source metadata records CC BY 3.0 IGO. Not a cadastral boundary; neighbouring countries are excluded. |
| Basemap imagery | Esri / Maxar / Earthstar Geographics; OpenStreetMap | Basemap dates vary independently of the dated analytical overlay. Attribution remains visible on the map. |
| Local photo description | [SmolVLM-256M](https://huggingface.co/ggml-org/SmolVLM-256M-Instruct-GGUF), [llama.cpp](https://github.com/ggml-org/llama.cpp) | Small vision-language model that can make mistakes. Descriptions are unverified and do not supply coordinates, ownership records or suitability scores. Model: Apache-2.0; runtime: MIT. |

## Recommendations and forecasts

The forecasting module compares a linear same-season NDVI trend with persistence using rolling-origin historical errors. It requires at least five usable years and displays approximate statistical uncertainty. It is a baseline, not a validated national land-use prediction model.

Solar and restoration scores are transparent preliminary rubrics. Built/water cover can withhold redevelopment scoring; median slopes above 15 degrees withhold solar scoring. A rank is a study priority among supported comparisons, not approval or proof of a best use. Other future uses require additional evidence.

## Ownership and history

The application has no connected title registry. Owners, transfer chains, abandonment, last-use dates and closure reasons remain unverified. Consult [South African Government guidance on Deeds Registry information](https://www.gov.za/services/services-residents/place-live/get-deeds-registry-information) for the required property identifiers and official process.

## Terms and attribution

Data, model and runtime licences are separate from application-code rights. Open-Meteo's free hosted endpoints are for non-commercial use; see its [terms](https://open-meteo.com/en/terms). Respect provider fair-use policies, attribution requirements and dataset licences. The country-boundary attribution is bundled in `backend/data/national/boundary_source.json`. This repository does not grant rights to third-party imagery, datasets or model weights.
