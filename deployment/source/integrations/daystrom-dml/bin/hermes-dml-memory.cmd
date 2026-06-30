@echo off
setlocal
set INTEGRATION_DIR=C:\Users\test\AppData\Local\hermes\integrations\daystrom-dml
set DAYSTROM_DML_VENV=%INTEGRATION_DIR%\.venv-dml
set DAYSTROM_DML_CORE=%INTEGRATION_DIR%\source\dml_core
set OPENCLAW_WORKSPACE=C:\Users\test\AppData\Local\hermes\workspace
set STORE_DEFAULT=%INTEGRATION_DIR%\stores\aec-cptx-runtime-store
set CONFIG_DEFAULT=%INTEGRATION_DIR%\config\aec-cptx-portable.yaml
set WRAPPER=%INTEGRATION_DIR%\scripts\dml_memory.py
set OLLAMA_EXE=C:\Users\test\AppData\Local\Microsoft\WinGet\Packages\Ollama.Ollama.Portable_Microsoft.Winget.Source_8wekyb3d8bbwe\ollama.exe
powershell -NoProfile -ExecutionPolicy Bypass -Command "if (-not (Test-NetConnection -ComputerName 127.0.0.1 -Port 11434 -InformationLevel Quiet)) { Start-Process -FilePath $env:OLLAMA_EXE -ArgumentList 'serve' -WindowStyle Hidden; Start-Sleep -Seconds 10 }" >nul 2>nul
"%DAYSTROM_DML_VENV%\Scripts\python.exe" "%WRAPPER%" --storage-dir "%STORE_DEFAULT%" --config-path "%CONFIG_DEFAULT%" %*
