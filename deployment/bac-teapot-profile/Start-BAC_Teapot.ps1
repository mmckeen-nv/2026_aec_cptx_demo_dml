$ErrorActionPreference = 'Stop'
$env:HERMES_HOME = 'C:\Users\test\AppData\Local\hermes'
$env:Path = 'C:\Users\test\AppData\Local\hermes\hermes-agent\venv\Scripts;C:\Users\test\AppData\Local\hermes\bin;' + [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')
Set-Location 'C:\Users\test'
Write-Host ''
Write-Host '============================================================'
Write-Host ' BAC_Teapot - Hermes Profile'
Write-Host ' Profile: bac_teapot'
Write-Host ' Model: nvidia/Qwen3.6-35B-A3B-NVFP4 (local vLLM, Docker/WSL2)'
Write-Host ' Vision: Nemotron-3-Nano-Omni-30B-A3B (local vLLM, Docker/WSL2)'
Write-Host ' Endpoint: http://localhost:8000/v1 (chat), :8001 (vision)'
Write-Host '============================================================'
Write-Host ''
& 'C:\Users\test\AppData\Local\hermes\hermes-agent\venv\Scripts\hermes.exe' -p bac_teapot chat
$code = $LASTEXITCODE
Write-Host ''
Write-Host "Hermes exited with code $code. Press Enter to close."
Read-Host | Out-Null
exit $code
