# Hermes Demos — Portable Bundle

This directory is the **canonical, portable** home for all demo project
data (models, source geometry, renders, ComfyUI outputs). It lives inside
the Hermes agent directory (`~/AppData/Local/hermes/demos/`) specifically
so that copying/zipping/syncing this one folder — or the whole Hermes
profile — carries every demo asset with it. No demo data should be
required to exist elsewhere for this bundle to be usable standalone.

Total size: ~94 MB (junk/backup files intentionally excluded — see
"What was left out" below).

## Structure

```
demos/
├── README.md                          (this file)
├── cliff_house/                       Demo 1: build-from-ground-up
│   ├── hero/                          protected canonical master
│   │   └── cliff_house_02_HERO.blend
│   ├── sessions/                      per-session working copies
│   │   └── cliff_house_02_session_<timestamp>.blend
│   └── source/                        earliest working checkpoint + renders
│       ├── base_model_final_20260615_0920.blend
│       └── renders/
├── cliff_house_modification/          Demo 2: iterative design-change track
│   └── comfyui_outputs/               Blender renders + ComfyUI stylized passes
│       └── mark_outputs/              final photoreal ComfyUI output(s)
├── virtual_production_studio/         Demo 3: VP studio (LED volume, brain bar)
│   ├── vp_studio_01_base_model.3dm    Rhino source
│   ├── vp_studio_01_scene.blend       Blender scene
│   ├── vp_studio_01_scene_gear.blend  variant w/ camera gear
│   ├── exports/                       OBJ/MTL exports
│   ├── renders/                       raw Blender renders (6 angles)
│   └── comfy_enhanced/                ComfyUI-enhanced passes (v4, multi-seed)
└── teapot/                            Demo 4: Utah teapot (Blender-only)
    ├── utah_teapot.{3dm,obj}          source geometry
    ├── build_teapot_demo.py           reusable Blender build/render script
    ├── teapot_demo.blend              scene (see material history below)
    └── renders/
        └── blender_teapot_hero.png    Blender Cycles hero render
```

**Note:** the Teapot demo was converted from Unreal Engine to Blender-only
on 2026-07-10 (Maya/UE support shelved — see `DEPENDENCIES.md`). The old
`.fbx`, UE import script, and UE render outputs were removed.

**Material history:** originally built with a ceramic (`M_Teapot_Ceramic`)
Principled BSDF material; converted to a polished chrome/mirror metal
(`M_Teapot_Chrome`: Metallic=1.0, Roughness≈0.02) on 2026-07-10, with the
mesh shade-smoothed and Eevee Next raytracing enabled so reflections
render correctly (see the `blender-mcp-scene-debugging` Hermes skill for
the pitfalls hit along the way — orphaned scene-collection objects, flat
shading, AgX color rolloff, fluid-sim bake instability). A fire/flame
environment experiment (emissive flame-mesh ring + Cycles GPU path
tracing) was explored in a live session but never folded into a saved
`.blend`.

**2026-07-10, later same day — model replaced from the `BAC_Teapot`
profile session:** the committed `.blend` now contains a single object,
`utah_teapot_canonical` (14,336 polys, dimensions 6.43×3.0×4.0, no
material, no camera, no lights, no ground plane — render engine left on
`BLENDER_EEVEE`). This does not carry forward the chrome material, camera,
or lighting setup described above; it looks like a fresh import/reset
rather than an edit on top of the prior scene. This was captured and
committed as the current on-disk state per explicit instruction, but has
**not been independently verified as intentional** — treat it as
in-progress until confirmed. If picking this demo back up, check with
whoever last worked in `BAC_Teapot` before assuming the chrome/camera/
lighting setup is gone for good.

## Hero / Session Model Rule (Cliff House only)

`cliff_house/hero/cliff_house_02_HERO.blend` is the **protected canonical
master**. It must never be silently overwritten by in-session edits.

- All active work happens on a copy in `cliff_house/sessions/`, named
  `cliff_house_02_session_<YYYYMMDD_HHMMSS>.blend`.
- Folding a change back into the hero file requires **explicit user
  confirmation** each time — never assume approval.
- The `cliff_house_modification` demo builds on top of the hero/session
  files above; its own directory holds only its render/ComfyUI outputs,
  not a separate copy of the model (avoid duplicting the same .blend
  across two demo folders — check `cliff_house/sessions/` for the model
  state a given `cliff_house_modification` render was produced from).

## What was left out (and why)

To keep this bundle small and portable, the following were intentionally
NOT copied in from the original working directories:

- Blender `.blend1` autosave files (redundant with the main `.blend`)
- Rhino `.3dmbak` and OBJ `.objbak` backup files (redundant)
- Intermediate `vp_studio_01_comfy/`, `_comfy_v2/`, `_comfy_v3/` passes
  (superseded by `_comfy_v4/`, kept here as `comfy_enhanced/`)
- The full Unreal Engine project (`Documents/unreal-mcp/`, ~3 GB) — only
  the teapot-specific import script and render outputs are demo-relevant
- Airport demo — removed from the lineup entirely (deemed unreasonable
  by user decision, 2026-07-10)
- ComfyUI raw `input/`/`output/` folders under `~/ComfyUI/` — the
  finished, presentable renders were copied out of these; the folders
  themselves are ComfyUI's own scratch space, not demo assets

Original working locations (Documents\, ComfyUI\, comfyui_outputs\) are
left untouched — this bundle is a curated copy, not a move. See
`Documents\DEMOS_MENU.md` on this machine for the older non-portable
index with full original-location paths, if needed for archaeology.

## Menu

See `Documents\DEMOS_MENU.md` for the user-facing demo menu that Hermes
presents at the start of each session. That file should be treated as
the canonical *menu/index*; this README documents the canonical *portable
data bundle*. Keep both in sync when demos are added/removed/modified.

## Dependencies & Deployment

See `DEPENDENCIES.md` (same directory as this file) for the full
dependency manifest and an agent-actionable deploy playbook — covers
Blender, ComfyUI, the Blender MCP bridge, Daystrom DML (agent memory
layer — REQUIRED, GPU+Ollama dependent), and optional Rhino/rhino3dm, on
both Windows and Linux/WSL2. Maya and Unreal Engine are explicitly out of
scope (shelved).
