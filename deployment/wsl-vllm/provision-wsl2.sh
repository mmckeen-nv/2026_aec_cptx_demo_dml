#!/usr/bin/env bash
# provision-wsl2.sh
#
# Idempotent provisioning script for the WSL2 Ubuntu instance that hosts the
# vLLM model containers for the aec-cptx / bac_teapot Hermes profiles on
# the target Windows host.
#
# Run this INSIDE the target WSL2 distro (not from Windows):
#   wsl -d Ubuntu
#   bash provision-wsl2.sh
#
# What it does, in order, each step idempotent / safe to re-run:
#   1. Verifies this is actually WSL2 (not native Linux, not WSL1).
#   2. Verifies the NVIDIA driver is visible from inside WSL2 (nvidia-smi).
#   3. Installs Docker Engine (docker-ce) if not already present.
#   4. Installs the NVIDIA Container Toolkit (nvidia-ctk / nvidia-container-runtime)
#      if not already present, and configures Docker to use it.
#   5. Verifies GPU access from inside a container (nvidia-smi via docker run).
#   6. Pulls vllm/vllm-openai:latest.
#   7. Creates the shared HuggingFace cache dir at /root/.cache/huggingface
#      (both model containers mount this — weights are downloaded once and
#      reused across container recreations).
#   8. Prints next steps (run the model containers via run-vllm-*.sh).
#
# Known-good versions on the reference machine (2026-07-10):
#   Ubuntu 24.04.1 LTS (noble), Docker 29.6.1, nvidia-ctk 1.19.1,
#   host NVIDIA driver 596.59 / CUDA 13.2, 2x RTX PRO 6000 Blackwell (97GB each)
#
# This script does NOT download model weights — that happens automatically
# the first time each model container starts (see run-vllm-qwen36.sh /
# run-vllm-nemotron-vision.sh). First cold start per model can take a long
# time depending on network speed (35B-70B+ param models).

set -euo pipefail

log() { echo "[provision-wsl2] $*"; }
die() { echo "[provision-wsl2] ERROR: $*" >&2; exit 1; }

# --- 1. Confirm we're in WSL2 ---------------------------------------------
if ! grep -qi microsoft /proc/version 2>/dev/null; then
    die "This does not look like WSL. /proc/version does not mention Microsoft. Aborting."
fi
if [ -f /proc/sys/fs/binfmt_misc/WSLInterop ] || grep -qi wsl2 /proc/version 2>/dev/null; then
    log "Confirmed running inside WSL."
else
    log "WARNING: could not positively confirm WSL2 (vs WSL1). Continuing anyway."
fi

# --- 2. Confirm NVIDIA driver is visible -----------------------------------
if ! command -v nvidia-smi >/dev/null 2>&1; then
    die "nvidia-smi not found. Install/verify the NVIDIA driver on the Windows host and enable WSL2 GPU passthrough (this is a Windows-side driver install, not something this script can do)."
fi
log "nvidia-smi found. GPU summary:"
nvidia-smi --query-gpu=index,name,memory.total --format=csv || die "nvidia-smi ran but returned an error — GPU passthrough into WSL2 may be broken."

# --- 3. Install Docker Engine if missing -----------------------------------
if command -v docker >/dev/null 2>&1; then
    log "Docker already installed: $(docker --version)"
else
    log "Installing Docker Engine (docker-ce) via the official apt repo..."
    sudo apt-get update -y
    sudo apt-get install -y ca-certificates curl gnupg
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg
    ARCH=$(dpkg --print-architecture)
    CODENAME=$(. /etc/os-release && echo "$VERSION_CODENAME")
    echo \
      "deb [arch=${ARCH} signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu ${CODENAME} stable" \
      | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update -y
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    log "Docker installed: $(docker --version)"
fi

# WSL2 typically doesn't run systemd for Docker; start dockerd manually if not running.
if ! docker info >/dev/null 2>&1; then
    log "Docker daemon not responding — attempting to start it..."
    if command -v service >/dev/null 2>&1; then
        sudo service docker start || true
    fi
    sleep 2
    if ! docker info >/dev/null 2>&1; then
        # Fall back to starting dockerd directly in the background.
        sudo nohup dockerd >/tmp/dockerd.log 2>&1 &
        sleep 5
    fi
fi
docker info >/dev/null 2>&1 || die "Docker daemon still not responding after start attempts. Check /tmp/dockerd.log."
log "Docker daemon is running."

# --- 4. Install NVIDIA Container Toolkit if missing ------------------------
if command -v nvidia-ctk >/dev/null 2>&1; then
    log "NVIDIA Container Toolkit already installed: $(nvidia-ctk --version | head -1)"
else
    log "Installing NVIDIA Container Toolkit..."
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
      | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
    curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
      | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
      | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list > /dev/null
    sudo apt-get update -y
    sudo apt-get install -y nvidia-container-toolkit
    log "NVIDIA Container Toolkit installed: $(nvidia-ctk --version | head -1)"
fi

# Configure Docker to use the nvidia runtime (writes /etc/docker/daemon.json).
sudo nvidia-ctk runtime configure --runtime=docker
log "Restarting Docker to pick up nvidia runtime config..."
if command -v service >/dev/null 2>&1; then
    sudo service docker restart || true
    sleep 3
fi
docker info >/dev/null 2>&1 || die "Docker did not come back up after restart."

# --- 5. Verify GPU access from inside a container ---------------------------
log "Verifying GPU visibility from inside a test container..."
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi \
    || die "GPU not visible inside container. Check 'docker info' for the nvidia runtime and re-run 'nvidia-ctk runtime configure --runtime=docker'."
log "GPU visible inside containers. Good."

# --- 6. Pull the vLLM image --------------------------------------------------
log "Pulling vllm/vllm-openai:latest (this is a large image, can take a while)..."
docker pull vllm/vllm-openai:latest

# --- 7. Create shared HF cache dir ------------------------------------------
sudo mkdir -p /root/.cache/huggingface
log "HuggingFace cache dir ready at /root/.cache/huggingface"

log ""
log "Provisioning complete. Next steps:"
log "  1. Copy run-vllm-qwen36.sh and run-vllm-nemotron-vision.sh into this WSL2 distro"
log "     (or run them directly from the Windows-mounted repo path, e.g."
log "     /mnt/c/Users/<windows-user>/<repo>/deployment/wsl-vllm/)."
log "  2. bash run-vllm-qwen36.sh          # first run downloads the chat model weights"
log "  3. bash run-vllm-nemotron-vision.sh # first run downloads the vision model weights"
log "  4. Verify: curl http://localhost:8000/v1/models && curl http://localhost:8001/v1/models"
log "  5. On subsequent Windows sessions, just double-click Desktop\\start_vllm.bat"
log "     (it runs 'docker start' on both already-configured containers — much faster"
log "     than recreating them, since weights are already cached)."
