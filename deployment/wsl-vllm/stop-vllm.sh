#!/usr/bin/env bash
# stop-vllm.sh — stops both model containers (does not remove them; weights
# and container config are preserved for the next `docker start` / the
# Desktop start_vllm.bat launcher).
set -euo pipefail
echo "[stop-vllm] Stopping vllm-qwen36 and vllm-nemotron-vision..."
docker stop vllm-qwen36 vllm-nemotron-vision 2>&1 || true
echo "[stop-vllm] Done. GPU memory should free up within a few seconds:"
nvidia-smi --query-gpu=index,memory.used,memory.total --format=csv 2>&1 || true
