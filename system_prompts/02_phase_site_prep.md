# Phase 1 — Site Preparation
### Site Prep Execution Prompt
*Part of the Hermes AEC Demo prompt suite*
*Reads: `01_user_prompt.md` § Phase 1, `[project]/prompts/` deltas*
*Version 1.0 — May 2026*

---

## Purpose

Build the terrain surface, define lot boundaries, and establish the building pad
and retaining curtain wall. Everything in this phase happens in Rhino. Blender
receives the exported mesh for later phases.

---

## Inputs

- Empty Rhino file from Phase 0: `[project]/rhino_assets/base_model.3dm`
- Delta notes: `[project]/prompts/` — check for site-specific overrides
  (slope direction, lot shape, terrain character)

## Outputs

- `[project]/rhino_assets/base_model.3dm` — terrain, lot lines, pad, curtain wall
- `[project]/rhino_assets/base_model_checkpoint_YYYYMMDD_HHMM.3dm`

---

## Pre-Phase Audit Checklist

- [ ] Phase 0 gate approved and recorded
- [ ] Rhino is open with the Phase 0 baseline file
- [ ] Any site-specific delta notes have been read
- [ ] OBS RHINO source verified (screenshot check) before first use

---

## OBS Recording Protocol

→ **TRAY:** Update `current_stage.json` with current phase. Announce: "Starting phase — click Record in the tray when ready."
Confirm: "Recording started — `01-site_prep-hermes`."

Hermes explains terrain approach, slope direction, and NURBS strategy on screen.

→ **TRAY:** Announce: "Switching to Rhino — click Record Rhino in the tray when ready."
Confirm: "Switching to Rhino."

Stay on RHINO throughout all Rhino work, including any revision rounds.

→ **TRAY:** Announce: "Switching back to Hermes."

---

## Execution Steps

### 1. Terrain NURBS surface
- Create a grid of U curves (running east–west) and V curves (running north–south)
  on dedicated layers in Rhino.
- Shape the curves to produce a natural hillside: high on the east (street side),
  sloping down to the west (view side), with gentle organic undulation.
- Loft or network-surface the curves into a single smooth NURBS surface.
- Confirm the surface is large enough that no render angle exposes its edge.
- [adjustable — slope direction, terrain character per delta notes]

### 2. Lot lines
- Draw the lot boundary as closed curves on a `Lot lines` layer.
- Default: roughly rectangular, long axis east–west, street on the east short edge.
- [adjustable per delta notes]

### 3. Building pad
- Create a solid box representing the building pad — a thick dark concrete slab
  sitting on the terrain, projecting slightly above finished grade on all sides.
- The pad bottom must extend below the lowest terrain point within its footprint.
  Sample terrain Z at all four corners and midpoints of each edge; extend the pad
  bottom at least 50mm below the minimum sampled Z value.
- [adjustable — pad footprint and thickness per delta notes]

### 4. Curtain wall (retaining wall)
- Create a slightly larger hollow box wrapping the pad perimeter, representing the
  retaining wall that holds the pad against the hillside.
- Same depth rule as the pad: bottom must be below the terrain at all perimeter points.
- Use the Rhino Trim operator with the terrain surface as the cutting tool to remove
  the portion of the curtain wall above the terrain surface if needed.
  Do NOT use Boolean Difference — use Trim so the terrain surface is the cutter
  and the above-terrain portion is deleted. Always set `rotation_mode = 'XYZ'`
  on any imported object before applying rotation transforms.

---

## Post-Phase Cleanup Checklist

- [ ] Terrain surface is smooth, large enough, and has no visible edge in any
      of the four compass-point viewport renders
- [ ] Lot lines are on their own layer
- [ ] Pad bottom is below terrain at all sample points (confirm with BVH ray test)
- [ ] Curtain wall bottom is below terrain at all perimeter sample points
- [ ] No floating geometry — no gaps between pad/curtain wall and terrain
- [ ] All geometry on correct named layers

---

## ▶ REVIEW GATE 1 — Site

Present:
1. Top-down viewport screenshot showing terrain, lot lines, and pad
2. Perspective view from SW showing terrain slope and pad above grade
3. Close-up of curtain wall / terrain intersection confirming no gap

Wait for written approval.

---

## Checkpoint Save

```csharp
// RhinoMCP
string stamp = DateTime.Now.ToString("yyyyMMdd_HHmm");
doc.WriteFile($@"[project]\rhino_assets\base_model_checkpoint_{stamp}.3dm",
    new Rhino.FileIO.FileWriteOptions());
```

→ **TRAY:** Announce: "Phase complete — stop recording in the tray."
Rename captures: `01-site_prep-hermes.mkv`, `01-site_prep-rhino.mkv`. Confirm.

Proceed to `05_massing_prompt.md`.
