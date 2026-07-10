#!/usr/bin/env bash
# run-vllm-nemotron-vision.sh
#
# Creates (or, if it already exists, just starts) the vllm-nemotron-vision
# container: the VISION model for the aec-cptx / bac_teapot Hermes profiles.
#   Model:  nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-NVFP4
#   Port:   8001 (OpenAI-compatible /v1 API)
#   GPU:    1 (pinned via CUDA_VISIBLE_DEVICES/NVIDIA_VISIBLE_DEVICES=1, so it
#              never competes with the chat model on GPU 0)
#
# Run inside the target WSL2 distro:
#   bash run-vllm-nemotron-vision.sh
#
# Same offline-mode rationale as run-vllm-qwen36.sh applies here in
# principle, though this container has not crashed on the DNS issue in
# practice yet. If it starts crash-looping with an HF connection error,
# add HF_HUB_OFFLINE=1 / TRANSFORMERS_OFFLINE=1 the same way (see
# run-vllm-qwen36.sh for the exact env vars and reasoning), then
# `bash run-vllm-nemotron-vision.sh --recreate`.
#
# Idempotency: if a container named vllm-nemotron-vision already exists,
# this script just starts it instead of recreating it. Use --recreate to
# force a full docker rm + docker run.

set -euo pipefail

RECREATE=0
if [ "${1:-}" = "--recreate" ]; then
    RECREATE=1
fi

NAME=vllm-nemotron-vision
IMAGE=vllm/vllm-openai:latest
MODEL=nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-NVFP4
PORT=8001
GPU_INDEX=1

if docker ps -a --format '{{.Names}}' | grep -qx "$NAME"; then
    if [ "$RECREATE" = "1" ]; then
        echo "[run-vllm-nemotron-vision] --recreate passed, removing existing container..."
        docker rm -f "$NAME"
    else
        echo "[run-vllm-nemotron-vision] Container '$NAME' already exists, starting it..."
        docker start "$NAME"
        echo "[run-vllm-nemotron-vision] Started. Poll http://localhost:${PORT}/v1/models until it returns 200."
        exit 0
    fi
fi

echo "[run-vllm-nemotron-vision] Creating and starting '$NAME'..."
docker run -d --name "$NAME" \
  --gpus all \
  --shm-size=64m \
  --ipc=private \
  -p ${PORT}:${PORT} \
  -v /root/.cache/huggingface:/root/.cache/huggingface \
  -e CUDA_VISIBLE_DEVICES=${GPU_INDEX} \
  -e NVIDIA_VISIBLE_DEVICES=${GPU_INDEX} \
  "$IMAGE" \
  "$MODEL" \
  --host 0.0.0.0 --port ${PORT} \
  --tensor-parallel-size 1 \
  --trust-remote-code \
  --gpu-memory-utilization 0.85 \
  --max-model-len 65536

echo "[run-vllm-nemotron-vision] Container created. First run downloads weights from HF (large, can take a while)."
echo "[run-vllm-nemotron-vision] Poll http://localhost:${PORT}/v1/models until it returns 200, or:"
echo "[run-vllm-nemotron-vision]   docker logs -f ${NAME}"
