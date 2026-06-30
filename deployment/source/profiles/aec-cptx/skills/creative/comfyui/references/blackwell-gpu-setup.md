# ComfyUI on Blackwell GPUs (RTX PRO 6000 / sm_120)

## Problem

PyTorch 2.6+cu124 does not support compute capability sm_120 (Blackwell).
ComfyUI starts but crashes on the first GPU operation with:

```
CUDA error: no kernel image is available for execution on the device
```

## Fix: PyTorch nightly with CUDA 12.8

```bash
# Bootstrap pip into the venv first if missing
python -m ensurepip

# Install PyTorch nightly with cu128 (supports sm_120)
python -m pip install --pre torch torchvision torchaudio \
  --index-url https://download.pytorch.org/whl/nightly/cu128 \
  --force-reinstall
```

Verify:
```bash
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
# Expected: 2.12.0.dev2026XXXX+cu128 True NVIDIA RTX PRO 6000 Blackwell Workstation Edition
```

## Dependency chain (Hermes venv)

ComfyUI's `requirements.txt` doesn't list all runtime dependencies. When
launching ComfyUI in a fresh venv, install these in order:

```bash
python -m pip install \
  sqlalchemy filelock aiosqlite alembic \
  comfy-aimdo \
  safetensors transformers tokenizers sentencepiece \
  einops scipy psutil torchsde \
  av \
  comfyui-workflow-templates comfyui-frontend-package
```

### numpy version mismatch

If pip installed numpy for a different Python version (e.g. Python 3.12
binaries in a Python 3.11 venv), you'll get `ModuleNotFoundError: No module
named 'numpy._core._multiarray_umath'`. Fix:

```bash
python -m pip install numpy --force-reinstall --no-deps
```

### --target installs are unreliable

`pip install --target <dir>` can leave broken partial installs (torch C
extensions fail to load). Always use `python -m pip install` (without
`--target`) once pip is bootstrapped into the venv.

## GPU detection

ComfyUI correctly detects dual Blackwell GPUs:
```
[INFO] Device: cuda:0 NVIDIA RTX PRO 6000 Blackwell Workstation Edition : cudaMallocAsync
[INFO] Device: cuda:1 NVIDIA RTX PRO 6000 Blackwell Workstation Edition : cudaMallocAsync
```

With 97GB VRAM per GPU, SDXL runs comfortably with no offloading needed.

## Launch command

```bash
cd "C:/Users/test/ComfyUI"
python main.py --listen 127.0.0.1 --port 8188
```

First launch takes 30-60s to initialize. Verify with:
```bash
curl -s http://127.0.0.1:8188/system_stats
```

## Blender 5.1 ShaderNodeMapRange pitfall

When rendering depth maps for ControlNet, `ShaderNodeMapRange` does NOT have
a `use_clamp` property in Blender 5.1. Clamping is on by default — do not set
it explicitly or the script will fail with a compile error.
