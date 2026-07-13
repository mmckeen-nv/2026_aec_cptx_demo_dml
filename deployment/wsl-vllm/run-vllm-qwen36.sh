#!/usr/bin/env bash
# run-vllm-qwen36.sh
#
# Creates (or, if it already exists, just starts) the vllm-qwen36 container:
# the CHAT model for the aec-cptx / bac_teapot Hermes profiles.
#   Model:  nvidia/Qwen3.6-35B-A3B-NVFP4
#   Port:   8000 (OpenAI-compatible /v1 API)
#   GPU:    0 (all GPUs visible; tensor-parallel-size=1 so it only uses one)
#
# Run inside the target WSL2 distro:
#   bash run-vllm-qwen36.sh
#
# IMPORTANT: HF_HUB_OFFLINE=1 / TRANSFORMERS_OFFLINE=1 are set when a complete
# local model snapshot is present. A fresh online installation leaves them
# unset so Hugging Face can download the model on first start.
# vLLM normally re-fetches HF image-processor/config metadata from
# huggingface.co on every single startup, even when the weights are already
# fully cached locally. On this machine's WSL2 networking, that outbound
# HF metadata call intermittently fails ("Temporary failure in name
# resolution" / "Cannot send a request, as the client has been closed"),
# which crashes the whole container on startup. Forcing offline mode makes
# vLLM load entirely from the local HF cache and skips that network call.
# Do not remove these two env vars without re-testing multiple cold starts.
#
# Idempotency: if a container named vllm-qwen36 already exists, this script
# just starts it (fast — seconds to ~2min depending on whether it needs to
# recompile CUDA graphs) instead of recreating it. Use --recreate to force
# a full docker rm + docker run (e.g. after intentionally changing flags
# below).

set -euo pipefail

RECREATE=0
if [ "${1:-}" = "--recreate" ]; then
    RECREATE=1
fi

NAME=vllm-qwen36
IMAGE=vllm/vllm-openai:latest
MODEL=nvidia/Qwen3.6-35B-A3B-NVFP4
PORT=8000
CACHE_ROOT=/root/.cache/huggingface
MODEL_CACHE=${CACHE_ROOT}/hub/models--nvidia--Qwen3.6-35B-A3B-NVFP4
OFFLINE_ENV=()
if [ -d "${MODEL_CACHE}/snapshots" ]; then
    # Transformers resolves trusted remote-code symlinks to hashed blobs in
    # offline mode, then looks for relative Python imports beside that blob by
    # filename. Add aliases to the existing blobs without duplicating data.
    for module in "${MODEL_CACHE}"/snapshots/*/*.py; do
        [ -e "${module}" ] || continue
        resolved=$(readlink -f "${module}")
        case "${resolved}" in
            "${MODEL_CACHE}/blobs/"*)
                alias="${MODEL_CACHE}/blobs/$(basename "${module}")"
                [ -e "${alias}" ] || ln -s "$(basename "${resolved}")" "${alias}"
                ;;
        esac
    done
    echo "[run-vllm-qwen36] Cached model snapshot found; enabling Hugging Face offline mode."
    OFFLINE_ENV=(-e HF_HUB_OFFLINE=1 -e TRANSFORMERS_OFFLINE=1)
else
    echo "[run-vllm-qwen36] No cached snapshot found; first start requires internet access."
fi

if docker ps -a --format '{{.Names}}' | grep -qx "$NAME"; then
    if [ "$RECREATE" = "1" ]; then
        echo "[run-vllm-qwen36] --recreate passed, removing existing container..."
        docker rm -f "$NAME"
    else
        echo "[run-vllm-qwen36] Container '$NAME' already exists, starting it..."
        docker start "$NAME"
        echo "[run-vllm-qwen36] Started. Poll http://localhost:${PORT}/v1/models until it returns 200."
        exit 0
    fi
fi

echo "[run-vllm-qwen36] Creating and starting '$NAME'..."
docker run -d --name "$NAME" \
  --gpus all \
  --shm-size=64m \
  --ipc=private \
  -p ${PORT}:${PORT} \
  -v /root/.cache/huggingface:/root/.cache/huggingface \
  "${OFFLINE_ENV[@]}" \
  "$IMAGE" \
  "$MODEL" \
  --host 0.0.0.0 --port ${PORT} \
  --tensor-parallel-size 1 \
  --trust-remote-code \
  --kv-cache-dtype fp8 \
  --attention-backend flashinfer \
  --moe-backend marlin \
  --gpu-memory-utilization 0.4 \
  --max-model-len 262144 \
  --max-num-seqs 4 \
  --max-num-batched-tokens 8192 \
  --enable-chunked-prefill \
  --async-scheduling \
  --enable-prefix-caching \
  --speculative-config '{"method":"mtp","num_speculative_tokens":3,"moe_backend":"triton"}' \
  --load-format fastsafetensors \
  --reasoning-parser qwen3 \
  --tool-call-parser qwen3_xml \
  --enable-auto-tool-choice

if [ ${#OFFLINE_ENV[@]} -gt 0 ]; then
    echo "[run-vllm-qwen36] Container created from the local Hugging Face cache."
else
    echo "[run-vllm-qwen36] Container created. First run downloads weights from HF (large, can take a while)."
fi
echo "[run-vllm-qwen36] Poll http://localhost:${PORT}/v1/models until it returns 200, or:"
echo "[run-vllm-qwen36]   docker logs -f ${NAME}"
