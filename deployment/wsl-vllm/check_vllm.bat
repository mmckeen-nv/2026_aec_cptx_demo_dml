@echo off
setlocal
echo ============================================================
echo  vLLM status check (bac_teapot / aec-cptx demo, WSL2)
echo ============================================================
echo.

wsl -e bash -lc "docker ps -a --filter name=vllm-qwen36 --filter name=vllm-nemotron-vision --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"

echo.
echo --- chat (vllm-qwen36, :8000) ---
curl -s http://localhost:8000/v1/models
echo.
echo.
echo --- vision (vllm-nemotron-vision, :8001) ---
curl -s http://localhost:8001/v1/models
echo.
echo.
pause
