# Demo Pack Dependencies

Audience: an AI agent (Hermes) being asked to stand up this demo pack on a
new machine, from a single prompt like "deploy the demo pack." This file
is the dependency manifest + step-by-step deploy playbook. Read this
BEFORE touching the demos themselves.

Run the executable preflight before copying commands from this document:

```bash
python scripts/aec_setup.py --check --tier viewer
python scripts/aec_setup.py --check --tier agent
python scripts/aec_setup.py --check --tier enhancement
python scripts/aec_setup.py --check --tier full
```

`--configure` creates an ignored machine-local environment file. `--install`
offers supported package-manager commands interactively and then rechecks the
machine. Commercial software, private source, model weights, and credentials
remain explicit manual steps.

Scope note: Maya and Unreal Engine are SHELVED. Do not install or wire up
either. The Teapot demo is Blender-only (see `teapot/` — no `.fbx`, no UE
import script). If a user asks to revive Maya/UE support, treat that as a
new request requiring explicit confirmation, not something to infer from
this file.

---

## 1. What's actually needed, per demo

| Demo | Hard requirements | Optional / enhances |
|---|---|---|
| Cliff House (build-from-ground-up) | Blender 4.0+ (built/tested on 5.1) | Rhino 8 + rhino3dm (source geometry originated there; not required to just open/render the `.blend`) |
| Cliff House Modification | Blender 4.0+, ComfyUI + SDXL checkpoint + depth ControlNet model | comfy-cli (convenience layer over ComfyUI's REST API) |
| Virtual Production Studio | Blender 4.0+ | Rhino 8 + rhino3dm (base model source), ComfyUI (enhanced passes) |
| Teapot | Blender 4.0+ | — (fully self-contained, no external deps beyond Blender itself) |
| **Agent-driven continuity** | **Daystrom DML — REQUIRED for persistent agent memory, see Section 2.5** | — |

Nothing in this pack requires Maya, Unreal Engine, or Windows specifically
— Blender and ComfyUI both run natively on Linux, and Rhino (Windows/macOS
only) is optional/source-only, not required to run the demos as shipped.
Daystrom DML is required for the persistent agent-memory workflow and needs a
CUDA GPU + Ollama. It is not required to open or render the packaged Blender
scenes without Hermes.

---

## 2. Core stack

### 2.1 Blender (required for all 4 demos)

- Version: 4.0 or newer. This pack was authored/tested on **Blender 5.1**.
- **Windows:** install from https://www.blender.org/download/ or via
  winget: `winget install BlenderFoundation.Blender`
- **Linux / WSL2:** either the distro package or the official tarball —
  package managers often lag several versions behind, prefer the tarball
  for anything requiring 4.x+ features:
  ```bash
  # Ubuntu/Debian via snap (simplest, auto-updates):
  sudo snap install blender --classic

  # OR official tarball (pin an exact version):
  wget https://download.blender.org/release/Blender5.1/blender-5.1.2-linux-x64.tar.xz
  tar xf blender-5.1.2-linux-x64.tar.xz
  export PATH="$PWD/blender-5.1.2-linux-x64:$PATH"   # add to ~/.bashrc to persist
  ```
- **WSL2 specifically:** Blender's GUI needs an X server or WSLg (bundled
  with Windows 11 / recent Windows 10 WSL2 builds). For headless
  builds/renders (`--background`), no GUI/X server is needed at all — this
  is the recommended path for WSL2 agents driving this pack, since it
  sidesteps WSLg entirely. Verify GPU passthrough for Cycles rendering:
  ```bash
  nvidia-smi   # should show the GPU(s) from inside WSL2
  ```
  If `nvidia-smi` fails inside WSL2, install the NVIDIA CUDA driver for
  WSL from https://developer.nvidia.com/cuda/wsl — do NOT install a
  Linux GPU driver inside WSL2 itself, it uses the Windows host driver via
  passthrough.
