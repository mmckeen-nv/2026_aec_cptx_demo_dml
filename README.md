# AEC CPTX Demo — AI Architectural Visualization Pipeline

A live demonstration of an AI agent (Hermes / Claude) autonomously building a 3D architectural model in Rhino, exporting to Blender for rendering, and optionally running ComfyUI post-processing — in real time, with an audience watching.

**Active project:** `cliff_house_02` — a modernist 3-storey cliff house with cantilevered floors, west-facing ocean views, white ashlar stone, and bronze glazing.

---

## What this is

This is not a plugin or a script library. It is a **prompt engineering system** — a structured set of phase prompts, skills, and operating rules that instruct an AI agent to:

1. Read a plain-English design brief
2. Build a Rhino 3D model step by step via MCP
3. Export and render in Blender
4. Produce final images via ComfyUI (optional)

The agent does the work. The human watches, approves, and steers.

---

## Prerequisites

| Tool | Purpose | Notes |
|------|---------|-------|
| [Hermes Agent](https://hermes-agent.nousresearch.com) | AI agent runtime | Runs Claude Sonnet via Anthropic API |
| [Rhinoceros 3D](https://www.rhino3d.com) (v7+) | 3D modeling | Windows only |
| [Rhino MCP Server](https://github.com/your-rhino-mcp-link) | Rhino ↔ agent bridge | localhost:3001 |
| [Blender](https://www.blender.org) (4.0+) | Rendering | |
| [BlenderMCP](https://github.com/your-blender-mcp-link) | Blender ↔ agent bridge | localhost:9876 (TCP) |
| [OBS Studio](https://obsproject.com) | Screen capture | For demo recording |
| [ComfyUI](https://github.com/comfyanonymous/ComfyUI) | AI post-processing | Optional |

---

## Quick start

### Local/rebuild path

1. Clone this repo
2. Open Hermes and set `ROOT` to the cloned directory in `README.md`
3. Open Rhino and start the MCP server
4. Tell Hermes: **"Resume cliff_house_02"**
5. Hermes reads the session startup sequence and asks what to build next

See [SETUP.md](SETUP.md) for full configuration instructions.

### Current remote demo deployment

The working AEC demo server deployment is captured under [`deployment/`](deployment/):

- `deployment/aec-cptx-profile/` — sanitized Hermes `aec-cptx` profile artifacts copied from the remote server.
- `deployment/windows-launchers/` — Windows desktop launcher scripts verified to start the interactive `aec-cptx` Hermes shell.
- `deployment/source/` — captured Hermes Agent source, Daystrom DML integration source, and the active profile Daystrom plugin copy from the working remote deployment.

Verified remote target:

| Item | Value |
|------|-------|
| Windows host | `DESKTOP-14FNBB2` |
| Windows user | `test` |
| Hermes profile | `aec-cptx` |
| Profile path | `C:\Users\test\AppData\Local\hermes\profiles\aec-cptx` |
| Desktop launcher path | `C:\Users\test\Desktop` |
| Best manual launcher | `START_HERMES_AEC_CPTX.cmd` |

The launcher path was tested through an interactive TTY and reached the live Hermes prompt:

```text
aec-cptx ❯
```

Use `deployment/aec-cptx-profile/config.example.yaml` as a redacted reference for the live profile posture. Do **not** commit live `.env`, auth files, `state.db`, session logs, caches, or DML runtime stores.

Current remote Hermes/DML posture has also been verified for side-task summarization and active DML runtime use: auxiliary compression/title/web extraction resolve to the same working custom NVIDIA-compatible model endpoint as chat, `compression.threshold` is set to `0.85`, the `daystrom_dml` memory provider registers/activates cleanly on Windows, and DCN active-read logs show `retrieve_dml: true` with `retrieval_policy: always`. See [`deployment/README.md`](deployment/README.md#dml-posture) and [`deployment/README.md`](deployment/README.md#auxiliary-summarizationcompression-posture).

---

## Repository structure

```
aec_cptx_demo/
├── system_prompts/     Phase execution prompts (00–13) + appendixes
├── skills/             Agent knowledge base + Python validation scripts
├── hermes/             DEMO_RULES.md — the live demo operating bible
├── tools/              OBS controller, MCP wrappers, layer reveal scripts
├── scripts/            Blender Python: depth extraction, ComfyUI, render
├── docs/               Pipeline diagram and documentation
├── deployment/         Sanitized remote `aec-cptx` profile + Windows launchers
├── aa_demo_versions/   Project files
│   └── cliff_house_02/
│       ├── user_prompts/project_prompt.md   ← fill this in for your project
│       └── rhino_assets/base_model.3dm      ← start-state Rhino file
└── _scene_templates/   Clean template files
```

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

---

## Key design principles

- **Derive, don't redraw** — every vertex snaps to existing geometry. No eyeballed positions.
- **One object per MCP call** — paced construction the audience can follow in real time.
- **Metadata propagates** — Rhino User Text encodes material roles, survives export to Blender.
- **Reference layers are sacred** — hidden template geometry is audited silently and never modified.
- **Backup before every change** — numbered `.3dm` checkpoints before any substantive edit.

---

## The design brief

Edit `aa_demo_versions/cliff_house_02/user_prompts/project_prompt.md` to describe your own project. The template has 12 sections covering site, style, materials, glazing, outdoor spaces, lighting, and camera. Fill it in naturally — or tell Hermes "interview me about my project" and it will fill it in for you.

---

## License

MIT — see LICENSE
