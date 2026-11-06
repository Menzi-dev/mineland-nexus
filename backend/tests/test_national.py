"""Offline regression checks: no external APIs, no production records mutated."""
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".test-tools"))
sys.path.insert(0, str(ROOT / "backend"))
from PIL import Image
from fastapi.testclient import TestClient
from app.main import app
from app.national import store, router, engine
from app.national.geometry import validate_boundary
from app.national.analysis import trend_forecast, screening, evidence_summary
from app.national.insights import build_brief, photo_match
from app.national import providers, local_ai


def square(lon=28.01, lat=-26.23, width=0.01):
    return {"type": "Polygon", "coordinates": [[[lon, lat], [lon+width, lat], [lon+width, lat+width], [lon, lat+width], [lon, lat]]]}


class GeometryTests(unittest.TestCase):
    def test_accepts_multiple_provinces(self):
        for lon, lat in [(28.01, -26.23), (18.6, -33.9), (30.9, -29.8), (29.4, -23.9)]:
            with self.subTest(lon=lon):
                self.assertGreater(validate_boundary(square(lon, lat))["area_ha"], 1)

    def test_rejects_lesotho_and_neighbours(self):
        for lon, lat in [(27.5, -29.3), (25.9, -24.6), (32.6, -25.9)]:
            with self.subTest(lon=lon), self.assertRaises(ValueError):
                validate_boundary(square(lon, lat))

    def test_rejects_small_and_self_crossing(self):
        with self.assertRaises(ValueError):
            validate_boundary(square(width=0.00001))
        with self.assertRaises(ValueError):
            validate_boundary({"type":"Polygon", "coordinates":[[[28,-26],[28.01,-26.01],[28,-26.01],[28.01,-26],[28,-26]]]})


class ForecastTests(unittest.TestCase):
    def test_withholds_sparse_forecast(self):
        self.assertEqual(trend_forecast([{"year":2020, "ndvi":.3}], 5)["status"], "insufficient_evidence")

    def test_temporal_holdouts_and_bounds(self):
        observations = [{"year":2018+i,"ndvi":.5-i*.03} for i in range(8)]
        result = trend_forecast(observations, 10)
        self.assertEqual(result["predictions"][0]["year"], 2026)
        self.assertLess(result["backtest_mae"], .001)
        self.assertEqual(result["backtests"][0]["year"], 2021)
        for row in result["predictions"]:
            self.assertTrue(-1 <= row["lower"] <= row["ndvi"] <= row["upper"] <= 1)

    def test_persistence_can_win(self):
        rows = [{"year":2018+i,"ndvi":v} for i,v in enumerate([.1,.8,.5,.5,.5,.5,.5,.5])]
        self.assertIn("Persistence", trend_forecast(rows, 3)["method"])

    def test_no_abandonment_story(self):
        result = evidence_summary({"observations":[{"year":2020,"ndvi":.7},{"year":2025,"ndvi":.1}]}, {})
        self.assertEqual(result["reason_abandoned"]["status"], "unknown")
        self.assertEqual(result["last_used"]["status"], "unknown")

    def test_withholds_scores_on_missing_evidence(self):
        self.assertEqual(screening({}, {}, {}, {}, {})["candidates"], [])

    def test_occupied_land_does_not_receive_redevelopment_scores(self):
        satellite={'observations':[{'year':2020+i,'ndvi':.4} for i in range(5)]}
        weather={'annual':[{'year':2020+i,'rainfall_mm':700,'solar_kwh_m2_day':5.5} for i in range(5)]}
        cover={'years':[{'year':2023,'fractions':[{'class':'Built area','percent':80},{'class':'Water','percent':0}]}]}
        result=screening(satellite,weather,{}, {'slope_median_degrees':2}, {},cover)
        self.assertEqual(result['status'],'constrained')
        self.assertEqual(result['candidates'],[])

    def test_screening_depends_on_actual_data_and_exposes_formula(self):
        satellite={'observations':[{'year':2020+i,'ndvi':.4} for i in range(5)]}
        weather={'annual':[{'year':2020+i,'rainfall_mm':700,'solar_kwh_m2_day':5.5} for i in range(5)]}
        cover={'years':[{'year':2023,'fractions':[{'class':'Rangeland','percent':100}]}]}
        result=screening(satellite,weather,{}, {'slope_median_degrees':2}, {},cover)
        self.assertEqual(result['status'],'preliminary')
        self.assertEqual(len(result['candidates']),2)
        self.assertIsNone(result['candidates'][1]['future_score'])