- Verify install (either platform):
  ```bash
  blender --version
  ```

### 2.2 Blender MCP addon + bridge (required to drive Blender live from Hermes)

The agent controls Blender live via the `blender-mcp` bridge, not just by
running headless scripts. Two pieces:

1. **Blender-side addon** — `blender_mcp_addon.py`, installed into
   Blender's user addons directory and enabled. Find the directory from
   inside Blender:
   ```python
   import bpy, os
   print(os.path.join(bpy.utils.user_resource('SCRIPTS'), 'addons'))
   # Windows: C:\Users\<user>\AppData\Roaming\Blender Foundation\Blender\<ver>\scripts\addons
   # Linux:   ~/.config/blender/<ver>/scripts/addons
   ```
   Enable via Blender's Preferences > Add-ons, or headlessly:
   ```python
   bpy.ops.preferences.addon_enable(module="blender_mcp_addon")
   ```
   This starts a local TCP listener (default `localhost:9876`) that the
   MCP server talks to.

2. **Hermes-side MCP server config** — in `~/AppData/Local/hermes/config.yaml`
   (Windows) or `~/.hermes/config.yaml` (Linux), under `mcp_servers:`:
   ```yaml
   mcp_servers:
     blender:
       command: cmd            # Windows
       args: ["/c", "uvx", "blender-mcp"]
       env:
         BLENDER_HOST: localhost
         BLENDER_PORT: "9876"
         DISABLE_TELEMETRY: "true"
       connect_timeout: 30
       timeout: 180
   ```
   On Linux, drop the `cmd`/`/c` wrapper and call `uvx` directly:
   ```yaml
   mcp_servers:
     blender:
       command: uvx
       args: ["blender-mcp"]
       env:
         BLENDER_HOST: localhost
         BLENDER_PORT: "9876"
       connect_timeout: 30
       timeout: 180
   ```
   Requires `uv`/`uvx` on PATH (`pip install uv` or the official installer
   at https://docs.astral.sh/uv/getting-started/installation/).

3. **Verify the bridge is live** before assuming any `mcp_blender_*` tool
   call will work: Blender must already be running with the addon enabled
   BEFORE the MCP server process starts, or the handshake fails silently.
   Symptom of a dead bridge: MCP tool calls hang until `connect_timeout`
   then error. Fix: start Blender first, confirm the addon's "BlenderMCP
   server started on localhost:9876" line appears in Blender's system
   console/terminal output, THEN let Hermes connect.

### 2.3 ComfyUI (required only for Cliff House Modification; optional/enhances VP Studio)

- Version: this pack was built against ComfyUI **0.24.0**.
- **Windows (native, not WSL2)** — this is how it's set up on the
  reference machine:
  ```bash
  git clone https://github.com/comfyanonymous/ComfyUI.git
  cd ComfyUI
  python -m venv .venv
  .venv\Scripts\python.exe -m pip install -r requirements.txt
  .venv\Scripts\python.exe -m pip install torch --index-url https://download.pytorch.org/whl/cu121  # match your CUDA version
  ```
  Launch (do NOT use a `.bat` wrapper that redirects output with `>>` —
  it can exit before the server actually starts; launch the interpreter
  directly and track the process):
  ```bash
  .venv\Scripts\python.exe main.py --listen 0.0.0.0 --port 8188 --enable-manager
  ```
- **Linux / WSL2:**
  ```bash
  git clone https://github.com/comfyanonymous/ComfyUI.git
  cd ComfyUI
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  pip install torch --index-url https://download.pytorch.org/whl/cu121
  python main.py --listen 0.0.0.0 --port 8188 --enable-manager
  ```
- Verify readiness:
  ```bash
  curl -s http://127.0.0.1:8188/system_stats
  ```
  A 200 response listing your GPU(s) under `devices` means it's fully up.
- Recommended CLI layer (optional but used by the `comfyui` skill's
  scripts): `comfy-cli`
  ```bash
  pip install comfy-cli
  comfy setup --where local
  comfy tracking disable
  ```

#### Required models

| Model | Used by | Install |
|---|---|---|
| `sd_xl_base_1.0.safetensors` (SDXL base checkpoint) | Cliff House Modification | Install from the official `stabilityai/stable-diffusion-xl-base-1.0` model card or ComfyUI Manager |
| An SDXL-compatible depth ControlNet | Cliff House Modification (depth-conditioned img2img) | Install through ComfyUI Manager and verify that it appears in `ControlNetLoader`; model filenames vary by release |

Verify both are present:
```bash
curl -s http://127.0.0.1:8188/object_info
python scripts/comfyui_phase7.py --dry-run
```

#### GPU / hardware

- This pack targets a machine with substantial VRAM (reference machine:
  2x RTX PRO 6000 Blackwell, 97GB VRAM each). SDXL + ControlNet needs
  **≥8GB VRAM minimum**, more comfortably 12GB+.
- If the target machine has no capable GPU, use Comfy Cloud instead of a
  local install — see the `comfyui` skill's Path A for setup. This
  requires a paid Comfy Cloud subscription for actual workflow execution
  (free tier is read-only).

### 2.5 Daystrom DML (REQUIRED — agent project-memory / cookbook layer)

Daystrom DML ("Concept Memory Adapter" / `cma` package internally) is a
Hermes plugin that gives the agent persistent, project-scoped recall
across sessions — cookbook recipes, prior decisions, retrieval-augmented
context for this specific project. It is **not optional** for this demo
pack: without it, the agent has no memory of prior cliff-house/VP-studio
work between sessions and will re-derive things (or ask questions) that
DML would otherwise answer from its store.

**Hard requirements — no CPU fallback:**
- A CUDA-capable NVIDIA GPU. The config pins `embedding_device: cuda` and
  `strict_embedding_required: true` / `strict_llm_required: true` — DML
  will refuse to run in a degraded CPU-only mode rather than silently
  working slower. Verify:
  ```bash
  nvidia-smi
  ```
- **Ollama**, running locally, serving two specific models:
  ```bash
  # Install Ollama: https://ollama.com/download (Windows/Linux/macOS)
  ollama pull qwen3-embedding:0.6b   # embeddings (639MB)
  ollama pull llama3:8b              # summarization/LLM backend (4.7GB)
  # Verify the server is up:
  curl -fsS http://127.0.0.1:11434/api/version
  ```
  DML's launcher script auto-starts Ollama if it's not already running
  (see `bin/hermes-dml-memory.cmd` — checks the API, starts `ollama serve`
  if unreachable), but the two models above must be pulled manually first.

**Install (Windows — reference machine layout):**
```bash
# 1. Get the Daystrom source recorded in deployment/SOURCE_VERSIONS.md into:
#    <hermes_home>/integrations/daystrom-dml/source/

# 2. Create a dedicated venv (Python 3.10+) and install:
cd <hermes_home>/integrations/daystrom-dml
python -m venv .venv-dml
.venv-dml\Scripts\python.exe -m pip install -e source/
.venv-dml\Scripts\python.exe -m pip install torch --index-url https://download.pytorch.org/whl/cu128  # match your CUDA version
.venv-dml\Scripts\python.exe -m pip install faiss-cpu

# 3. Verify CUDA is visible to THIS venv specifically (not just system-wide):
.venv-dml\Scripts\python.exe -c "import torch; print('cuda available:', torch.cuda.is_available())"
# must print: cuda available: True
```

**Install (Linux / WSL2):** same steps, POSIX paths:
```bash
cd <hermes_home>/integrations/daystrom-dml
python3 -m venv .venv-dml
source .venv-dml/bin/activate
pip install -e source/
pip install torch --index-url https://download.pytorch.org/whl/cu128
pip install faiss-cpu
python -c "import torch; print('cuda available:', torch.cuda.is_available())"
```
On WSL2, this depends on the same NVIDIA CUDA-for-WSL driver setup called
out in Section 2.1 — verify `nvidia-smi` works inside WSL2 BEFORE
installing the DML venv, not after.

**Config** (`integrations/daystrom-dml/config/<project>-portable.yaml`):
```yaml
capacity: 4000
dml_top_k: 8
token_budget: 800
embedding_model: ollama:qwen3-embedding:0.6b
embedding_device: cuda
strict_embedding_required: true
llm_backend: ollama
model_name: llama3:8b
strict_llm_required: true
storage_dir: <hermes_home>/integrations/daystrom-dml/stores/<project>-runtime-store
ingest_persist_mode: dml_only
persistence:
  enable: true
  path: ./dml_state.jsonl
  interval_sec: 120
rag_store:
  enable: true
  path: ./rag_index.faiss
  meta_path: ./rag_meta.json
  backend: faiss
  dim: 1024
dpm:
  enable: true
  mode: active-write
  preference_graph_path: ./dpm_preference_graph.json
  relationship_id: relationship:<your-relationship-id>
  project_id: project:<your-project-id>
  token_budget: 80
agentic_mode:
  enabled: true
  schema_validation: true
  promotion_pipeline: true
  scratch_to_durable_threshold: 0.7
```

**Wire into Hermes** — `config.yaml`:
```yaml
memory:
  provider: daystrom_dml
  nudge_interval: 10
  flush_min_turns: 6
  daystrom_dml:
    client_id: <your-client-id>
    config_path: <hermes_home>/integrations/daystrom-dml/config/<project>-portable.yaml
    integration_dir: <hermes_home>/integrations/daystrom-dml
    launcher: <hermes_home>/integrations/daystrom-dml/bin/hermes-dml-memory.cmd  # .sh on Linux
    max_context_chars: 5000
    no_require_gpu: true   # NOTE: this flag exists but strict_*_required in
                            # the DML config above still hard-fails without a
                            # GPU — don't rely on this flag alone to make DML optional
    project_id: project:<your-project-id>
    relationship_id: relationship:<your-relationship-id>
    retrieval_policy: always
    source_dir: <hermes_home>/integrations/daystrom-dml/source
    storage_dir: <hermes_home>/integrations/daystrom-dml/stores/<project>-runtime-store
    sync_turns: true
    tenant_id: <your-tenant-id>
    timeout_seconds: 20
    top_k: 8
    venv_python: <hermes_home>/integrations/daystrom-dml/.venv-dml/Scripts/python.exe  # .venv-dml/bin/python3 on Linux
    enable_memory: true
    enable_personality: true
    dcn:
      mode: active_read
plugins:
  enabled:
    - daystrom_dml
```

**Verify end-to-end:**
```bash
# 1. Ollama serving both models:
curl -s http://127.0.0.1:11434/api/version
ollama list | grep -E "qwen3-embedding|llama3:8b"

# 2. DML venv has CUDA:
<venv_python> -c "import torch; print(torch.cuda.is_available())"

# 3. Launcher runs without error (smoke test):
<hermes_home>/integrations/daystrom-dml/bin/hermes-dml-memory.cmd --help
```

**Note on the store itself:** the DML runtime store
(`stores/<project>-runtime-store/`, ~12MB on the reference machine) holds
this project's accumulated cookbook/recipe knowledge (e.g. proven ComfyUI
workflow recipes, prior debugging findings). It is **not** part of the
portable `demos/` bundle — DML is a Hermes-profile-level integration, not
demo-specific data. If you need that accumulated knowledge on a new
machine, copy the `stores/` directory across separately; ask the user
before doing so, since it may contain session-specific context not meant
to travel automatically.

