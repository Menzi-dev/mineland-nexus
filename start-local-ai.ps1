$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$aiDirectory = Join-Path $PSScriptRoot '.local-ai'
$aiExecutable = Join-Path $aiDirectory 'runtime/llama-server.exe'
if (-not (Test-Path -LiteralPath $aiExecutable)) { throw 'Run python backend/setup_local_vision.py first.' }
try {
    $response = Invoke-WebRequest 'http://127.0.0.1:11435/health' -UseBasicParsing -TimeoutSec 2
    if ($response.StatusCode -eq 200) { Write-Host 'Local photo assistant is already running.'; exit 0 }
} catch { }
$aiLogDirectory = Join-Path $PSScriptRoot 'artifacts'
New-Item -ItemType Directory -Path $aiLogDirectory -Force | Out-Null
$aiArguments = @('-m', ('"' + (Join-Path $aiDirectory 'SmolVLM-256M-Instruct-Q8_0.gguf') + '"'),
    '--mmproj', ('"' + (Join-Path $aiDirectory 'mmproj-SmolVLM-256M-Instruct-Q8_0.gguf') + '"'),
    '--host', '127.0.0.1', '--port', '11435', '-c', '4096', '-t', '4', '--parallel', '1', '--alias', 'mineland-vision')
Start-Process -FilePath $aiExecutable -ArgumentList $aiArguments -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $aiLogDirectory 'vision.stdout.log') -RedirectStandardError (Join-Path $aiLogDirectory 'vision.stderr.log') | Out-Null
Write-Host 'Starting local photo assistant on loopback port 11435. Loading may take a few seconds.'
