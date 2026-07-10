#!/usr/bin/env bash
# status-vllm.sh — quick health check for both model containers, runnable
# from inside WSL2. Windows-side callers should use check_vllm.bat instead.
set -uo pipefail

echo "=== docker ps ==="
docker ps -a --filter "name=vllm-qwen36" --filter "name=vllm-nemotron-vision" \
  --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo
echo "=== chat (vllm-qwen36, :8000) ==="
if curl -s --max-time 3 http://localhost:8000/v1/models; then
    echo
else
    echo "(no response)"
fi

echo
echo "=== vision (vllm-nemotron-vision, :8001) ==="
if curl -s --max-time 3 http://localhost:8001/v1/models; then
    echo
else
    echo "(no response)"
fi
