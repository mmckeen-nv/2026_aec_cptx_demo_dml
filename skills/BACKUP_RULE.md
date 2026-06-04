# Backup Rule — All aec_cptx_demo Projects

**Non-negotiable. Cannot be skipped for any reason.**

## Rhino
Before ANY substantive change to a Rhino scene:
1. Create `rhino_assets/backups/` if it doesn't exist
2. Save a numbered copy of the current .3dm there
   - Naming: `{filename}_{NNN}.3dm` where NNN is zero-padded sequence (001, 002, ...)
   - Example: `cliff_house_site_map_001.3dm`
3. Only then proceed with edits to the working file

## Blender
Before ANY substantive change to a Blender scene:
1. Create `blender_assets/backups/` if it doesn't exist
2. Save a numbered copy of the current .blend there
   - Naming: `{filename}_{NNN}.blend`
3. Only then proceed with edits

## Retention
Backups are kept until end-of-project review. Do not delete during active work.

## What counts as "substantive"
- Deleting any objects
- Restructuring layers
- Running any script that modifies geometry
- Importing or merging files
- Any operation that cannot be trivially undone by hand

*Added: 2026-05-20 per Sean's directive after scene wipe incident.*
