# AEC CPTX Demo — AI Architectural Visualization Pipeline

A live demonstration of an AI agent (Hermes Agent) autonomously building
3D architectural/product visualization content — driving Rhino via MCP,
rendering and shading in Blender, and optionally stylizing output through
ComfyUI — in real time, with an audience watching. The agent runs with
persistent cross-session memory via the Daystrom DML/DCN plugin, so it
can pick a project back up across sessions without re-deriving context.

**Active project:** `cliff_house_02` — a modernist 3-storey cliff house
with cantilevered floors, west-facing ocean views, white ashlar stone,
and bronze glazing.

---

## What this is

This is not a plugin or a script library. It is a **prompt engineering
system** — a structured set of phase prompts, skills, and operating rules
that instruct an AI agent to:

1. Read a plain-English design brief
2. Build a Rhino 3D model step by step via MCP
3. Export and render in Blender
4. Produce final images via ComfyUI (optional)

The agent does the work. The human watches, approves, and steers.

---

## Demo lineup

The portable demo bundle lives under [`demos/`](demos/) — see
[`demos/README.md`](demos/README.md) for the full structure and
[`demos/DEPENDENCIES.md`](demos/DEPENDENCIES.md) for the per-demo
dependency manifest and deploy playbook.

| Demo | What it shows | Hard requirements |
|------|---------------|--------------------|
| **Cliff House** (build-from-ground-up) | Full Rhino → Blender pipeline, phase-by-phase | Blender 4.0+ (built/tested on 5.1); Rhino 8 + rhino3dm optional (source geometry only) |
| **Cliff House Modification** | Iterative design changes (material swaps, geometry edits) + ComfyUI stylization pass | Blender 4.0+, ComfyUI + SDXL checkpoint + depth ControlNet |
| **Virtual Production Studio** | LED volume / brain bar visualization, multiple camera angles, ComfyUI-enhanced passes | Blender 4.0+; Rhino/ComfyUI optional (source + enhancement only) |
| **Teapot** | Blender-only material/shading test scene (Utah teapot); converted from an earlier Unreal Engine version on 2026-07-10 | Blender 4.0+ only, fully self-contained |
| **All demos (agent memory layer)** | Cross-session project memory + iteration-budget policy via Daystrom DML/DCN | **Required** — CUDA GPU + Ollama, see below |

Maya and Unreal Engine are **shelved** — not required by any current demo,
not covered by this repo's tooling, do not install without an explicit
new request.

---

## Prerequisites

