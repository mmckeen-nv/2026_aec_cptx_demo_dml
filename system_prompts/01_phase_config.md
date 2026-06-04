# Phase 0 — Project Configuration
### Config & Session Setup Prompt
*Part of the Hermes AEC Demo prompt suite*
*Reads: `01_user_prompt.md`, `02_demo_prompt.md`*
*Version 1.0 — May 2026*

---

## Purpose

This prompt governs everything that must happen **before any geometry is created**:
project directory creation, application configuration, OBS source verification,
coordinate system setup, and prompt inheritance. Completing this phase correctly
means every subsequent phase has a clean, predictable working environment.

Run this prompt at the start of every new project, and at the start of every new
session on an existing project (for the OBS verification steps).

---

## Inputs

- `system_prompts/00_session_startup.md` — session startup rules
- `aa_demo_versions/[project]/user_prompts/project_prompt.md` — design brief
- Any project-specific delta notes provided by the user

---

## Outputs

- `aa_demo_versions/[project_name]/` — full directory tree created
- `aa_demo_versions/[project_name]/prompts/` — delta prompt documents (if any)
- OBS configured and all sources verified
- Blender and Rhino output paths set to project folder
- User confirmation that setup is complete

---

## Pre-Phase Audit Checklist

Before doing anything else, confirm the following with the user:

- [ ] Project name confirmed (lowercase, underscores, version suffix — e.g. `hillside_house_01`)
- [ ] `dummy_beach_house_01` is accessible as the reference folder structure
- [ ] Rhino 3D is open and responsive
- [ ] Blender is open and responsive
- [ ] OBS is open with the `AEC Demo` profile loaded
- [ ] Google Chrome is available for ComfyUI (later phases)
- [ ] BlenderMCP server is running (port 9876 confirmed in Blender Scripting tab)
- [ ] RhinoMCP server is running
- [ ] OBS MCP server is connected

If any item is not ready, stop and resolve it before proceeding.

---

## OBS Recording Protocol

→ **OBS ACTION:** Run the Session Startup Source Verification procedure from
`02_demo_prompt.md` before starting any recording:
1. Ask the operator to verify OBS sources: HERMES, RHINO, BLENDER, COMFYUI are visible and showing the correct windows.
2. Confirm with operator before proceeding.
3. Report pass/fail for each source to the user.
4. Do not proceed until all needed sources pass.

→ **TRAY:** Update `current_stage.json` with current phase. Announce: "Starting phase — click Record in the tray when ready."
Confirm: "Recording started — `00-project_setup-hermes`."

All configuration work happens in Hermes only. No Rhino or Blender work this phase.

---

## Execution Steps

### Step 1 — Create project directory tree

Create the following folder structure, mirroring `dummy_beach_house_01` exactly:

```
aa_demo_versions/[project_name]/
  blender_assets\
  rhino_assets\
  renders\
  test_renders\
  hdr\
  comfy_source\
  comfy_output\
  demo_assets\
  demo_captures\
  video_source\
  video_edits\
  scripts\
  skills\
  prompts\
  references\
  user_prompts\
  logs\
```

Confirm each folder was created. Report to user.

### Step 2 — Set OBS output path

→ **OBS ACTION:** Call `obs-set-record-directory` with path:
```
aa_demo_versions/[project_name]/demo_captures/
```
Confirm the path was set.

### Step 3 — Set Blender output paths

Via BlenderMCP, set:
- `scene.render.filepath` to `[project_root]\renders\`
- Confirm via `scene.render.filepath` readback

### Step 4 — Copy HDRI files

Ask the user which HDRI(s) this project will use. Copy them from the master
HDRI library at `{ASSET_ROOT}\assets\` into
`aa_demo_versions/[project_name]/hdr/`.
Confirm filenames.

### Step 5 — Copy scripts and skills

Copy any reusable scripts from `scripts/` into
`aa_demo_versions/[project_name]/scripts/` if they will be modified for this project.
Copy relevant skill files from `skills/` into
`aa_demo_versions/[project_name]/skills/` if project-specific overrides are anticipated.
If no overrides are needed, note that the master versions will be referenced directly.

### Step 6 — Establish prompt inheritance

Ask the user: "Are there any design differences from the master prompt for this project?
For example: different site orientation, different materials, different entourage, or
ComfyUI workflow notes?"

If yes: create `[project_name]/prompts/01_delta_notes.md` and document the differences.
If no: note that this project runs on master prompts with no delta.

Read back the delta notes to the user and confirm they are complete and accurate
before proceeding.

### Step 7 — Set coordinate system

Confirm with the user:
- North direction (default: positive Y)
- Primary view direction (default: west / negative X)
- Terrain slope direction (default: slopes down from east to west)
- World origin placement (default: near building footprint centre, at grade)

Document any differences from defaults in the project delta notes.

### Step 8 — Confirm Rhino and Blender are clean

- Rhino: new empty file, correct units set to metres, named and saved as
  `[project_name]/rhino_assets/base_model.3dm`
- Blender: new empty file, units set to metres, named and saved as
  `[project_name]/blender_assets/base_model.blend`

---

## Post-Phase Cleanup Checklist

Before presenting for review, confirm:

- [ ] All 17 project subfolders exist and are empty (ready to receive content)
- [ ] OBS output path points to `[project_name]/demo_captures/`
- [ ] Blender render output path points to `[project_name]/renders/`
- [ ] HDRI files are in `[project_name]/hdr/`
- [ ] Delta notes are written (or explicitly noted as "none")
- [ ] Rhino file saved as `base_model.3dm` in `[project_name]/rhino_assets/`
- [ ] Blender file saved as `base_model.blend` in `[project_name]/blender_assets/`
- [ ] Coordinate system confirmed and documented

---

## ▶ REVIEW GATE 0 — Configuration

Present to the user:
1. A directory listing of `[project_name]/` showing all subfolders
2. The OBS output path confirmation
3. The delta notes (or "no deltas — using master prompts as-is")
4. The coordinate system summary

Wait for explicit written approval before proceeding to Phase 1.

---

## Checkpoint Save

No geometry exists yet — no Blender or Rhino checkpoints needed.
Save the empty working files as the Phase 0 baseline:
- `[project_name]/blender_assets/base_model_checkpoint_YYYYMMDD_HHMM.blend`
- `[project_name]/rhino_assets/base_model_checkpoint_YYYYMMDD_HHMM.3dm`

---

## Gate Approved — Stop Recording

→ **TRAY:** Announce: "Phase complete — stop recording in the tray."
Rename output file to `00-project_setup-hermes.mkv`.
Confirm to user: "Configuration complete. Recording saved as `00-project_setup-hermes.mkv`."

Proceed to `02_phase_site_prep.md`.
