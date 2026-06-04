# Skills INDEX -- aec_cptx_demo
# Last updated: May 2026
# ROOT: C:\Users\swags\Documents\2026_aec_cptx_demo
# All paths below are relative to ROOT.

---

## Read this file first. Every session, every task.

The project is an architectural visualization pipeline:
brief + reference images + Rhino source -> Blender render -> optional ComfyUI post.
Deliverable: a demo that runs end-to-end, suitable for stakeholders.

---

## Operating rules

1. Read INDEX.md first. Before any task.
2. MCP health check at session start. Ping: Rhino, Blender, OBS, ComfyUI.
   Report what is up/down. If a required server is down, notify Sean -- do not
   work around or fail silently.
3. Read session_state.md second. Know exactly where the project is.
4. Then view the specific skill(s) for the task. Don't rely on memory.
5. Skills are the source of truth. If a phase prompt or memory disagrees
   with a skill file, the skill file wins.

---

## After reading this INDEX, read `skills/session_state.md`

---

## Pipeline overview

```
[0] Session start: MCP health check + read project_prompt
    |
[1] Reference interpretation: brief + images -> design intent
    |
[2] Site prep (02_phase_site_prep) -> Rhino MCP
    |
[3] Massing (03_phase_massing) + Floorplans (04, 05) -> Rhino MCP
    |
[4] Detailing (06_phase_detailing) -> Rhino MCP
    |
[5] Export to Blender (07_phase_export_blender): validate -> snapshot -> import
    |
[6] Lighting + Camera (08_phase_lighting_camera) -> Blender MCP
    |
[7] Materials (09_phase_materials) -> Blender MCP
    |
[8] Test render (10_phase_test_render) -> Blender
    |
[9] Final render (11_phase_final_render) -> Blender + optional ComfyUI
```

---

## Skills catalog

### Reference and philosophy

| Skill                     | When to read                                      | File                              |
|---------------------------|---------------------------------------------------|-----------------------------------|
| Architectural pipeline    | Starting any task; recall the full workflow       | skills/architectural_pipeline.md  |
| Rhino modeling discipline | Advise on or audit Rhino construction             | skills/rhino_modeling.md          |
| Rhino pre-export          | Final gate before .3dm handoff to Blender         | skills/rhino_prep.md              |

### OBS recording

| Skill                     | When to read                                      | File                              |
|---------------------------|---------------------------------------------------|-----------------------------------|
| OBS recording protocol    | Any time recording is involved                    | skills/obs_recording.md           |

### Rhino-side tools (run inside Rhino)

| Skill                     | When to invoke                                    | File                              |
|---------------------------|---------------------------------------------------|-----------------------------------|
| Active-document audit     | During modeling; reports coplanar/duplicates      | skills/audit_active_document.py   |
| Pre-export validation     | Immediately before export (Phase 7 gate)          | skills/pre_export_validate.py     |

### Blender-side tools

| Skill                     | When to invoke                                    | File                              |
|---------------------------|---------------------------------------------------|-----------------------------------|
| Coplanar detector         | After import; before render; after geometry edits | skills/coplanar_detector.py       |
| Import .3dm with metadata | First step of Phase 7 inside Blender             | skills/import_with_metadata.py    |
| Validate scene            | Phase 7 post-import gate                          | skills/validate_blender_scene.py  |
| Derive-geometry helpers   | Modifying geometry in Blender                     | skills/derive_geometry.py         |

### Depth and segmentation

| Skill                     | When to invoke                                    | File                              |
|---------------------------|---------------------------------------------------|-----------------------------------|
| Depth + segmentation      | Rendering depth maps or segmentation masks        | skills/depth_and_segmentation.md  |

### Persistent rules

| Rule                      | Applies                                           | File                              |
|---------------------------|---------------------------------------------------|-----------------------------------|
| Backup rule               | Before ANY substantive Rhino or Blender change    | skills/BACKUP_RULE.md             |
| Visual engagement rule    | All design discussions and scene work             | skills/VISUAL_ENGAGEMENT_RULE.md  |

### Pending (not yet built)

| Skill                              | Stage  | What it needs to do                                              |
|------------------------------------|--------|------------------------------------------------------------------|
| MCP health check + restart-notify  | [all]  | Ping all MCPs at session start, report status                    |
| Reference interpretation           | [1]    | Brief + images -> structured design_intent.md                   |
| Rhino construction via MCP         | [2-4]  | Given design intent + base Rhino -> built model with metadata    |
| Iterative change loop              | [4]    | User says "wider patio" -> locate, derive, update, re-audit      |
| Materials library                  | [7]    | Metadata tag -> correct Blender material setup                   |
| ComfyUI integration                | [9]    | Submit frames + depth to ComfyUI, retrieve output               |
| Retaining wall + footing           | [2]    | Wall from terrain + pad curve, continuous footing, frost depth   |

---

## Trigger reference

| Trigger phrase                                | Action                                          |
|-----------------------------------------------|-------------------------------------------------|
| "audit" / "z-fight" / "coplanar"             | coplanar_detector.py or audit_active_document.py|
| "export" / "Rhino -> Blender" / "Phase 7"    | pre_export_validate -> import_with_metadata -> validate |
| "new geometry" / "modify object"             | derive_geometry.py                              |
| "material" / "texture" / "looks wrong"       | architectural_pipeline.md metadata conventions  |
| "render" / "encode" / "MP4"                  | 10_phase_test_render.md or 11_phase_final_render.md |
| "OBS" / "record" / "capture"                 | skills/obs_recording.md                         |
| "Rhino discipline" / "modeling correctly"    | rhino_modeling.md                               |
| "depth map" / "segmentation"                 | depth_and_segmentation.md                       |
| "retaining wall" / "footing" / "frost depth" | retaining_wall_footing.md                       |
| "backup" / "checkpoint"                      | BACKUP_RULE.md                                  |
| "reference image" / "show me"                | VISUAL_ENGAGEMENT_RULE.md                       |
| "send to ComfyUI" / "AI render" / "Execute"  | claude_config/REBUILD_GUIDE.md (Phase 8)        |
