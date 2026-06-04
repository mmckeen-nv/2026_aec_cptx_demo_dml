# Phase 3 — Detailing
### Detailing Execution Prompt
*Part of the Hermes AEC Demo prompt suite*
*Reads: `01_user_prompt.md` § Phase 3, `[project]/prompts/` deltas*
*Version 1.0 — May 2026*

---

## Purpose

Add all architectural surface elements to the massing: curtain wall glazing and
mullion grid, balcony, veranda posts, entry sequence (canopy, steps, landing, door),
garage doors, and driveway. No materials assigned yet — everything is neutral grey.

---

## Inputs

- `[project]/rhino_assets/base_model.3dm` from Phase 2
- Delta notes — check for: glazing extent, balcony sides, entry location,
  door style, driveway width

## Outputs

- `[project]/rhino_assets/base_model.3dm` — all detail geometry added
- `[project]/rhino_assets/base_model_checkpoint_YYYYMMDD_HHMM.3dm`

---

## Pre-Phase Audit Checklist

- [ ] Phase 2 gate approved
- [ ] Massing geometry clean and fully present
- [ ] Delta notes read for detailing overrides

---

## OBS Recording Protocol

→ **TRAY:** Update `current_stage.json` with current phase. Announce: "Starting phase — click Record in the tray when ready."
Confirm: "Recording started — `03-detailing-hermes`."

→ **TRAY:** Announce: "Switching to Rhino — click Record Rhino in the tray when ready."

→ **TRAY:** Announce: "Switching back to Hermes."

---

## Execution Steps

### 1. Curtain wall — glazing panels
- Upper floor west face: full-height glass panels within a regular grid.
  [adjustable — partial glazing, punched openings, or wrap to side facades]
- Glass sits slightly inset from the outer mullion face.

### 2. Curtain wall — mullions and transoms
- Vertical mullions create a regular rhythm across the facade.
- Horizontal transoms divide panels into equal heights.
- Mullions and transoms are dark aluminium extrusions — a separate object from glass.

### 3. Balcony
- Cantilevered slab running along the west/view face of the upper floor, projecting
  beyond the curtain wall line. [adjustable — depth and which sides]
- Clean flat plate, same thickness language as floor slabs.
- Solid parapet or railing at the outer edge — plain solid at this stage.
  [adjustable — glass rail, cable, or tube railing per delta]

### 4. Veranda structural posts
- Posts at the outer west edge of the lower floor supporting the upper floor overhang.
- Same material category as walls (assigned in Phase 6). [adjustable — can be steel]

### 5. Entry canopy
- Small secondary shed roof over the front door on the east/street face. [adjustable]
- Slopes in the same direction as the main roof (east high, west low).
- Supported by a post or wall bracket — simple solid at this stage.

### 6. Entry steps and landing
- Steps lead from driveway/grade up to front door level.
- Flat landing at the top. [adjustable — step count and width]
- Dark concrete material category (assigned in Phase 6).

### 7. Front door
- Solid panel door flush with or slightly inset from the wall face.
- Same material category as garage doors (assigned in Phase 6). [adjustable]

### 8. Garage doors
- Large flat panel doors on the east face, garage portion of lower floor. [adjustable]
- Flush with the wall face.

### 9. Driveway
- Paved surface connecting the street to the garage, following terrain slope.
- [adjustable — width and shape per delta]

---

## Post-Phase Cleanup Checklist

- [ ] Mullion rhythm is regular and consistent across glazed faces
- [ ] Glass panels do not interpenetrate mullions
- [ ] Balcony slab overhangs cleanly beyond the curtain wall line
- [ ] Entry canopy slope matches main roof direction
- [ ] Steps connect cleanly between grade and door level — no floating
- [ ] Driveway follows terrain — no floating or buried sections
- [ ] All new objects on correct named layers
- [ ] No geometry interpenetrates walls or terrain

---

## ▶ REVIEW GATE 3 — Detailing

Present:
1. Four compass-point renders (N, E, S, W)
2. Close-up of entry sequence from the street side
3. Close-up of curtain wall mullion rhythm

Wait for written approval.

---

## Checkpoint Save

Save Rhino checkpoint to `[project]/rhino_assets/base_model_checkpoint_YYYYMMDD_HHMM.3dm`.

→ **TRAY:** Announce: "Phase complete — stop recording in the tray."
Rename: `05-detailing-hermes.mkv`, `05-detailing-rhino.mkv`. Confirm.

Proceed to `07_phase_export_blender.md`.