### 2.6 Rhino 8 + rhino3dm (optional — source geometry only)

Rhino itself is **Windows/macOS only**, and is NOT required to run any
demo — the `.3dm` files in this pack are source/reference geometry only;
the actual demos run from `.blend`/`.obj` files that don't need Rhino to
open. Skip this section entirely unless the user specifically wants to
re-derive geometry from the original Rhino source files.

If needed anyway:
- Rhino 8: https://www.rhino3d.com/download/ (Windows/macOS, paid license)
- `rhino3dm` (Python bindings, cross-platform, free, used for
  script-level `.3dm` inspection without a Rhino license):
  ```bash
  pip install rhino3dm
  ```
  Note: on this reference machine, the git-bash default `python` resolves
  to the Hermes venv, which does NOT have `rhino3dm`. Use the system
  Python explicitly:
  the interpreter returned by `py -0p` or
  `python -c "import sys; print(sys.executable)"`.
  On Linux this is less likely to be an issue — a single system Python
  with `pip install rhino3dm` is normally sufficient.

---

## 3. Deploy playbook (what an agent should do given "deploy the demo pack")

Given a fresh machine and a prompt like "deploy this demo pack, get as
much running as possible," an agent should work through this checklist,
skipping/flagging steps that can't complete rather than stopping outright:

