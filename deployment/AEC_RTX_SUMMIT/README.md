# AEC_RTX_SUMMIT

Connected installer for the AEC Cliff House demo.

Double-click `Setup-AEC-RTX-Summit.cmd`. The installer configures:

- Hermes with NVIDIA-hosted Claude Opus 4.5 using its 200,000-token context window.
- NVIDIA-hosted Nemotron 3 Nano Omni for 262K-context image inspection.
- Daystrom DML/CMA with the low-latency agent-memory fixes.
- The compact `qwen3-embedding:0.6b` Ollama embedding model.
- The verified Cliff House procedural-memory seed.
- ComfyUI 0.24.0 and the exact FLUX.2 Klein 4B FP8 model set used by the
  golden run.
- AEC Mission Control and the Desktop launchers, including
  `AEC_CLIFFHOUSE_CLI.bat` for direct Hermes CLI operation.

The installer does **not** include, copy, pull, provision, or start:

- vLLM or Docker inference containers.
- Qwen/Nemotron chat or vision models.
- Hugging Face model caches.
- SDXL or unrelated heavyweight model files.

The bundled image payload is approximately 11.6 GB and contains only:

- `flux-2-klein-base-4b-fp8.safetensors`
- `qwen_3_4b.safetensors`
- `flux2-vae.safetensors`

The installer verifies every model by byte size and SHA-256 before and after
copying. Models are stored as FAT32-safe 2 GiB chunks in the portable package
and reassembled automatically during installation. It creates an isolated
Python 3.13 ComfyUI runtime, installs the
official CUDA 13 PyTorch packages, and starts ComfyUI on
`http://127.0.0.1:8188`.

Rhino, Blender, and their application-side MCP add-ons remain machine
prerequisites for the complete visual workflow.

The demo source is installed under
`%LOCALAPPDATA%\AEC_RTX_SUMMIT\aec-demo`; desktop launchers do not depend on
the USB drive remaining connected.

Before installation, the portable package can be checked without changing the
machine:

```bat
Setup-AEC-RTX-Summit.cmd -SmokeTest
```

The smoke test parses every packaged PowerShell script, validates all payload
checksums, streams and verifies every model chunk, and performs a disposable
reassembly test.

The NVIDIA API key is requested securely during profile setup and stored only
in the ignored local Hermes profile environment.
