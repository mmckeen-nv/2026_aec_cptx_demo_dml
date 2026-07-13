@echo off
setlocal
set "NO_PAUSE=%~1"
echo ============================================================
echo  Starting vLLM models in WSL2 for BAC_Teapot demo
echo    chat:   vllm-qwen36          (nvidia/Qwen3.6-35B-A3B-NVFP4)   -> :8000  GPU0
echo    vision: vllm-nemotron-vision (Nemotron-3-Nano-Omni-30B-A3B)   -> :8001  GPU1
echo ============================================================
echo.

wsl -e bash -lc "docker start vllm-qwen36 vllm-nemotron-vision"
if errorlevel 1 (
    echo.
    echo ERROR: docker start failed. Check WSL2/Docker is running.
    echo If you see "address already in use" on port 8000 or 8001,
    echo a stray native/native process may be holding the port. Check with:
    echo   wsl -e bash -lc "ss -tlnp | grep -E ':(8000^|8001)'"
    if /I not "%NO_PAUSE%"=="--no-pause" pause
    exit /b 1
)

rem A running container can retain its configured port binding while losing
rem its actual bridge attachment. Repair that state before health checks.
wsl -e bash -lc "set -e; for c in vllm-qwen36 vllm-nemotron-vision; do if ! docker inspect -f '{{json .NetworkSettings.Networks}}' \"$c\" | grep -q bridge; then echo Repairing detached Docker network for $c...; docker network connect bridge \"$c\"; docker restart \"$c\" >/dev/null; fi; done"
if errorlevel 1 (
    echo.
    echo ERROR: Failed to verify or repair Docker bridge networking.
    if /I not "%NO_PAUSE%"=="--no-pause" pause
    exit /b 1
)

echo.
echo Containers started. Waiting for models to finish loading...
echo (this can take 1-4 minutes while weights load and compile)
echo.

set /a tries=0
:waitloop
set /a tries+=1
curl -s -o nul --max-time 3 http://localhost:8000/v1/models
set chat_status=%errorlevel%
curl -s -o nul --max-time 3 http://localhost:8001/v1/models
set vis_status=%errorlevel%

if "%chat_status%"=="0" if "%vis_status%"=="0" goto ready

if %tries% GEQ 48 (
    echo.
    echo Timed out after 4 minutes waiting for both endpoints.
    echo Check status manually:
    echo   curl http://localhost:8000/v1/models
    echo   curl http://localhost:8001/v1/models
    echo   wsl -e bash -lc "docker logs --tail 50 vllm-qwen36"
    echo   wsl -e bash -lc "docker logs --tail 50 vllm-nemotron-vision"
    if /I not "%NO_PAUSE%"=="--no-pause" pause
    exit /b 1
)

echo   [%tries%/48] chat(8000)=%chat_status% vision(8001)=%vis_status% - still loading...
rem ping provides a roughly five-second delay and works even when this batch
rem is invoked noninteractively by a PowerShell profile launcher.
%SystemRoot%\System32\ping.exe -n 6 127.0.0.1 >nul
goto waitloop

:ready
echo.
echo ============================================================
echo  Both models are up and responding.
echo    chat:   http://localhost:8000/v1
echo    vision: http://localhost:8001/v1
echo  You can now launch the BAC_Teapot Hermes profile.
echo ============================================================
if /I not "%NO_PAUSE%"=="--no-pause" pause