1. **Detect platform** — Windows-native, WSL2, or native Linux. Check via
   `uname -a` (WSL2 kernel string contains "microsoft") or
   `$OSTYPE`/`sys.platform` if scripting.
2. **Copy the `demos/` directory** to the target machine — this whole
   folder is portable by design (see `README.md` at the demos root). No
   other files from the original machine are required.
3. **Install Blender** (Section 2.1) — required unconditionally. Verify
   with `blender --version` before proceeding.
4. **Set up Daystrom DML** (Section 2.5) — REQUIRED, not optional. Verify
   GPU (`nvidia-smi`), pull the two Ollama models, build the `.venv-dml`
   venv with CUDA torch, confirm `torch.cuda.is_available()` is `True`
   inside that venv specifically, then wire `plugins.enabled` and
   `memory.provider` in `config.yaml`. Do this BEFORE the Blender-only
   canary step below, since DML has no CPU fallback and its absence
   should be surfaced early, not discovered mid-task later.
5. **Try each demo Blender-only next**, since 2 of 4 demos need nothing
   else:
   - Teapot: `blender --background --python demos/teapot/build_teapot_demo.py -- --render <path>`
     — should succeed with zero other dependencies. Use this as the
     canary: if this fails, something is wrong with the Blender install
     itself, fix that before going further.
   - Virtual Production Studio: open `vp_studio_01_scene.blend` directly
     in Blender; renders/exports/comfy_enhanced are pre-built and don't
     require regenerating anything.
   - Cliff House: open `cliff_house/hero/cliff_house_02_HERO.blend`
     directly — pre-built, no regeneration needed for basic viewing.
