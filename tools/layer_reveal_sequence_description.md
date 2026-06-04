# cliff_house_02 — Layer Reveal Sequence
## Algorithm Description

### Purpose

A timed layer-visibility animation that walks an audience through the
architectural design of cliff_house_02 in four narrative phases:

1. **Deconstruct massing** — strip away the design intent volumes top-down
2. **Build structure** — reveal the structural skeleton bottom-up
3. **Apply finish** — swap structure for finished materials floor by floor
4. **Reveal deck & pool** — complete the site with the pool deck and water features

---

### Guiding Principle: UI Stacking Order

Every phase respects the layer panel's visual stacking order.
"Bottom-up" means: the layer that sits lowest in the Rhino layer panel
is revealed first. This produces a coherent ground-up construction
narrative that matches how the building was actually built.

- In `h2_structure`: H2_L1_structure sits at the bottom → shown first
- In `H02_finishes`: L1_floors sits at the bottom → shown first
- Within each level: floors (bottom of group) → walls → balconies/roof (top)

---

### Reset State

Before the sequence runs, all layers are forced to their explicit starting
visibility using Python + `rhinoscriptsyntax.LayerVisible()`. This is
critical: Rhino's C# `layer.IsVisible` getter returns *effective* (parent-
inherited) visibility, so writing False to a child whose parent is already
hidden is a no-op. Python's `rs.LayerVisible(guid, False)` bypasses this
and forces the layer's own flag regardless of parent state.

**Start state:**
- `building_site_fixed` — all ON except terrain (hidden)
- `House_02_massing` — all ON
- `h2_structure` — all OFF (explicitly, not by inheritance)
- `House_02_finish` — all OFF (explicitly, not by inheritance)

---

### Phase 1 — Deconstruct Massing (top → down, 2s per beat)

Removes the design-intent massing volumes starting from the topmost layer
in the panel (L3) and working down to L1. Each sublayer disappears
individually before its parent is hidden.

Order: L3 balcony solids → L3 solids → H2_L3_solid parent →
       L2 roof solids → L2 balcony solids → L2 solids → H2_L2_solid parent →
       h2_L1_solids → House_02_massing parent

---

### Phase 2 — Build Structure (bottom → up, 2s per beat)

Reveals the structural model starting from the lowest layer in the panel
and building upward. `deck_flush_swap` (the flush deck reference geometry,
including its cladding) is the 3rd item made visible — it lives under
H2_L1_structure and represents the first site-level geometry that appears.

Order:
1. h2_structure (parent — no geometry, enables group)
2. H2_L1_structure (parent)
3. deck_flush_swap + deck_cladding + deck_retaining_wall + deck_flush  ← #3
4. L1_garage
5. h2l1_walls + l1_west
6. H2_L2_structure → h2_l2_floors → h2l2_walls → h2_l2_balc
7. H2_L3_structure → h2_l3_floors → h2l3_walls → h2_l3_balc
8. h2_L2_roof
9. H2_L3_roof

---

### Phase 3 — Swap Structure → Finish (bottom → up, 2s per beat)

For each floor level (L1 → L2 → L3), structure layers are hidden and
finish layers are shown simultaneously. The structural skeleton dissolves
and the finished building materialises in its place, level by level.

The swap pattern for each floor:
- Hide the structure walls/floors/balconies
- Show the finish equivalents (walls, glazing, mullions, floors, balconies)
- Hide the structural parent once all finish is visible
- Show the finish roof
- Move to the next level up

`deck_pool_swap` and `pool` are the last two beats — they sit at the top
of the H02_finishes panel and represent the final site completion.

Order: L1 (floors → walls/doors → entry windows → windows → mullions → L1 structure off) →
       L2 (floors → walls/glazing → windows → balconies → roof → L2 structure off) →
       L3 (floors → walls/glazing → balconies → roof → L3 structure off → h2_structure off) →
       deck_pool_swap (second to last) →
       pool (last)

---

### Timing

- `tick()` — 2 second pause with `RhinoApp.Wait()` message pumping
  (NOT Thread.Sleep — that freezes the UI)
- `pause()` — 3 second hold at end of each phase
- `tick()` is called before the first beat of each phase to give breathing
  room between phases

---

### Technical Notes

- **Layer paths** use `::` separator with `FindByFullPath()` in C#
- **sv(path, bool)** helper: finds layer by full path, sets IsVisible,
  calls CommitChanges()
- **RhinoApp.Wait()** in timing loops allows Rhino to process window
  messages and update viewports during delays
- **Python reset** uses direct layer indices (not paths) for speed and
  reliability — indices must be re-verified after any layer restructure
- Layer indices shift whenever layers are added/deleted/moved — always
  re-audit before updating the Python reset script
