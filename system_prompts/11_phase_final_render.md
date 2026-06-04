# Phase 11 — Final Rendering
### Final Render Execution Prompt
*Part of the Hermes AEC Demo prompt suite*
*Reads: `01_user_prompt.md` § Phase 11, `[project]/prompts/` deltas*
*Version 1.0 — May 2026*

---

## Purpose

Render the full-resolution beauty sequence, depth maps, and segmentation masks.
Run the ComfyUI post-processing workflow on the beauty output. Deliver the final
MP4 and all render passes to the project folder.

---

## Inputs

- `[project]/blender_assets/base_model.blend` from Phase 10 (beauty materials restored)
- `[project]/comfy_source/` — ComfyUI workflow JSON for this project
- Delta notes — check for: final resolution, sample count, ComfyUI workflow type

## Outputs

- `[project]/renders/patio_sweep/v_YYYYMMDD_HHMM/` — full beauty sequence
- `[project]/renders/depth/` — final 16-bit depth maps
- `[project]/renders/segmentation/` — final segmentation masks
- `[project]/comfy_output/` — ComfyUI processed frames
- `[project]/video_source/` — all render outputs ready for video editing

---

## Pre-Phase Audit Checklist

- [ ] Phase 10 gate approved
- [ ] Beauty materials confirmed restored
- [ ] GPU is available and not running other workloads
- [ ] `[project]/renders/` folder exists
- [ ] ComfyUI workflow JSON is in `[project]/comfy_source/`
- [ ] Google Chrome is open (reserved for ComfyUI — no other tabs)
- [ ] OBS COMFYUI source verified (screenshot check)

---

## OBS Recording Protocol — Three Separate Clips

This phase produces three capture files. Stop and rename between each step.

**Step A — Hermes setup:**
→ **TRAY:** Update `current_stage.json` with current phase. Announce: "Starting phase — click Record in the tray when ready."
Hermes describes render settings and confirms output paths.
→ **TRAY:** Announce: "Phase complete — stop recording in the tray." Rename: `11-final_render-hermes.mkv`.

**Step B — Blender render:**
→ **TRAY:** Announce: "Switching to Blender — click Record Blender in the tray when ready."
Confirm: "Recording started — `11-final_render-blender`."
Stay on BLENDER for all Blender render work. Do not switch away during any render.
→ **TRAY:** Announce: "Blender renders complete — stop recording in the tray."
Rename: `11-final_render-blender.mkv`.

**Step C — ComfyUI post-processing:**
→ **OBS ACTION:** Verify COMFYUI source (screenshot check).
**TRAY:** Announce: "Switching to ComfyUI — click Record ComfyUI in the tray when ready."
Confirm: "Recording started — `11-final_render-comfyui`."
→ **TRAY:** Announce: "ComfyUI complete — stop recording in the tray."
Rename: `11-final_render-comfyui.mkv`.

---

## Execution Steps

### Step A — Render setup (Hermes window)

Confirm and document:
- Final resolution: 1920×1080 (or per delta). [adjustable]
- Sample count: 384. [adjustable]
- Denoiser: OPTIX (or OpenImageDenoise if OPTIX unavailable).
- Frame range: 0–192.
- Output path: `[project]/renders/patio_sweep/v_YYYYMMDD_HHMM/png/frame_####.png`
- EXR path: `[project]/renders/patio_sweep/v_YYYYMMDD_HHMM/exr/frame_####.exr`

### Step B — Blender renders (Blender window)

**B1. Beauty PNG sequence:**
- Engine: Cycles GPU, 384 samples, OPTIX denoiser, 1920×1080.
- Output: `v_YYYYMMDD_HHMM/png/frame_####.png` (PNG, RGB, 8-bit).
- Render all 193 frames.

**B2. EXR sequence:**
- Same settings, output format: OPEN_EXR, ZIP compression, 32-bit.
- Output: `v_YYYYMMDD_HHMM/exr/frame_####.exr`.

**B3. Encode beauty MP4:**
```
ffmpeg -y -framerate 24 -start_number 0 -i frame_%04d.png
       -c:v libx264 -pix_fmt yuv420p -crf 18 patio_sweep.mp4
```
Output: `v_YYYYMMDD_HHMM/patio_sweep.mp4`.

**B4. Depth maps — full resolution:**
Follow `depth_and_segmentation.md`. Output to `v_YYYYMMDD_HHMM/depth/`.

**B5. Segmentation masks — full resolution:**
Follow `depth_and_segmentation.md`. Output to `v_YYYYMMDD_HHMM/segmentation/`.

**B6. Restore beauty materials after passes.**

### Step C — ComfyUI post-processing (Chrome window)

- Load the ComfyUI workflow from `[project]/comfy_source/[workflow].json`
  via the Hermes in Chrome MCP extension.
- Connect the beauty PNG sequence from `v_YYYYMMDD_HHMM/png/` as the input.
- Run the workflow. Monitor via Chrome MCP DOM inspection for completion.
- Output processed frames to `[project]/comfy_output/`.

### Final — copy to video_source
Copy all deliverable files to `[project]/video_source/`:
- `patio_sweep.mp4` (beauty)
- A sample depth and segmentation frame (for editor reference)
- ComfyUI output folder reference

---

## Post-Phase Cleanup Checklist

- [ ] All 193 beauty PNGs present and non-zero file size
- [ ] All 193 EXRs present
- [ ] MP4 plays at correct duration (~8 seconds at 24fps)
- [ ] Depth maps correct (no shadows, correct near/far convention)
- [ ] Segmentation masks correct (flat colours, no gradients)
- [ ] ComfyUI output frames present in `[project]/comfy_output/`
- [ ] `depth_raw_temp/` deleted
- [ ] `video_source/` populated
- [ ] Beauty materials restored in Blender

---

## ▶ FINAL REVIEW — Delivery

Present:
1. Full-resolution beauty MP4
2. Three representative stills from the sequence
3. One depth map sample and one segmentation sample
4. ComfyUI processed sample frame

Confirm: delivery is complete and all files are in the correct project folders.

---

## Final Checkpoint Save

```python
import bpy, datetime
stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
bpy.ops.wm.save_as_mainfile(
    filepath=fr"[project]\blender_assets\base_model_checkpoint_{stamp}_FINAL.blend",
    copy=True)
```

→ **TRAY:** Update `current_stage.json` with current phase. Announce: "Starting phase — click Record in the tray when ready."
Hermes presents delivery summary on screen.
→ **TRAY:** Announce: "Delivery confirmed — stop recording in the tray."
Rename: `11-delivery-hermes.mkv`. Confirm all capture files present.

**Project complete.**