| Tool | Purpose | Notes |
|------|---------|-------|
| [Hermes Agent](https://hermes-agent.nousresearch.com) | AI agent runtime | Model/provider is configured per-deployment (this pack's reference deployment runs a custom NVIDIA-compatible endpoint, not a fixed Anthropic-only setup — see `deployment/aec-cptx-profile/config.example.yaml`) |
| [Rhinoceros 3D](https://www.rhino3d.com) (v7+) | 3D modeling | Windows only; optional — only needed to re-derive geometry from `.3dm` source, not to open/render existing `.blend` files |
| Rhino MCP server | Rhino ↔ agent bridge | localhost:3001; only needed alongside Rhino |
| [Blender](https://www.blender.org) (4.0+) | Rendering | Built/tested on Blender 5.1. Runs natively on Windows and Linux |
| Blender MCP bridge (`uvx blender-mcp`) | Blender ↔ agent bridge | localhost:9876 (TCP); only needed for live agent-driven scene edits, not for opening/rendering existing files headlessly |
| [ComfyUI](https://github.com/comfyanonymous/ComfyUI) | AI post-processing / stylization | Optional — only for the Cliff House Modification demo and VP Studio's enhanced passes |
| **Daystrom DML/DCN** | Agent memory + iteration-budget policy | **Required for the agent memory layer** across all demos. Needs a CUDA GPU + a local Ollama server (embedding + LLM models) — see `demos/DEPENDENCIES.md` §2.5. No CPU fallback by design (`strict_embedding_required`/`strict_llm_required`); Hermes's own `no_require_gpu` config flag does **not** override this |
| [OBS Studio](https://obsproject.com) | Screen capture | Only for demo recording |

Full per-platform (Windows / Linux / WSL2) install steps for everything
above: [`demos/DEPENDENCIES.md`](demos/DEPENDENCIES.md).

---

## Quick start

### Fastest path — just prove the demos work

No Rhino, ComfyUI, or MCP required. From a Blender install alone:

```bash
blender --background --python demos/teapot/build_teapot_demo.py -- --render /tmp/teapot.png
```

Or open any of the pre-built scenes directly in Blender:
`demos/cliff_house/hero/cliff_house_02_HERO.blend`,
`demos/virtual_production_studio/vp_studio_01_scene.blend`.

### Full agent-driven rebuild path

1. Clone this repo
2. Install/verify Daystrom DML/DCN (`demos/DEPENDENCIES.md` §2.5) — do
   this before anything else; it's required, not optional, and its
   absence is easier to catch early than mid-task
3. Open Hermes with this directory as the working root
4. Open Rhino and start the MCP server (only if rebuilding geometry from
   scratch rather than working from the pre-built `.blend`/`.3dm` files)
5. Tell Hermes: **"Resume cliff_house_02"**
6. Hermes reads the session startup sequence and asks what to build next

See [SETUP.md](SETUP.md) for detailed MCP server configuration.

### Current remote demo deployment

The working AEC demo server deployment is captured under
[`deployment/`](deployment/):

- `deployment/aec-cptx-profile/` — sanitized Hermes `aec-cptx` profile
  artifacts copied from the remote server.
- `deployment/windows-launchers/` — Windows desktop launcher scripts
  verified to start the interactive `aec-cptx` Hermes shell.
- `deployment/source/` — captured Hermes Agent source, Daystrom DML
  integration source, and the active profile Daystrom plugin copy from
  the working remote deployment.

Verified remote target:

| Item | Value |
|------|-------|
| Windows host | `DESKTOP-14FNBB2` |
| Windows user | `test` |
| Hermes profile | `aec-cptx` |
| Profile path | `C:\Users\test\AppData\Local\hermes\profiles\aec-cptx` |
| Desktop launcher path | `C:\Users\test\Desktop` |
| Best manual launcher | `START_HERMES_AEC_CPTX.cmd` |

Use `deployment/aec-cptx-profile/config.example.yaml` as a redacted
reference for the live profile posture. Do **not** commit live `.env`,
auth files, `state.db`, session logs, caches, or DML runtime stores.

**Daystrom DML/DCN posture (current, both root/default and `aec-cptx`
profiles on the reference machine):** `memory.provider: daystrom_dml`,
`memory.daystrom_dml.dcn.mode: active_read`, plugin listed in
`plugins.enabled`. This has been explicitly reaffirmed via
`hermes config set` on both profiles (not just relying on whatever was
already on disk) and verified live via `hermes memory status` on each —
both report `Plugin: installed ✓`, `Status: available ✓`, and
`daystrom_dml ← active`. Real DCN iteration-budget-extension decisions
(`decide_iteration_extension`) have been confirmed firing in production
session logs, not just in the plugin's own smoke test. New profiles
created with `hermes profile create <name> --clone` inherit the
**config** for this automatically since it's baked into the root config
— but **not the plugin files themselves**: `--clone` does not copy
`plugins/`, so a freshly-cloned profile can show the right config while
the plugin is genuinely not installed. This bit `BAC_Teapot` (see
`deployment/README.md`'s BAC_Teapot section) — fixed the same day by
copying the plugin directory in from the shared root location. Always
verify with `hermes -p <profile> memory status` after any `--clone`,
don't assume config parity means functional parity. See also
[`deployment/README.md`](deployment/README.md#dml-posture) and
[`deployment/README.md`](deployment/README.md#auxiliary-summarizationcompression-posture).

---

## Repository structure

```
2026_aec_cptx_demo_dml/
├── demos/               Portable bundle: cliff_house, cliff_house_modification,
│                        virtual_production_studio, teapot (~91MB, see demos/README.md)
├── system_prompts/      Phase execution prompts (00–13) + appendixes
├── skills/              Agent knowledge base + Python validation scripts
├── hermes/              DEMO_RULES.md — the live demo operating bible
├── tools/               OBS controller, MCP wrappers, layer reveal scripts
├── scripts/             Blender Python: depth extraction, ComfyUI, render
├── docs/                Pipeline diagram and documentation
├── deployment/          Sanitized remote `aec-cptx` profile + Windows launchers
├── aa_demo_versions/    Original (pre-portable-bundle) project files
│   └── cliff_house_02/
│       ├── user_prompts/project_prompt.md   ← fill this in for your project
│       └── rhino_assets/base_model.3dm      ← start-state Rhino file
└── _scene_templates/    Clean template files
```

`demos/` and `aa_demo_versions/` currently both hold Cliff House material
from different points in the project's history — `demos/` is the current
canonical portable bundle (added 2026-07-10); `aa_demo_versions/` is the
earlier working-file layout, kept for now rather than deleted outright.

---

## The 13-phase pipeline

| Phase | Where | What happens |
|-------|-------|--------------|
| 00 | Agent | Session startup, MCP health check |
| 01 | Agent | Read design brief, confirm decisions |
| 02 | Rhino | Site prep: terrain, pad, curtain wall, driveway |
| 03 | Rhino | Massing: L1/L2/L3 floor volumes, balconies, roof slabs |
| 04 | Rhino | 2D floor plans with room labels |
| 05 | Rhino | 3D floor plan stacking |
| 06 | Rhino | Detailing: glazing, mullions, railings, cladding |
| 07 | Gate | Pre-export validation: coplanar check, duplicate removal |
| 08 | Blender | Lighting (HDRI) + camera animation |
| 09 | Blender | Materials from Rhino metadata |
| 10 | Blender | Test render (960×540) |
| 11 | Blender | Final render (1920×1080 EXR+PNG) + optional ComfyUI |
| 12 | Rhino | Layer reveal animation |
| 13 | Rhino | Sun study animation |

Note: the Teapot demo does not use this pipeline at all — it's a
Blender-only material/shading test scene, independent of the Rhino-driven
phases above.

---

## Key design principles

- **Derive, don't redraw** — every vertex snaps to existing geometry. No eyeballed positions.
- **One object per MCP call** — paced construction the audience can follow in real time.
- **Metadata propagates** — Rhino User Text encodes material roles, survives export to Blender.
- **Reference layers are sacred** — hidden template geometry is audited silently and never modified.
- **Backup before every change** — numbered `.3dm` checkpoints before any substantive edit.
- **Hero/session model rule** (Cliff House) — the canonical hero `.blend`
  is never silently overwritten by in-session edits; active work happens
  on timestamped session copies, and folding a change back into the hero
  file requires explicit user confirmation every time. See
  `demos/README.md` for the full rule.

---

## The design brief

Edit `aa_demo_versions/cliff_house_02/user_prompts/project_prompt.md` to
describe your own project. The template has 12 sections covering site,
style, materials, glazing, outdoor spaces, lighting, and camera. Fill it
in naturally — or tell Hermes "interview me about my project" and it
will fill it in for you.

---

## License

MIT — see LICENSE
