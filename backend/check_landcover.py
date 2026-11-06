import requests
def main():
    import sys
    if '--providers' in sys.argv:
        from app.national.geometry import validate_boundary
        from app.national.providers import landcover_history, terrain, weather_history, mapped_context
        from pathlib import Path
        import json
        site=validate_boundary({'type':'Polygon','coordinates':[[[28.01,-26.23],[28.025,-26.23],[28.025,-26.215],[28.01,-26.215],[28.01,-26.23]]]})
        for name,call in [('terrain',lambda:terrain(site)),('weather',lambda:weather_history(site,2019,2025)),('landcover',lambda:landcover_history(site,2019,2025)),('context',lambda:mapped_context(site))]:
            try:
                data=call()
                print(name,json.dumps(data)[:2800],flush=True)
                Path(f'backend/data/national/verified_{name}.json').write_text(json.dumps(data),encoding='utf-8')
            except Exception as exc:
                print(name,'FAILED',str(exc),flush=True)
        return
    dem = requests.get('https://earth-search.aws.element84.com/v1/search',params={'collections':'cop-dem-glo-30','bbox':'28.01,-26.23,28.025,-26.215','limit':1},timeout=30)
    dem.raise_for_status()
    print('DEM ASSETS', dem.json()['features'][0]['assets'])
    data = requests.get('https://planetarycomputer.microsoft.com/api/stac/v1/search', params={
        'collections':'io-lulc-annual-v02','bbox':'28.01,-26.23,28.025,-26.215','limit':20},timeout=45)
    data.raise_for_status()
    for f in data.json().get('features',[]):
        print(f['id'], f['properties'].get('datetime'), {key:value.get('href') for key,value in f['assets'].items() if value.get('type','').startswith('image/tiff')})
if __name__ == '__main__':
    main()
