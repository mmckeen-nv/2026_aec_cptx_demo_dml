# Phase 2 — Massing
### Massing Execution Prompt
*Part of the Hermes AEC Demo prompt suite*
*Reads: `01_user_prompt.md` § Phase 2, `[project]/prompts/` deltas*
*Version 1.0 — May 2026*

---

## Purpose

Establish the pure building volume — lower floor, upper floor, roof, and floor
slabs as simple solids. No windows, doors, or surface detail. Massing is the
proportional foundation everything else is built on.

---

## Inputs

- `[project]/rhino_assets/base_model.3dm` from Phase 1 (terrain + pad)
- Delta notes — check for: floor plan shape, storey count, roof type, overhang depth

## Outputs

- `[project]/rhino_assets/base_model.3dm` — building volumes added
- `[project]/rhino_assets/base_model_checkpoint_YYYYMMDD_HHMM.3dm`

---

## Pre-Phase Audit Checklist

- [ ] Phase 1 gate approved
- [ ] All Phase 1 geometry present and correct in Rhino
- [ ] Delta notes read for any massing-specific overrides

---

## OBS Recording Protocol

→ **TRAY:** Update `current_stage.json` with current phase. Announce: "Starting phase — click Record in the tray when ready."
Confirm: "Recording started — `02-massing-hermes`."

→ **TRAY:** Announce: "Switching to Rhino — click Record Rhino in the tray when ready."

→ **TRAY:** Announce: "Switching back to Hermes."

---

## Execution Steps

### 1. Lower floor walls
- Solid rectangular (or plan-shape per delta) box sitting on the building pad.
- Footprint is smaller than the upper floor — set back to the east to leave a
  covered veranda on the west/view side. [adjustable — setback dimension and sides]
- Height: approx 3.0–3.5m clear ceiling. [adjustable]
- Garage integrated on the street/east side within the same footprint. [adjustable]

### 2. Floor slab — Level 1
- One solid object spanning the full lower-floor footprint.
- Thickness reads clearly as a horizontal datum. Sits on top of the lower walls.

### 3. Upper floor walls
- Footprint extends further west than the lower floor, creating the overhang
  that shelters the veranda below. [adjustable — overhang depth]
- Same ceiling height as lower floor. [adjustable]
- A visible gap (slab thickness) separates L1 top from L2 bottom.

### 4. Floor slab — Level 2
- One solid spanning the full upper-floor footprint.

### 5. Roof slab
- A single continuous shed (mono-pitch) plane sloping from east (high) to west
  (low). [adjustable — flat, butterfly, hip, or gabled per delta notes]
- Overhangs the building perimeter on all sides.
- Reads as one unified horizontal element, not broken into sections.

### Key geometry rules (from project history)
- Upper floor footprint is LARGER than lower floor — not equal, not smaller.
- Lower floor is recessed to the east creating the veranda on the west.
- Floor slab is ONE object spanning full footprint — not split by room divisions.
- Roof is ONE object — no joints, no ridges unless explicitly specified in delta.
- All objects must clear the terrain — no interpenetration between walls and terrain.

---

## Post-Phase Cleanup Checklist

- [ ] Lower floor walls sit cleanly on the pad — no gap, no interpenetration
- [ ] Upper floor overhangs the lower on the correct side(s)
- [ ] Floor slabs are single objects, correct footprint
- [ ] Roof overhang is consistent on all sides
- [ ] Gap between L1 top and L2 bottom is visible in elevation
- [ ] Building sits cleanly on pad — no floating or sinking
- [ ] All objects on correct named layers

---

## ▶ REVIEW GATE 2 — Massing

Present four compass-point viewport renders (N, E, S, W) in solid shading.
Confirm: proportions, overhang depth, roof slope, storey gap, garage integration.

Wait for written approval.

---

## Checkpoint Save

Save Rhino checkpoint to `[project]/rhino_assets/base_model_checkpoint_YYYYMMDD_HHMM.3dm`.

→ **TRAY:** Announce: "Phase complete — stop recording in the tray."
Rename: `02-massing-hermes.mkv`, `02-massing-rhino.mkv`. Confirm.

Proceed to `04_phase_floorplan_2d.md`.
