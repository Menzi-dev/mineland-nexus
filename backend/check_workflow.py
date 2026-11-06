"""Exercise the live national API through submission, polling and report download."""
import json
from pathlib import Path
import time
import requests

def main():
    base = 'http://127.0.0.1:8000'
    body = {'name':'National workflow verification (Johannesburg)',
        'geometry':{'type':'Polygon','coordinates':[[[28.01,-26.23],[28.025,-26.23],[28.025,-26.215],[28.01,-26.215],[28.01,-26.23]]]},
        'location_confirmed':True,'start_year':2019,'end_year':2025,'season_month':6,'horizon':5,
        'notes':'Engineering verification extent; not asserted to be abandoned. Every satellite and climate value is retrieved from the linked public sources.'}
    response=requests.post(base+'/api/assessments',json=body,timeout=20)
    response.raise_for_status()
    identifier=response.json()['id']
    print('ASSESSMENT_ID='+identifier,flush=True)
    previous=None
    for _ in range(300):
        response=requests.get(base+'/api/assessments/'+identifier,timeout=20)
        response.raise_for_status()
        record=response.json()
        stage=record['stage']
        if stage != previous:
            print(record['status'],stage,flush=True)
            previous=stage
        if record['status'] not in ('running','queued'):
            if record['status'] not in ('complete','partial'):
                raise RuntimeError(record)
            report=requests.get(base+f'/api/assessments/{identifier}/report',timeout=20)
            report.raise_for_status()
            assert report.json()['id']==identifier
            result=record['result']
            assert result['satellite']['observations'], 'No real satellite observations'
            assert result['weather']['annual'][0]['rainfall_mm'] is not None
            assert result['climate']['models'], 'No climate projections'
            assert result['landcover']['years'], 'No historical land cover'
            assert result['screening']['status']=='constrained', 'Built-up verification land must not receive redevelopment scores'
            assert not result['screening']['candidates']
            assert result['history']['reason_abandoned']['status']=='unknown'
            overlay=requests.get(base+f'/api/assessments/{identifier}/overlay',timeout=20)
            overlay.raise_for_status()
            print(json.dumps({'status':record['status'],'usable_satellite_years':len(result['satellite']['observations']),
                'cover_years':len(result['landcover']['years']),'climate_models':len(result['climate']['models']),
                'screening':result['screening']['status'],'source_statuses':{k:result[k]['status'] for k in ['satellite','weather','terrain','climate','landcover','context']}}),flush=True)
            print('PASS: live submission, durable progress, actual data, occupied-land constraint, JSON report and overlay.',flush=True)
            Path('artifacts').mkdir(exist_ok=True)
            Path('artifacts/live-verification.json').write_text(report.text,encoding='utf-8')
            return
        time.sleep(3)
    raise TimeoutError('Assessment exceeded the verification time limit; inspect its saved progress.')

if __name__=='__main__':
    main()
