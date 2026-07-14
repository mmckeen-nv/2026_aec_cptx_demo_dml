# Creative Commons asset sourcing contract

## Purpose

Third-party production equipment and set dressing belong in Blender, not in the
authoritative Rhino architectural model. Rhino may contain named lightweight
proxy volumes, movement envelopes, and clearances, but these are coordination
objects—not finished visible equipment. After the Rhino-to-Blender gate, Blender
must replace every visible required proxy with its approved detailed cached asset.
Do not present proxy boxes as a finished scene.

## License policy

Preference order:

1. CC0/public domain.
2. CC BY 4.0 or a clearly stated equivalent, with attribution.
3. Original geometry created for this project.

Reject assets carrying any of these conditions unless the user explicitly approves a separate use case and legal review: NonCommercial, NoDerivatives, ShareAlike, editorial-only, unclear/custom license, ripped/extracted content, or a NoAI restriction. NoAI assets are incompatible with the planned Blender-render-to-ComfyUI path.

License metadata can change. Before every download, reopen the source page and verify creator, exact asset ID, download availability, license, and special restrictions. Record the verification date. Never infer a license from search-result text or a filename.

## Import procedure

1. Query DML for previously approved/rejected assets and known import issues.
2. Consult `assets/asset_manifest.yaml`; do not free-search and import in the same step.
3. Read `assets/cache/cache_index.json`. If a verified cached package exists, import from its path resolved relative to the cache index and do not redownload it.
4. When the cache is absent, use Blender MCP's Poly Haven or Sketchfab integration where possible. For Sketchfab, use the exact UID from the manifest. Cache the original package with `scripts/cache_vp_assets.py` before production import.
5. Retain the original archive or glTF/FBX and a text copy of license/source metadata.
6. Import into an isolated Blender collection named `ASSET_<ASSET_KEY>`.
7. Normalize units, orientation, origin, materials, and naming without destructively replacing the source file.
8. Check polygon count, missing textures, unsupported shaders, duplicate materials, malware-like scripts/drivers, unexpected cameras/lights, and excessive scene scale.
9. Create an optimized linked/collection instance for the production scene. Preserve the untouched imported collection, disabled from render.
10. Add the actually used asset and any modifications to `assets/ATTRIBUTIONS.md`.
11. Ingest the validated asset record into DML. Reinforce only if the import and render test pass.

## Required replacement gate

- Map proxy names/roles to manifest keys before importing assets.
- Required visible roles include cinema camera/tripod, production/director
  seating, control-room seating/monitors, practical LED lights/stands, and road cases.
- Preserve the proxy transform and clearance intent when placing the detailed asset.
- Hide the corresponding proxy from render only after the replacement asset is
  present, correctly scaled, grounded, oriented, and visually inspected.
- Fail the Blender beauty gate if a required visible proxy remains as a cube,
  cuboid, generic cylinder, or other placeholder silhouette.

## Performance budgets

- Hero camera/equipment asset: target under 100k triangles before duplication.
- Repeated chair, monitor, stand, rack, or case: target under 50k triangles; create LOD/proxy when higher.
- Background dressing: target under 10k triangles per unique asset.
- Use collection instances for repeated assets.
- Texture target: 2K for ordinary props, 4K only for hero close-ups; downscale 8K source textures unless justified.

## Attribution release gate

Before packaging, rendering final deliverables, or sharing the `.blend`, ensure every non-CC0 external asset used in a visible or distributed scene appears in `assets/ATTRIBUTIONS.md` with title, creator, source URL, asset ID, license, verification date, and modifications. A shortlist entry alone does not count as attribution.
