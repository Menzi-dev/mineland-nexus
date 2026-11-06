$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$environmentPython = Join-Path $PSScriptRoot '.venv-sa/Scripts/python.exe'
$pythonCommand = if (Test-Path -LiteralPath $environmentPython) { $environmentPython } else { 'python' }
& $pythonCommand -c "import fastapi,uvicorn,multipart,requests,numpy,rasterio,PIL,shapely,pyproj"
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Install dependencies first: python -m venv .venv-sa'
    Write-Host '.\.venv-sa\Scripts\python.exe -m pip install -r backend/requirements-national.txt'
    exit 1
}
if (-not (Test-Path -LiteralPath 'backend/data/national/south_africa.geojson')) {
    & $pythonCommand backend/bootstrap_data.py
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
Write-Host 'MineLand Nexus API: http://127.0.0.1:8000 | API documentation: http://127.0.0.1:8000/docs'
& $pythonCommand -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
