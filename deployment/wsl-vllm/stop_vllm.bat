@echo off
setlocal
echo ============================================================
echo  Stopping vLLM models in WSL2 (bac_teapot / aec-cptx demo)
echo ============================================================
echo.

wsl -e bash -lc "docker stop vllm-qwen36 vllm-nemotron-vision"
if errorlevel 1 (
    echo.
    echo WARNING: docker stop reported an error. Containers may already be
    echo stopped, or WSL2/Docker may not be running. Check with:
    echo   wsl -e bash -lc "docker ps -a --filter name=vllm"
    pause
    exit /b 1
)

echo.
echo Containers stopped. GPU memory should free up within a few seconds.
wsl -e bash -lc "nvidia-smi --query-gpu=index,memory.used,memory.total --format=csv"
echo.
pause