class ReadableEvidenceTests(unittest.TestCase):
    def test_empty_evidence_never_invents_owners_or_recommendations(self):
        brief = build_brief({}, validate_boundary(square()))
        self.assertEqual(brief['recommendations'], [])
        self.assertIsNone(brief['ownership']['current_owner'])
        self.assertEqual(brief['ownership']['previous_owners'], [])
        self.assertTrue(all(m['value'] is None for m in brief['metrics']))

    def test_moisture_signal_and_soil_percentage_are_distinct(self):
        brief = build_brief({'satellite': {'observations': [{'year':2025,'ndvi':.4,'ndbi':-.12}]},
                            'moisture': {'annual':[{'year':2025,'surface_m3_m3':.24}]}}, validate_boundary(square()))
        metrics = {m['id']:m for m in brief['metrics']}
        self.assertEqual(metrics['plant_moisture']['value'], .12)
        self.assertEqual(metrics['soil_moisture']['value'], 24)
        self.assertEqual(metrics['soil_moisture']['unit'], '% water by volume')

    def test_water_balance_uses_matching_years_only(self):
        brief = build_brief({'weather': {'annual':[{'year':2024,'rainfall_mm':600,'evapotranspiration_mm':None},
                                                  {'year':2025,'rainfall_mm':None,'evapotranspiration_mm':1000}]}}, validate_boundary(square()))
        self.assertIsNone(next(m for m in brief['metrics'] if m['id']=='water_balance')['value'])

    def test_steep_ground_withholds_solar_and_explains_restoration_risks(self):
        satellite={'observations':[{'year':2020+i,'ndvi':.12,'ndbi':.2} for i in range(5)]}
        weather={'annual':[{'year':2020+i,'rainfall_mm':150,'solar_kwh_m2_day':6,'evapotranspiration_mm':2000} for i in range(5)]}
        cover={'years':[{'year':2023,'dominant_class':'Rangeland','fractions':[{'class':'Rangeland','percent':100}]}]}
        terrain={'slope_median_degrees':26}
        comparison=screening(satellite,weather,{},terrain,{},cover)
        self.assertFalse(any(r['name'].startswith('Solar') for r in comparison['candidates']))
        brief=build_brief({'satellite':satellite,'weather':weather,'terrain':terrain,'landcover':cover,'screening':comparison},validate_boundary(square()))
        risks=' '.join(brief['recommendations'][0]['risks'])
        self.assertIn('slope',risks)
        self.assertIn('low score',risks)
        self.assertIn('water demand',risks)

    def test_photo_without_gps_never_claims_a_match(self):
        self.assertEqual(photo_match({'gps':None}, validate_boundary(square()))['status'], 'user_located')

    def test_photo_outside_boundary_warns_even_when_site_is_confirmed(self):
        site = validate_boundary(square())
        photo = {'gps':{'lat':-33.9,'lon':18.6}}
        self.assertEqual(photo_match(photo, site)['status'], 'gps_outside_boundary')
        self.assertIn('photograph location', build_brief({}, site, photo)['headline'])
        self.assertEqual(photo_match({'gps':{'lat':-26.225,'lon':28.015}}, site)['status'], 'gps_inside_boundary')

    def test_soil_moisture_rejects_incomplete_annual_data(self):
        data = {'daily':{'time':['2025-01-01'], 'soil_moisture_0_to_7cm_mean':[.3], 'soil_moisture_7_to_28cm_mean':[.4]}}
        with patch.object(providers,'fetch',return_value=data):
            result=providers.soil_moisture(validate_boundary(square()),2025,2025)
        self.assertEqual(result['status'],'unavailable')
        self.assertIsNone(result['annual'][0]['surface_m3_m3'])

    def test_public_background_keeps_distance_and_does_not_create_owners(self):
        data={'query':{'pages':{'1':{'title':'Nearby mine','extract':'A former mine.','fullurl':'https://en.wikipedia.org/wiki/Test',
                                    'coordinates':[{'lat':-26.22,'lon':28.02}]}}}}
        with patch.object(providers,'fetch',return_value=data):
            result=providers.public_history(validate_boundary(square()))
        self.assertEqual(result['articles'][0]['scope'],'nearby_area_only')
        self.assertGreater(result['articles'][0]['distance_km'],0)
        self.assertNotIn('owner',result['articles'][0])

    def test_unconfigured_photo_ai_returns_explicit_status(self):
        with patch.object(local_ai,'status',return_value={'status':'not_configured','message':'No local model'}):
            self.assertEqual(local_ai.describe_photo(Path('absent'))['status'],'not_configured')


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        path = Path(self.temp.name)
        self.patches = [patch.object(store, "DATA_DIR", path), patch.object(router, "MEDIA", path)]
        for p in self.patches: p.start()
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        for p in self.patches: p.stop()
        self.temp.cleanup()

    def request(self, **extra):
        return {"name":"Test land", "geometry":square(), "location_confirmed":True, "start_year":2018,"end_year":2025, **extra}

    def test_health_is_national(self):
        self.assertEqual(self.client.get('/health').json()['region'], 'South Africa')

    def test_confirmation_required(self):
        self.assertEqual(self.client.post('/api/assessments',json=self.request(location_confirmed=False)).status_code, 422)

    def test_future_observations_rejected(self):
        self.assertEqual(self.client.post('/api/assessments',json=self.request(end_year=2099)).status_code, 422)

    def test_missing_photo_rejected(self):
        self.assertEqual(self.client.post('/api/assessments',json=self.request(photo_id='absent')).status_code, 422)

    def test_location_lookup_and_outage(self):
        with patch.object(router,'identify_place',return_value={'name':'Nearby mapped address','status':'available'}):
            self.assertEqual(self.client.get('/api/location?lat=-26.22&lon=28.02').json()['name'],'Nearby mapped address')
        with patch.object(router,'identify_place',side_effect=RuntimeError('offline')):
            self.assertEqual(self.client.get('/api/location?lat=-26.22&lon=28.02').status_code,503)
        self.assertEqual(self.client.get('/api/location?lat=100&lon=28.02').status_code,422)

    def test_photo_ai_requires_a_real_upload(self):
        self.assertEqual(self.client.post('/api/photos/missing/analyse').status_code,404)

    def test_photo_metadata_without_fake_location(self):
        buffer = io.BytesIO()
        Image.new('RGB',(32,32),'green').save(buffer,format='JPEG')
        response = self.client.post('/api/photos',files={'file':('../../test.jpg',buffer.getvalue(),'image/jpeg')})
        self.assertEqual(response.status_code, 201)
        photo = response.json()
        self.assertIsNone(photo['gps'])
        self.assertEqual(photo['location_status'],'location_required')
        self.assertEqual(self.client.get(photo['preview_url']).status_code, 200)

    def test_false_image_rejected(self):
        self.assertEqual(self.client.post('/api/photos',files={'file':('fake.jpg',b'not an image','image/jpeg')}).status_code,415)

    def test_photo_gps_is_extracted_and_unconfirmed(self):
        buffer=io.BytesIO()
        image=Image.new('RGB',(32,32),'grey')
        exif=Image.Exif()
        exif[34853]={1:'S',2:(26,13,12),3:'E',4:(28,1,12)}
        image.save(buffer,format='JPEG',exif=exif)
        response=self.client.post('/api/photos',files={'file':('gps.jpg',buffer.getvalue(),'image/jpeg')})
        self.assertEqual(response.status_code,201)
        self.assertAlmostEqual(response.json()['gps']['lat'],-26.22,places=4)
        self.assertEqual(response.json()['location_status'],'gps_unconfirmed')

    def test_job_persists_and_export_is_valid(self):
        with patch.object(router.EXECUTOR,'submit') as submit:
            response = self.client.post('/api/assessments',json=self.request())
        self.assertEqual(response.status_code,202)
        identifier = response.json()['id']
        submit.assert_called_once()
        self.assertEqual(self.client.get('/api/assessments').json()['assessments'][0]['id'],identifier)
        report = self.client.get(f'/api/assessments/{identifier}/report')
        self.assertEqual(report.json()['site']['geometry']['type'],'Polygon')
        self.assertIn('attachment',report.headers['content-disposition'])

    def test_restart_marks_pending_job_interrupted(self):
        row=store.save('assessment',{'status':'running','stage':'test'})
        store.recover_interrupted()
        self.assertEqual(store.get(row['id'],'assessment')['status'],'interrupted')

    def test_all_providers_down_produces_gaps_not_scores(self):
        row=store.save('assessment',{**self.request(), 'site':validate_boundary(square()),'status':'queued',
            'options':{'start_year':2018,'end_year':2025,'season_month':1,'horizon':5}})
        unavailable = {'status':'unavailable','reason':'Offline'}
        with patch.object(engine.providers,'satellite_history',return_value=({**unavailable,'observations':[]},None)), patch.object(engine,'safe_source',return_value=unavailable):
            engine.execute(row['id'])
        result=store.get(row['id'],'assessment')
        self.assertEqual(result['status'],'partial')
        self.assertEqual(result['result']['screening']['candidates'],[])
        self.assertEqual(result['result']['forecast']['status'],'insufficient_evidence')

if __name__=='__main__':
    unittest.main(verbosity=2)
