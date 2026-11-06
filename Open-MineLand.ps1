param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$logDirectory = Join-Path $PSScriptRoot 'artifacts'
New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot '.local-ai/runtime/llama-server.exe')) {
    & (Join-Path $PSScriptRoot 'start-local-ai.ps1')
}

function Test-ServiceUrl([string]$Url) {
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
        return $response.StatusCode -eq 200
    } catch { return $false }
}

$pythonPath = Join-Path $PSScriptRoot '.venv-sa/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { $pythonPath = (Get-Command python -ErrorAction Stop).Source }
$nodePath = (Get-Command node -ErrorAction Stop).Source
$vitePath = Join-Path $PSScriptRoot 'frontend/node_modules/vite/bin/vite.js'
if (-not (Test-Path -LiteralPath $vitePath)) { throw 'Frontend dependencies are missing. Run npm.cmd ci in the frontend folder first.' }

if (-not (Test-ServiceUrl 'http://127.0.0.1:8000/health')) {
    Write-Host 'Starting the land assessment API...'
    $backendArguments = @('-m', 'uvicorn', 'app.main:app', '--app-dir', ('"' + (Join-Path $PSScriptRoot 'backend') + '"'), '--host', '127.0.0.1', '--port', '8000')
    Start-Process -FilePath $pythonPath -ArgumentList $backendArguments -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logDirectory 'backend.stdout.log') -RedirectStandardError (Join-Path $logDirectory 'backend.stderr.log') | Out-Null
}
if (-not (Test-ServiceUrl 'http://127.0.0.1:5173/')) {
    Write-Host 'Starting the interface...'
    $frontendArguments = @(('"' + $vitePath + '"'), '--host', '127.0.0.1', '--port', '5173', '--strictPort')
    Start-Process -FilePath $nodePath -ArgumentList $frontendArguments -WorkingDirectory (Join-Path $PSScriptRoot 'frontend') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logDirectory 'frontend.stdout.log') -RedirectStandardError (Join-Path $logDirectory 'frontend.stderr.log') | Out-Null
}

$ready = $false
for ($attempt = 0; $attempt -lt 20; $attempt++) {
    if ((Test-ServiceUrl 'http://127.0.0.1:8000/health') -and (Test-ServiceUrl 'http://127.0.0.1:5173/')) { $ready = $true; break }
    Start-Sleep -Milliseconds 750
}
if (-not $ready) { throw "Startup failed. Check the backend.stderr.log and frontend.stderr.log files in $logDirectory" }
Write-Host 'MineLand Nexus is ready: http://127.0.0.1:5173'
Write-Host 'Both services will keep running in the background. Run Open-MineLand.cmd to reopen the app.'
if (-not $NoBrowser) { Start-Process 'http://127.0.0.1:5173/' }
