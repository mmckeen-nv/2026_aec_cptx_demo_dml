# Rhino Phase 1 — Site and building shell
### Agent-authored execution prompt

## Purpose

Establish the lot, access logic, building placement, exterior shell, stage floor,
and clear soundstage volume. This is proportion and circulation massing—not a
replay of a predetermined model.

## Inputs

- `01_standard_vp_studio_brief.md`: lot, building, stage, entry, and loading requirements.
- Current Rhino scene and any applicable DML decisions/failures.

## Design decisions before modeling

Decide and state the building position on the lot, public versus service sides,
truck approach, stage location within the shell, ancillary-bar orientation, and
how the 120 ft x 100 ft clear stage fits inside the approximately 180 ft x 150 ft
building. Label any departure from the baseline as a planning assumption.

## Execution steps

1. Query DML and augment the proposed site/shell strategy through CMA.
2. Inspect Rhino and set inches, origin, and tolerances.
3. Author one bounded MCP script for lot/property and access reference geometry.
4. Inspect plan dimensions and placement.
5. Author a separate bounded MCP script for building shell and clear stage/floor.
6. Inspect plan, exterior axonometric, stage dimensions, names, layers, and metadata.
7. Record and ingest each attempt; reinforce only the passed result.

## Post-phase checklist

- Lot is 300 ft x 400 ft and visibly distinguishable from building geometry.
- Building is approximately 180 ft x 150 ft with a rational lot placement.
- Clear stage is at least 120 ft x 100 ft x 40 ft.
- Public, crew, loading, and service approaches can be developed independently.
- No geometry was created in Blender and no save command was issued.

## Review gate

Present plan and exterior-axonometric evidence plus measured bounds. Advance only
when the massing and access concept are coherent.
