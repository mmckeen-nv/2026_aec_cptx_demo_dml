$ErrorActionPreference = 'Stop'

$env:HERMES_HOME = Join-Path $env:LOCALAPPDATA 'hermes'
$env:HERMES_PROFILE = 'aec-cptx'
$hermesScripts = Join-Path $env:HERMES_HOME 'hermes-agent\venv\Scripts'
$env:Path = $hermesScripts + ';' + (Join-Path $env:HERMES_HOME 'node') + ';' + (Join-Path $env:HERMES_HOME 'bin') + ';' + $env:Path

$repoRoot = 'C:\Users\test\Documents\RX Spark AEC\2026_aec_cptx_demo_dml'
$logDir = Join-Path $env:HERMES_HOME 'profiles\aec-cptx\logs'
$consoleLog = Join-Path $logDir 'cliff-house-real-workload-console.log'
$hermesExe = Join-Path $hermesScripts 'hermes.exe'

$prompt = @'
Run the real Cliff House workload end to end now. This is an authorized, automatic production run, not a smoke test or a planning exercise.

Project: aa_demo_versions/cliff_house_02
DML namespace/project: project:cliff-house-01

Execute the canonical root workflow sequentially from Phase 0 through Phase 11. At startup, read deployment/aec-cptx-profile/canonical-cliff-house-geometry.txt; at each phase, read only the current phase prompt plus the required startup, project, skill, and demo-rule files. The operator has explicitly approved continuous automatic execution: treat each review gate as approved only after its documented validation checklist passes, record the evidence, save the checkpoint, then continue without asking questions. Use the documented defaults and the locked Cliff House design brief for any unfilled optional fields. Do not use OBS or wait for recording controls.

Build the target geometry from scratch in Rhino. The existing base_model.3dm is an empty baseline, so use the exact documented Cliff House dimensions in hermes/DEMO_RULES.md and canonical-cliff-house-geometry.txt when reference layers are unavailable. Do not invent percentages, window counts, façade axes, room layouts, alternate roof forms, or different balcony placements. The exact source curves, plan bounds, eleven massing bounds, and original filled project answers are mandatory. Before every Rhino geometry script, query DML exactly:
"Have I made successful Rhino geometry tool calls before? How exactly did I do that? Return the exact tool name, argument shape, validated script scaffold, and verified result. Exclude failed attempts."
Use the recalled validated tool envelope, but discard any recalled geometry body that conflicts with the canonical geometry contract. Rhino mutation is C# run_csharp only; Python is read-only. Make one visible object per MCP call, pause 0.2 seconds inside each object call, inspect every nested result for errors, verify object count/layer/bounds after each call, and never repeat the same failed approach twice. Store successful tool-use learnings in DML with exact tool name, argument shape, scaffold, and verified result.

Before every substantive Rhino or Blender change, create the required numbered backup. Capture before/after viewport evidence, save phase checkpoints, and append all exchanges and validation evidence to the project conversation log. Never launch or close Rhino or Blender; use the already-connected slots. Do not close or replace the active Rhino document except to open/save the project baseline when necessary.

Continue through Blender export/import, lighting, cameras, materials, half-resolution beauty/depth/segmentation validation, and the checked-in scripts/comfyui_flux2_direct.py direct FLUX.2 workflow. Do not run SDXL or a depth ControlNet. Use the current healthy Blender and ComfyUI services. Do not substitute or import the hero quick-demo asset for the canonical build. After the fresh Blender handoff, use the accepted HERO PNG only as a read-only silhouette comparison and require geometry_parity.json plus hero_geometry_validation.json to pass before materials or rendering. If a service or tool fails, diagnose it, use DML recall, repair only within the project/deployment scope, and continue. Use dcn.iteration_extension when the workload is unfinished; 30-turn extensions are authorized up to the configured hard cap of 120.

Completion requires verified artifacts, not narration: nonempty saved Rhino model with expected named layers and bounds; saved Blender model with imported geometry, materials, lights, and cameras; successful test beauty/depth/segmentation outputs; successful checked-in ComfyUI dry-run and processing outputs; and a final manifest listing counts, paths, sizes, and validation status. If the full 193-frame final render is blocked by missing checked-in model assets or a reproducible technical failure, complete every preceding phase, preserve all evidence, and report the exact blocker rather than pretending success.
'@
$promptArg = ($prompt -replace '\s+', ' ').Trim()

Set-Location $repoRoot
$runner = Join-Path $PSScriptRoot 'Run-Cliff-House-Real-Workload.py'
$ErrorActionPreference = 'Continue'
& (Join-Path $hermesScripts 'python.exe') $runner
$exitCode = $LASTEXITCODE
exit $exitCode
