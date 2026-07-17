@echo off
setlocal EnableExtensions EnableDelayedExpansion
set "NO_PAUSE=%~1"
echo ============================================================
echo  Starting vLLM models in WSL2 for BAC_Teapot demo
echo    chat:   vllm-qwen36          (nvidia/Qwen3.6-35B-A3B-NVFP4)   -^> :8000  GPU0
echo    vision: vllm-nemotron-vision (Nemotron-3-Nano-Omni-30B-A3B)   -^> :8001  GPU1
echo ============================================================
echo.
echo Models start sequentially to avoid exhausting WSL memory while both
echo engines load weights and compile kernels at the same time.
echo.

call :start_model vllm-qwen36 8000 chat
if errorlevel 1 goto failed

call :start_model vllm-nemotron-vision 8001 vision
if errorlevel 1 goto failed

echo.
echo ============================================================
echo  Both models are up and responding.
echo    chat:   http://localhost:8000/v1
echo    vision: http://localhost:8001/v1
echo  Detached containers remain independent of this launcher window.
echo  On reboot, rerun this launcher for health-gated sequential startup.
echo ============================================================
if /I not "%NO_PAUSE%"=="--no-pause" pause
exit /b 0

:start_model
set "CONTAINER=%~1"
set "PORT=%~2"
set "ROLE=%~3"
echo Starting !ROLE! container !CONTAINER! on port !PORT!...
wsl -e bash -lc "set -e; docker update --restart no !CONTAINER! ^>/dev/null; docker start !CONTAINER! ^>/dev/null; if docker inspect -f '{{json .NetworkSettings.Networks}}' !CONTAINER! | grep -q bridge; then :; else echo Repairing detached Docker network for !CONTAINER!...; docker network connect bridge !CONTAINER!; docker restart !CONTAINER! ^>/dev/null; fi"
if errorlevel 1 (
    echo ERROR: Failed to start or repair !CONTAINER!.
    exit /b 1
)

set /a tries=0
:wait_model
set /a tries+=1
curl -s -o nul --max-time 3 http://localhost:!PORT!/v1/models
if not errorlevel 1 (
    echo   !ROLE! is ready on port !PORT!.
    exit /b 0
)

set "STATE=unknown"
for /f "usebackq delims=" %%S in (`wsl -e docker inspect -f "{{.State.Status}}" !CONTAINER! 2^>nul`) do set "STATE=%%S"
if /I not "!STATE!"=="running" (
    echo.
    echo ERROR: !CONTAINER! exited while loading.
    wsl -e docker logs --tail 80 !CONTAINER!
    exit /b 1
)

if !tries! GEQ 72 (
    echo.
    echo ERROR: Timed out after 6 minutes waiting for !CONTAINER!.
    wsl -e docker logs --tail 80 !CONTAINER!
    exit /b 1
)

echo   [!tries!/72] !ROLE!^(!PORT!^) is still loading...
rem ping provides a roughly five-second delay and works noninteractively.
%SystemRoot%\System32\ping.exe -n 6 127.0.0.1 >nul
goto wait_model

:failed
echo.
echo vLLM startup failed. The successful container, if any, remains running.
echo Inspect status with deployment\wsl-vllm\check_vllm.bat.
if /I not "%NO_PAUSE%"=="--no-pause" pause
exit /b 1
