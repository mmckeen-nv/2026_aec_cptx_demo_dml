# AEC_RTX_SUMMIT

Lightweight connected installer for the AEC Cliff House demo.

Double-click `Setup-AEC-RTX-Summit.cmd`. The installer configures:

- Hermes with NVIDIA-hosted Claude Opus 4.5 using its 200,000-token context window.
- NVIDIA-hosted Nemotron 3 Nano Omni for 262K-context image inspection.
- Daystrom DML/CMA with the low-latency agent-memory fixes.
- The compact `qwen3-embedding:0.6b` Ollama embedding model.
- The verified Cliff House procedural-memory seed.
- AEC Mission Control and the Desktop launchers.

The installer does **not** include, copy, pull, provision, or start:

- vLLM or Docker inference containers.
- Qwen/Nemotron chat or vision models.
- Hugging Face model caches.
- ComfyUI, FLUX, SDXL, or other heavyweight model files.

Rhino, Blender, their application-side MCP add-ons, and ComfyUI remain
machine prerequisites for the complete visual workflow. The Summit package
only installs the remote-agent and DML support path.

The NVIDIA API key is requested securely during profile setup and stored only
in the ignored local Hermes profile environment.
