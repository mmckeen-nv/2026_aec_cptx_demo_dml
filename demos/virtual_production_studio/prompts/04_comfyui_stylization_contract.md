# ComfyUI stylization and cached-asset contract

## Geometry authority

ComfyUI stylizes approved Blender renders; it does not import or place `.blend`, `.fbx`, or `.glb` packages. Rhino remains authoritative for architecture and clearances. Blender remains authoritative for production equipment, set dressing, camera perspective, materials, lighting, and object placement. Never ask an image model to invent missing studio equipment as a substitute for importing it in Blender.

## Required context before stylization

1. Query Daystrom DML for `project:vp-studio-01` using: `What verified offline Blender assets are available for the virtual production studio, and which have passed import validation?`
2. Read `assets/asset_manifest.yaml` for identity, role, creator, source, and license.
3. Read `assets/cache/cache_index.json` relative to its own directory. A usable cached entry has `status: cached`, existing indexed files, and a Blender-ready `.glb` or `.blend` path.
4. Read `assets/cache/blender_import_smoke_test.json`. Sketchfab GLBs are eligible only when their result is `passed` for the installed Blender version.
5. Inspect Blender through MCP and inventory visible collections named `ASSET_<ASSET_KEY>`. The cache is an availability list, not proof that an asset is present in a shot.
6. Confirm every visible non-CC0 asset has a completed entry in `assets/ATTRIBUTIONS.md` before producing a distributable image or `.blend`.

## Verified model vocabulary

The following manifest keys are the approved vocabulary the agent should use when selecting, importing, describing, masking, and recording props:

| Asset key | Production role | ComfyUI preservation cue |
| --- | --- | --- |
| `camera_cinema_body_re1monsen` | Hero cinema camera body | Preserve camera silhouette, lens, controls, and placement. |
| `camera_tripod_silver_key` | Cinema camera with tripod | Preserve camera/tripod geometry and floor contact. |
| `chair_director_creativejenna` | Director and production seating | Preserve director-chair frame and fabric silhouette. |
| `grip_c_stand_kilianpohl` | Grip and lighting stand | Preserve stand legs, riser, grip head, and safe position. |
| `light_led_soft_panel_roy` | Practical LED production light | Preserve panel housing, yoke/stand, aim, and emitted-light intent. |
| `control_server_rack_anais` | Media-server room rack | Preserve rack volume, equipment face, and service-clearance context. |
| `control_monitor_datsketch` | Repeated control-room monitor | Preserve monitor count, screen positions, and workstation layout. |
| `roadcase_thomas_kole` | Stage/loading-area road case | Preserve case proportions, hardware, wheels, and location. |
| `cables_modular_simon_laisne` | Controlled cable dressing | Preserve intentional routes; do not create trip hazards or random cables. |
| `chair_modern_arm_polyhaven` | Green-room/client-lounge chair | Preserve lounge-chair count, placement, and material family. |
| `chair_crew_monobloc_polyhaven` | Stackable crew seating | Preserve chair count and aisle/egress clearances. |
| `dressing_office_notepads_polyhaven` | Control-room/office dressing | Preserve only when visible; do not exaggerate into structural geometry. |

## Blender-to-ComfyUI handoff

For each approved shot, create a versioned handoff manifest containing:

- Blender file and scene name.
- Camera name, resolution, lens, transform, and frame.
- Visible `ASSET_<ASSET_KEY>` collections and instance counts.
- Beauty, depth, normal, object-ID, and cryptomatte paths where supported.
- An object-ID or cryptomatte mapping from each visible asset key to its mask.
- Architectural control masks for the LED wall, openings, columns, stage edge, and rigging.
- Attribution status for every visible external asset.

The positive prompt may describe only equipment confirmed in the Blender inventory. Use the exact asset role and important visual cues from the table. The negative prompt must reject added or removed cameras, stands, chairs, racks, monitors, road cases, cables, doors, columns, truss, LED seams, and unsafe rigging.

## Workflow constraints

- Use an approved Blender beauty render as img2img input.
- Feed depth and other control passes into compatible control nodes when installed.
- Start with low denoise; increase it only after a side-by-side geometry review.
- Use fixed seeds during comparisons.
- Never claim that a checkpoint, LoRA, or ControlNet is installed without checking the ComfyUI object/model inventory.
- Do not use a cached asset merely because it is available. Import it in Blender, validate it, add attribution, and include it in the shot inventory first.

## Acceptance gate and learning

Compare the source and stylized images side by side. Fail the gate if visible equipment is missing, duplicated, moved, fused, relabeled as another object, or made unsafe; if architectural geometry drifts; or if attribution/handoff metadata is incomplete.

After a passing comparison, ingest the handoff manifest, visible asset keys, workflow path, checkpoint/control-model names, seed, denoise, output path, and validation result into DML. Reinforce only a validated preservation strategy or a user-approved visual preference.