6. **Set up the Blender MCP bridge** (Section 2.2) only if the user wants
   the agent to actively drive/modify the Blender scene live (not needed
   just to open/render existing `.blend` files headlessly).
7. **Set up ComfyUI** (Section 2.3) only if the user wants to (re)run the
   Cliff House Modification stylization pass, or regenerate VP Studio's
   `comfy_enhanced/` outputs. If GPU is inadequate, offer Comfy Cloud
   instead of failing outright.
8. **Skip Rhino entirely** unless the user explicitly asks to re-derive
   geometry from `.3dm` source files — flag this as optional/skipped in
   your summary rather than silently omitting it.
9. **Report a clear per-demo status** at the end: which demos are fully
   working, which are degraded (e.g. "VP Studio opens but comfy_enhanced
   regeneration needs ComfyUI, which isn't installed"), and which
   dependencies were skipped and why. Don't claim full success if any
   piece silently failed — and don't claim success on DML if
   `strict_embedding_required`/`strict_llm_required` would fail at
   runtime due to missing GPU/Ollama, even if the config file itself
   was written correctly.

### Fast path — if the ONLY goal is "show me the demos exist and look right"

Skip ComfyUI/Rhino/MCP entirely. Just:
```bash
blender --background --python demos/teapot/build_teapot_demo.py -- --render /tmp/teapot.png
blender --background --python -c "import bpy; bpy.ops.wm.open_mainfile(filepath='demos/cliff_house/hero/cliff_house_02_HERO.blend'); bpy.context.scene.render.filepath='/tmp/cliffhouse.png'; bpy.ops.render.render(write_still=True)"
```
This proves Blender + the two self-contained demos work, in under a
minute, without touching ComfyUI/MCP/Rhino at all.

---

## 4. Known pitfalls (carried over from hands-on debugging this session)

- **Don't trust a `.bat`/wrapper launcher for ComfyUI** — it can look
  like it started a background server and actually exit immediately.
  Launch the venv's `python.exe`/`python3` directly with an explicit
  working directory and track the real PID.
- **`curl /system_stats` is the real ComfyUI readiness signal** — a log
  line saying "Starting server" is necessary but not sufficient.
- **The in-Blender `ComfyUI-BlenderAI-node` addon is broken** on
  Blender 5.1 (Python 3.13) due to a `lupa`/LuaJIT native-dependency gap,
  and even after patching it has an unresolved deadlock in
  `addon_enable()`. Do not enable this addon — use the standalone
  `comfyui` skill's REST scripts instead (that's what this pack's
  Cliff House Modification demo actually uses). Full root-cause writeup:
  `blender-comfyui-integration` skill.
- **WSL2 `wsl -l -v` output is UTF-16 and looks like garbage in git-bash**
  unless you force `chcp.com 65001` first and pipe through `cat -v`.
- **Git-bash's default `python` may not be the same interpreter you
  expect** (on the reference machine it resolves into the Hermes agent's
  own venv, which lacks `rhino3dm` etc.) — always verify
  `python -c "import sys; print(sys.executable)"` before assuming a
  package is/isn't installed.
- **MiDaS depth ControlNet conditioning loses thin geometry** (e.g. a
  diving board) — if regenerating Cliff House Modification's stylized
  render and a thin feature vanishes, this is expected; see the `comfyui`
  skill's MiDaS pitfall section before re-prompting blindly.
- **Daystrom DML has no CPU fallback by design** — `strict_embedding_required`
  and `strict_llm_required` in its config mean a missing GPU or an
  unreachable Ollama server causes a hard failure, not degraded
  performance. The `no_require_gpu: true` flag in the Hermes-side
  `memory.daystrom_dml` config block does NOT override this — it's a
  separate, narrower flag; don't assume setting it makes DML optional.
  If the target machine has no CUDA GPU, DML plainly cannot run there —
  say so rather than half-configuring it.

---

## 5. Summary table — minimum viable install per platform

| Platform | Blender | ComfyUI | Daystrom DML | Rhino/rhino3dm | Blender MCP bridge |
|---|---|---|---|---|---|
| Windows (native) | winget/installer | native venv (see 2.3) | Ollama (winget) + `.venv-dml` w/ CUDA torch (see 2.5) | optional, Windows-native only | `uvx blender-mcp` via `cmd` |
| Linux (native) | snap or tarball | native venv, same as Windows minus `.bat` concerns | Ollama (native install) + `.venv-dml` w/ CUDA torch | rhino3dm only (no Rhino GUI) | `uvx blender-mcp` directly |
| WSL2 | tarball + WSLg (GUI) or headless-only (no WSLg needed) | native venv inside WSL2, verify `nvidia-smi` passthrough first | same as Linux native, but verify `nvidia-smi` CUDA-for-WSL passthrough BEFORE building the DML venv | rhino3dm only; Rhino GUI itself must run on the Windows host, not WSL2 | `uvx blender-mcp` inside WSL2, `BLENDER_HOST`/`PORT` must reach the Blender process (same WSL2 instance, or use Windows host IP if Blender runs on the Windows side) |

Maya and Unreal Engine: **not required by any demo in this pack, not
covered by this file, do not install.**
