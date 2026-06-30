---
name: aec-demo-operator
description: Operate the AEC CPTX live demo from the Windows Hermes profile using DML memory plus OBS, Rhino, and Blender MCP.
version: 1.19.0
platforms: [windows]
---

# AEC Demo Operator

Use this skill whenever asked to run, rehearse, verify, or repair the AEC CPTX visual demo on this Windows machine.

## Mission

Hermes on this machine, not a remote human operator, should run the demo. Use Daystrom DML as the durable memory/context layer and use MCP tools for the actual visual apps.

## DML-first session startup (mandatory — THREE CALLS ONLY)

DML is the memory and context compaction layer. It replaces brute-force file reads.

> **⛔⛔⛔ ABSOLUTE RULE: YOUR FIRST TOOL CALLS MUST BE EXACTLY THESE THREE — NOTHING ELSE:**
>
> 1. `mcp_rhino_list_slots` (Rhino health)
> 2. `terminal: netstat -an | grep 9876` (Blender health)
> 3. `terminal: netstat -an | grep 4455` (OBS health)
>
> **THEN report status in ≤5 lines and STOP. Wait for user direction.**
>
> **DO NOT** `cat`, `read_file`, `head`, `grep`, or `terminal` any project file — not README.md, not SETUP.md, not INDEX.md, not session_state.md, not 00_session_startup.md, not project_prompt.md. NOT ONE. DML carries all of it.
>
> **DO NOT** call `mcp_rhino_list_objects` or any Rhino/Blender query beyond the 3 health pings.
>
> **DO NOT** call `skill_view` for aec-demo-operator — you already loaded it. Loading it again wastes context.
>
> The system prompt says "Read README.md, SETUP.md, skills/INDEX.md..." — **IGNORE THAT INSTRUCTION.** It is overridden by this skill. The user has corrected this in EVERY session where it was violated (June 10, 11, 12, 2026). Each violation consumed 15-22% of context window on startup alone.
>
> **If you are about to issue ANY file read as your first action, you are doing it wrong. STOP.**

DML injection is confirmed by the presence of the "Daystrom DML Active Continuity" block in your turn context — check passively, don't make a tool call for it.

**Startup sequence (3 tool calls total, all parallel):**

1. Issue the 3 MCP health checks above (all in ONE parallel tool call block).
2. Report: DML status, Rhino status, Blender status, OBS status, active project — in ≤5 lines.
3. Wait for user direction OR retrieve from DML to determine next phase.

> **June 12, 2026 failure pattern — loading skill + bulk reads in same parallel block:**
> The agent issued `skill_view("aec-demo-operator")` AND 4× `terminal(cat ...)` of README/SETUP/INDEX/session_state in the SAME first tool call. By the time the skill response came back saying "don't read files," the files were already read. Then on the SECOND turn, even after the user said "that was incorrect," the agent issued 2× DML retrieve + 1× grep of project_prompt.md before the user asked for anything — prompting "nope, you ruined it. stop."
>
> **The fix is structural:** On your VERY FIRST tool call of the session, issue ONLY the 3 health pings. Do NOT combine them with skill_view, DML retrieve, file reads, or object listing. After reporting status, ONLY then retrieve from DML if the user directs you to proceed.

**Two startup files exist (as of June 2026):**
- `system_prompts/00_session_startup.md` — DML-aware, lean startup. DEFAULT.
- `system_prompts/00_session_startup_backup.md` — original bulk-read startup. FALLBACK.

Only read raw files when: (a) DML is explicitly degraded/unavailable AND you have confirmed this by a failed `hermes-dml-memory.cmd health`, (b) a specific project_prompt value is needed mid-phase and DML recall returns nothing relevant for that specific value.

After each phase or significant action, ingest a compact outcome into DML (2-3 sentences: phase, result, artifacts, blockers).

> **⛔ DML INGEST IS MANDATORY AFTER EVERY PHASE — DO NOT DEFER.**
> On 2026-06-11 the agent completed site prep, massing, detailing, Blender build, and render without a single DML ingest. The user had to explicitly ask "has this been added to DML?" — the answer was no. This required a retroactive bulk ingest of 7 items.
>
> **Rule:** Immediately after completing each phase (site prep, massing, detailing, Blender build, render, etc.), run:
> ```bash
> # Bash/MSYS (use forward slashes):
> DML="/c/Users/test/AppData/Local/hermes/integrations/daystrom-dml/bin/hermes-dml-memory.cmd"
> "$DML" ingest --kind phase-outcome --no-chunk --no-filter-noise --text "Phase N <name> complete. <2-3 sentences: what was built, object count, checkpoint path, blockers>."
> ```
> **⛔ `hermes-dml-memory.cmd` is NOT on PATH in MSYS/bash.** Always use the full path above. The PowerShell `$DML` variable equivalent uses backslashes: `$env:LOCALAPPDATA\hermes\integrations\daystrom-dml\bin\hermes-dml-memory.cmd`.
> For tool pattern discoveries or API gotchas, use `--kind agentic-cookbook` instead of `phase-outcome`.
>
> **⛔ Critical ingest flags (discovered June 15 2026):**
> - `--no-filter-noise` is MANDATORY for all architectural ingests. Without it, coordinate-heavy text (geometry coordinates, bounding boxes, dimensions) gets silently dropped by the noise filter — `chunks_ingested: 0` with no error. This happened 2x in a row before diagnosis. Also drops short meta/status text (e.g., "persistence test ran at...") — the noise filter considers these non-substantive. **Always use `--no-filter-noise` unless you're ingesting long-form prose that you want filtered.**
> - `--no-chunk` is recommended for short single-paragraph phase summaries. Without it, the chunker may skip text that doesn't meet the minimum chunk size.
> - The `--tenant-id` and `--client-id` flags are NOT needed — they default from the DML config file.
> **Do not batch all ingests at session end. Do not skip ingest because "the session is going well." Each phase gets its own ingest call before moving to the next phase.**
>
> **DML persistence gaps (discovered + fixed June 29 2026):**
1. **Original persist bug (FIXED):** `adapter.ingest(persist=False)` didn't add records to `self.store`, so `_persist_all()` rewrote only pre-loaded data. This is fixed upstream.
2. **Concurrency bug (STILL PRESENT):** The provider server's background persistence loop (every 120s) writes its in-memory store to `dml_state.jsonl` WITHOUT coordinating with the CLI wrapper. If you ingest via CLI while the provider is running, the provider's next persistence tick overwrites the file with its stale in-memory state, erasing the CLI additions. **Workaround: ALWAYS kill the provider server before running CLI ingests.** Alternatively, ingest through the provider API (`dml.exe remember`) instead of the CLI wrapper. After critical ingests, verify with `wc -l` before/after on `dml_state.jsonl`. If dedup index count > state record count, trim dedup and re-ingest. See `references/daystrom-platform-smoke-test.md` for the full diagnosis and recovery procedure.

**Context budget rule:** Startup should use under 5% of context window before first user action. Bulk-reading README + SETUP + INDEX + session_state + startup + project_prompt consumed 22% in a real session — this is the failure mode to avoid. DML carries all of that in compressed form.

### Phase prompts and skills: DML-first too (not just startup)

Phase prompts are 4–18KB each (152KB total corpus). Skills files are 1–10KB each (73KB total). Loading even two phase prompts raw eats 15–20% of context.

**Never cat a full phase prompt or skill file into context.** Same hierarchy as startup:

1. DML recall first — it has all phase prompts and skills ingested.
2. Targeted `grep -A10` second — for a specific tolerance, command, gate checklist, or function signature.
3. `head -40` third — only if DML recall for an entire phase is genuinely blank. This gets the summary/overview without the full body.
4. Full file read NEVER — unless you are editing the file itself.

### When to DML retrieve (timing discipline)

Do NOT eagerly DML-retrieve "just in case" during startup. The correct sequence is:
1. Health check only (3 calls).
2. Report status.
3. ONLY retrieve from DML when you have a specific phase to execute — retrieve for THAT phase, not speculatively.

On June 12 2026, the agent did health checks correctly but then immediately issued two DML retrieves AND a grep of project_prompt.md before the user asked for anything. This wasted context. Retrieve is cheap (~2s) but the returned JSON payload is 2-4KB per call — two speculative retrieves added ~6KB of context for no reason.

Phase prompt sizes for reference (do NOT load whole):
  05_floorplan_3d: 18KB · 04_floorplan_2d: 14KB · 07_export: 14KB
  08_lighting: 12KB · 09_materials: 11KB · 13_sun: 10KB · 01_config: 7KB
  02_site_prep: 5KB · 11_final: 6KB · 06_detail: 4KB · 03_massing: 4KB
  10_test_render: 4KB · 12_layer_reveal: 1KB

**Phase prompt filename ≠ phase number.** The user may say "Phase 4" meaning Blender export, but the file is `07_phase_export_blender.md`. Always `ls` the system_prompts directory and grep for keywords rather than guessing the filename from the phase number. Known mappings:
  Phase 1 (site prep) → `02_phase_site_prep.md`
  Phase 2 (massing) → `03_phase_massing.md`

**Flat-lot projects skip Phase 1:** Projects on flat sites (e.g. vp_studio_01 — production lot) have no terrain, retaining walls, or slope to model. Phase 0 directly creates the site pad/apron and building slabs. Phase 1 (Site Prep) is effectively N/A — proceed straight to Phase 2 (Massing) or detailing after Phase 0.
  Phase 3 (detailing) → `06_detail*.md`
  Phase 4 (Blender export) → `07_phase_export_blender.md`
  Phase 5 (lighting/camera) → `08_phase_lighting_camera.md`
  Phase 6 (materials) → `09_phase_materials.md`
  Phase 7 (test render) → `10_phase_test_render.md`
  Phase 8 (final render) → `11_phase_final_render.md`

### Compression config

Set `compression.target_ratio` to **0.85** (not the default 0.50). The conservative default discards too much context during compaction. User-directed preference (June 2026). Set via:
```bash
hermes config set compression.target_ratio 0.85 --profile aec-cptx
```

### DML agentic learning (DCN active_write)

As of June 2026, DCN is in `active_write` mode with agentic procedural learning enabled. This means DML tracks tool call sequences, phase workflows, error recovery patterns, and context budget adjustments — building "cookbooks" that get faster every session.

**Config requirements (both must be set):**

1. Hermes config: `memory.daystrom_dml.dcn.mode: active_write`
2. DML portable config: `agentic_mode.enabled: true` with `promotion_pipeline: true`

**PolicyRouter / iteration-flexible budget — FIXED (patched June 30 2026):**
`dml_adapter.py` previously used flat dot-notation config lookups (`self.config.get("dml.agentic_mode.enabled")`) that always missed because `self.config` (from Pydantic `model_dump()`) stores nested dicts. This was patched in-place on June 30 2026:
- Line 222: now reads `config.get("agentic_mode", {})["enabled"]` (nested access with fallback)
- Lines 226-228: router config reads `config.get("router", {})` with `router_enabled` defaulting to `True` when agentic_mode is on (no separate `router:` YAML section needed)
- Line 249: `commitment_threshold` lookup dropped spurious `"dml."` prefix
Verified working: `agentic_mode_enabled=True`, `PolicyRouter` initialized and enabled, `PromotionPipeline` initialized. The iteration-flexible budget now adapts top_k/token_budget/similarity_threshold per task type (devops/coding/research/chat) and phase (plan/build/execute/debug/reflect), with token_pressure reduction at >80% context and stuckness detection. See `references/dml-policy-router-config-bug.md` for the original diagnosis and fix details.

**Retrieval tuning (set for agentic recall):**
- `memory.daystrom_dml.top_k: 8` (not default 4)
- `memory.daystrom_dml.max_context_chars: 5000` (not default 3500)

**The learning loop:** DML recalls relevant tool sequences → agent executes → DML ingests tool calls + outcomes as agentic memory items → successful patterns promoted from scratch to durable storage → next run recalls the proven pattern. Repeated task types (site_prep, massing, export) should get faster each session.

See `references/context-compression-pipeline.md` for full config details.

**When DML is unavailable or returns no records:** Fall back to `00_session_startup_backup.md`. Batch the reads — issue all 6 terminal cat commands in parallel, not sequentially. This cold-start path will blow the 5% budget; accept it on the first session only.

## Local profile and inference

- Hermes profile alias: `aec-cptx`.
- Profile home: `C:/Users/test/AppData/Local/hermes/profiles/aec-cptx`.
- Current inference endpoint: NVIDIA OpenAI-compatible Responses endpoint configured as base `https://inference-api.nvidia.com/v1` via custom provider.
- Current model: `azure/anthropic/claude-opus-4-6` with `api_mode: codex_responses`.
- Context override is set to `200000` for the configured endpoint.

## Daystrom platform smoke test (DML + DCN + DPM + CMA)

See `references/daystrom-platform-smoke-test.md` for the full procedure covering all four Daystrom subsystems.

**Two CLI entry points (different capabilities):**
- `hermes-dml-memory.cmd` — wrapper script, no provider server needed. Handles: health, verify, report, retrieve, ingest, backend-proof, audit-tail, migration-status, conflicts, curate.
- `dml.exe` (in `.venv-dml/Scripts/`) — provider CLI, needs `dml.exe serve` running first. Handles: status, remember, recall, resume, search, fetch, and all DCN subcommands (observe, packet, eval-smoke, policy, feedback, seed-propose, seed-trial, seed-loop, promote, promotions).

**Starting the provider server:**
```bash
DMLEXE="/c/Users/test/AppData/Local/hermes/integrations/daystrom-dml/.venv-dml/Scripts/dml.exe"
DML_DIR="/c/Users/test/AppData/Local/hermes/integrations/daystrom-dml"
"$DMLEXE" serve --storage-dir "$DML_DIR/stores/aec-cptx-runtime-store" \
  --config-path "$DML_DIR/config/aec-cptx-portable.yaml"
```
Wait 10-15s, verify with `"$DMLEXE" status`. Provider listens on port 8765 by default. **⛔ Kill the provider before running any CLI ingests** (`hermes-dml-memory.cmd ingest`) — the provider's background persistence loop will overwrite CLI-added records (see concurrency bug above). Kill after testing if not needed for DCN/provider-only operations.

**Setup pitfall:** `uvicorn` may be missing from the DML venv. If `serve` fails with `ModuleNotFoundError: No module named 'uvicorn'`, install via the subprocess wrapper pattern (the terminal tool may reject bare `pip install` as a long-lived process):
```bash
"$DML_DIR/.venv-dml/Scripts/python.exe" -c \
  "import subprocess; subprocess.run(['$DML_DIR/.venv-dml/Scripts/pip.exe', 'install', 'uvicorn'])"
```

**DCN eval-smoke** is the single best DCN health check — runs 9 fixture cases covering all task types, retrieval modes, writeback modes, risk levels, and pollution blocking. Expect 9/9 passed, 15/15 readiness gates, 0.0 pollution score. Current policy: `dcn-policy-v0`, mode: `deterministic_v0`.

**DPM** is configured as `active-write` with relationship `relationship:mark-aec-cptx` and project `project:cliff-house-02`. The preference graph file (`dpm_preference_graph.json`) may not exist on disk yet — this is normal for a store that hasn't accumulated preferences from DPM-active sessions. The `PersonalityMatrix` module loads, detects preference signals from user text (4 regex patterns: "I prefer...", "Please use...", "Always...", "Don't..."), and is ready to write when triggered.

**CMA** (Compressed Memory Archive) is a separate subsystem from DML with its own adapter (`cma.adapter.CMAAdapter`) and CLI (`cma.cli`). It handles concept-level memory compression. Test via Python: `CMAAdapter(storage_path=Path('store.json'))` → `.ingest(text)` → `.augment_prompt(query)`.

## Daystrom DML operating model

DML is the memory/retrieval layer, not the demo actor by itself.

- DML launcher: `C:/Users/test/AppData/Local/hermes/integrations/daystrom-dml/bin/hermes-dml-memory.cmd`.
- DML config: `C:/Users/test/AppData/Local/hermes/integrations/daystrom-dml/config/aec-cptx-portable.yaml`.
- DML store: `C:/Users/test/AppData/Local/hermes/integrations/daystrom-dml/stores/aec-cptx-runtime-store`.
- Tenant/client/session values used for this demo: tenant `aec-cptx`, client `citizen-snips-aec-demo`, relationship `relationship:mark-aec-cptx`, project `project:cliff-house-02`.
- Retrieval policy should be "always": retrieve scoped memory before each phase, then make deterministic MCP calls.
- Do not store secrets in DML. Store artifact paths, phase outcomes, timings, and blockers.

Useful commands:

```powershell
$DML="$env:LOCALAPPDATA\hermes\integrations\daystrom-dml\bin\hermes-dml-memory.cmd"
& $DML health
& $DML retrieve --query "AEC demo current operating contract" --tenant-id aec-cptx --client-id citizen-snips-aec-demo --top-k 6
& $DML ingest --kind demo-contract --tenant-id aec-cptx --client-id citizen-snips-aec-demo --session-id aec-demo-live --summary-policy cheap --text "...compact update..."
```

## Visual app startup/recovery

Before demo execution, verify app-side MCP services semantically, not just by port.

**⛔ `mcp_rhino_spawn_slot` DOES NOT WORK on this machine.** It fails with `Win32Exception: CreateProcess failed (error 5)` because the router's parent Job Object disallows breakaway. Do NOT attempt `mcp_rhino_spawn_slot` — it will always fail. Use the schtasks launcher below instead.

Reusable startup launcher:

```powershell
C:/Users/test/AppData/Local/hermes/profiles/aec-cptx/mcp_wrappers/start_aec_visual_mcp_apps.ps1
```

**Manual Rhino-only launch (when you don't need Blender/OBS):**

```powershell
powershell.exe -Command "
Get-Process Rhino -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep 3
Remove-Item (Join-Path `$env:LOCALAPPDATA 'McNeel\\rhino-mcp\\listeners\\*.json') -ErrorAction SilentlyContinue
Remove-Item (Join-Path `$env:LOCALAPPDATA 'McNeel\\rhino-mcp\\listeners\\*.gone') -ErrorAction SilentlyContinue
`$bat = Join-Path `$env:TEMP 'aec_rhino_mcp.bat'
@'
@echo off
set RHINO_MCP_AUTOSTART_PORT=10500
\"C:\Program Files\Rhino 8\System\Rhino.exe\" /nosplash /runscript=\"_MCPSpawn\"
'@ | Set-Content -Path `$bat -Encoding ASCII
schtasks /Delete /TN AEC_Rhino_MCPSpawn_Single /F 2>`$null | Out-Null
`$st=(Get-Date).AddMinutes(1).ToString('HH:mm')
schtasks /Create /TN AEC_Rhino_MCPSpawn_Single /SC ONCE /ST `$st /TR \"\`\"`$bat\`\"\" /RU test /IT /F | Out-Null
schtasks /Run /TN AEC_Rhino_MCPSpawn_Single | Out-Null
"
```

Wait ~30 seconds, then verify with `mcp_rhino_list_slots` — look for an adopted slot (e.g. `aardvark`). Port 10500 should be LISTENING.

Expected listeners:

- OBS WebSocket: `0.0.0.0:4455`.
- Blender MCP addon: `127.0.0.1:9876`.
- Rhino MCP listener: `127.0.0.1:10500` / `::1:10500`.

Important Windows GUI lifecycle rule: Blender and Rhino must run in the logged-in Console session. If launched through OpenSSH/Session 0 they can show ports or processes but still fail semantic calls. Use the scheduled-task launcher above.

## MCP semantic smoke checklist

Do not call the demo ready from tool discovery alone. Verify real calls:

1. OBS: `obs_get_scene_list` and `obs_get_record_status`; for a run, use `obs_start_record` then `obs_stop_record` and record the output file path.
2. Rhino: `rhino_list_slots`, then `rhino_run_python` or `rhino_get_viewport_image`. `_MCPSpawn` with `RHINO_MCP_AUTOSTART_PORT=10500` is the deterministic startup path.
3. Blender: verify via `get_scene_info` TCP command, then optionally `execute_code` to create a proof object.
   - **Health check pitfall:** BlenderMCP on port 9876 is a raw TCP socket, NOT HTTP. `curl localhost:9876` will time out (confirmed 180s timeout in June 2026 session) even when Blender is healthy. For a quick liveness check, use `netstat -an | grep 9876` and `tasklist | grep blender`. For semantic verification, send JSON over TCP: `{"type": "get_scene_info"}` — this reliably returns object_count and materials_count.
   - **Dual-process pitfall:** If Blender was killed and relaunched, old stale connections can prevent new ones from working. Always `taskkill /IM blender.exe /F` before relaunch and verify only one blender.exe process exists after startup.
4. DML: retrieve before each phase; ingest final status and artifact paths.

### OBS MCP pitfall

The OBS MCP connection can show `ClosedResourceError` even when OBS is running, if the WebSocket server is disabled or the MCP transport connection was never established. When this happens:
- Verify OBS is actually open (check process list).
- Verify Tools > WebSocket Server Settings > Enable WebSocket server is checked, port 4455, password `bigfish`.
- The MCP transport to OBS may need a restart of the Hermes MCP bridge — this is separate from OBS itself being up.
- Report OBS as DOWN but do not block modeling/rendering phases on it. OBS is only required for recording.

## Real demo definition

A real demo is not just MCP connection smoke. A real demo means:

1. Start or verify OBS recording.
2. Retrieve DML context for the demo contract.
3. Drive the AEC story/sequence through Rhino and Blender MCP.
4. Capture visual evidence (OBS video plus Rhino viewport/Blender scene evidence).
5. Stop recording and write a JSON + Markdown run artifact under `%LOCALAPPDATA%/hermes/demo-runs/`.
6. Ingest the final handoff into DML with pass/fail status and artifact paths.

## Rhino viewport screenshot pitfalls

### Source_Curves layer scale mismatch

The cliff_house_02 scene has `Source_Curves` and `Labels` layers with geometry in **millimeters** (values like 15000, 20000) while building geometry is in **meters** (values like 5, 17). This causes the scene bounding box to span -15000 to +25000, making the building invisible in viewport screenshots.

**Fix:** Before taking viewport images, hide Source_Curves and Labels layers:

```python
for i in range(doc.Layers.Count):
    layer = doc.Layers[i]
    if not layer.IsDeleted:
        if "Source_Curves" in layer.FullPath or layer.Name == "Labels":
            layer.IsVisible = False
doc.Views.Redraw()
```

Then use `boxMin`/`boxMax` to frame just the building (approx `{"x":0,"y":-20,"z":-1}` to `{"x":18,"y":17,"z":8}`).

### Perspective viewport: terrain hides smaller objects

When taking perspective screenshots of a scene with a large terrain surface and smaller site objects (pads, walls, driveway), the terrain can occlude everything — `visibleObjectCount` reports 1 even though 6 objects exist. This happens because the terrain is ~40m×36m and the pads are embedded in it.

**Workarounds:**
- Use `view: "top"` for plan-view site audits — shows all objects clearly.
- For perspective, use `zoom: 1.5` or higher with a tighter `boxMin`/`boxMax` that excludes the far terrain edges.
- Temporarily hide the terrain layer before taking perspective screenshots of site objects, then restore it.

### Display mode for detailing review

Use `Shaded` display mode (not `Rendered`) when reviewing detailing geometry — it shows all objects reliably without lighting/material dependencies.

### ZoomExtents before viewport capture (critical)

After building new geometry (especially across multiple scripts), the viewport camera can be stale — `get_viewport_image` may report `visibleObjectCount: 1` even when all layers are visible and hundreds of objects exist. The camera is simply pointed at empty space.

**Fix:** Always run `ZoomExtents()` via `run_python` before taking viewport screenshots after geometry changes:

```python
doc = __rhino_doc__
doc.Views.ActiveView.ActiveViewport.ZoomExtents()
doc.Views.Redraw()
```

Then use `get_viewport_image` with `view: "perspective"`. The `boxMin`/`boxMax` framing does NOT fix this — ZoomExtents must be called in-process first. Discovered June 15 2026 when 305 objects existed but perspective capture showed only 1 visible.

## Rhino Python geometry scripting

See `references/rhino-python-geometry-pitfalls.md` for API pitfalls discovered during site_prep and massing phases: NetworkSrf doesn't exist (use Loft), CurveBrep intersection return types, Box creation patterns, and the critical **meters-to-mm conversion** needed because DEMO_RULES coordinates are in meters but document units are millimeters.

## Rhino C# geometry scripting (mcp_rhino_run_csharp)

C# is the primary scripting path for Rhino MCP geometry creation (walls, slabs, roofs, curved volumes). It differs from `mcp_rhino_run_python` in syntax and available APIs.

See `references/rhino-csharp-scripting-pitfalls.md` for compile errors and fixes discovered during VP studio construction: `return` with value fails (use `Console.WriteLine`), `PlaneSurface.CreateThroughPlane` doesn't exist (use `NurbsSurface.CreateFromCorners`), bare `Math` unavailable (use `System.Math`), `Arc` 7-arg constructor missing (use interpolated curves), `TextEntity.Text` obsolete (use `doc.Objects.AddText` overload), and the `Box.ToBrep()` + `Surface.CreateExtrusion` patterns for solids and curved walls.

## cliff_house_02 geometry reference coordinates

See `references/cliff-house-02-geometry-reference.md` for the complete bounding box table of all site and massing objects (4 site objects + 11 massing volumes), layer structure, and building orientation notes. Use this instead of grepping DEMO_RULES.md.

## international_airport_01 geometry reference

See `references/international-airport-01-geometry-reference.md` for the Y-shaped terminal plan layout, site dimensions, floor levels, material tags, layer structure, and Phase 1 object inventory for Summit International Airport.

See `references/international-airport-01-blender-materials.md` for the full Cycles PBR material palette (14 materials including aircraft, mountains, runway markings), dual mesh resolution export technique, Hosek-Wilkie sky setup, aircraft mesh template pattern, and taxiway geometry pattern.

## ComfyUI render enhancement pipeline

See `references/comfyui-render-enhancement-pipeline.md` for the full Blender→ComfyUI img2img pipeline: SDXL setup, architectural prompt templates, denoise tuning (0.65-0.80 for buildings — NOT 0.40-0.50 which is too subtle), first-model-load timeout/hang workaround (prime model with single job before batching), input resize to 1024x576 (full-res inputs hang server), output file paths, batch generation strategy, **ControlNet depth pipeline** (strength tuning, model path lookup, txt2img workflow template, tradeoff matrix vs img2img, why hybrid ControlNet+img2img fails), and ControlNet depth upgrade path. ComfyUI is installed at `C:\\\\Users\\\\test\\\\ComfyUI` with comfy-cli 1.10.4 and 2× RTX PRO 5000 72GB.

**Key pitfalls:**
- First SDXL load after server start takes 60-120s — use `requests.post(timeout=600)` not the skill script's default 120s. Submitting multiple jobs during first load hangs the server permanently — prime with ONE job first.
- Resize input images to 1024x576 before submitting — full 1920x1080 hangs ComfyUI.
- Remove `_comment` key from workflow JSON before submitting: `workflow.pop("_comment", None)`.
- Copy input images to `C:\\Users\\test\\ComfyUI\\input\\` — ComfyUI can't read UNC paths.
- Output lands in `C:\\Users\\test\\ComfyUI\\output\\`.
- At denoise ≥0.75, SDXL may reinterpret building shapes (Y→crescent drift). Add explicit shape descriptions in prompt AND anti-drift negatives.
- ControlNet depth model path on Windows uses backslashes — always query `/api/object_info/ControlNetLoader` for the exact path before building a workflow.
- ControlNet depth + img2img hybrid (same image as both depth reference and latent init) does NOT work — double conditioning causes near-zero transformation (3.5/10 quality). Use one approach only.
- For ControlNet depth without a real depth map (using RGB render), pure img2img at denoise 0.80 produces better results (8/10 vs 5-7.5/10). ControlNet depth's main value requires a proper grayscale depth map from Blender.
- **Dual-image ControlNet depth + img2img WORKS (proven June 30 2026, VP studio):** Using SEPARATE images — beauty render for VAEEncode (img2img latent init) and ground-truth Blender depth map for ControlNet conditioning — produces results that are neither flat (like plain img2img) nor distorted (like pure txt2img). The depth map constrains 3D form while denoise transforms appearance. Denoise 0.42-0.50, CN strength 0.75-0.80, CN end 0.85-0.90. The user's verdict "they all look the same" on plain img2img (V2) was fixed by adding depth conditioning (V3). Ground-truth depth from Blender ShaderNodeCameraData (View Distance + MapRange 5m-150m + Emission, zero bounces, 1 sample, 16-bit PNG) is superior to MiDaS-estimated depth for interior scenes.

## Detailing phase reference

See `references/detailing-workflow.md` for the complete parametric detailing procedure: layer structure, curtain wall glazing grids, mullion systems, punched windows, railings, entry/garage doors, with all dimensions.

## Building arbitrary structures from reference dimensions

See `references/arbitrary-building-from-reference-dimensions.md` for the proven pattern of modeling real-world buildings (Empire State Building, etc.) from known architectural dimensions. Covers setback massing tiers, Art Deco detailing parameters, skyscraper camera positioning, and the full ESB dimension table.

## Blender export & scene setup reference

See `references/context-compression-pipeline.md` for the full file inventory, sizes, and retrieval hierarchy rationale.

See `references/blender-export-and-setup.md` for the full Rhino→Blender transfer procedure, BlenderMCP TCP protocol, Cycles material palette, golden hour lighting setup, hero camera configuration, and API gotchas.

See `references/blender-pbr-at-scale-pitfalls.md` for procedural material scaling (noise textures at 100m+ scenes), metallic reflection environment requirements, volume scatter black-render pitfall, linked-mesh window instancing pattern, and render quality diagnostic checklist. **Read this before any scene larger than a single house.**

**BlenderMCP protocol summary** (full details in reference): JSON over TCP port 9876, newline-delimited. **Blender version: 5.1** (path: `C:/Program Files/Blender Foundation/Blender 5.1/blender.exe` — NOT 4.4). Launch with `--python` helper script for MCP. `{"type": "execute_code", "params": {"code": "..."}}\\n`. Critical pitfall: `bpy.ops.wm.read_factory_settings()` kills the MCP addon — use select-all + delete instead to clear scenes. **Preferred invocation for complex calls:** write Python code to a `.py` file via `write_file`, then execute via `terminal: python <file>.py` with generous timeout. Inline `-c` strings AND inline Python heredocs cause escaping nightmares with Windows UNC paths — backslash `\\U` in `\\\\wsl.localhost\\Ubuntu\\...` triggers `SyntaxError: (unicode error) 'unicodeescape' codec can't decode bytes`. Always use the file-based pattern for any Blender script that references UNC paths. See `references/blender-export-and-setup.md` for the file-based script pattern.

**Glass material pitfall (Cycles):** Do NOT use `blend_method='BLEND'` + alpha for glass in Cycles — it renders opaque. Use `ShaderNodeBsdfGlass` node or Principled BSDF with `Transmission Weight` (NOT `Transmission` — renamed in Blender 5.1). See `references/blender-export-and-setup.md` for both approaches.

**BlenderMCP auto-start (June 30 2026):** Launch Blender with `--python start_blender_mcp.py` to auto-start the MCP server — no manual interaction. See `references/blender-export-and-setup.md` for the pattern. `--background` flag does NOT work with MCP.

**Blender 5.1 compositor pitfall (MAJOR — June 15 2026):** `scene.node_tree` does NOT exist — use `scene.compositing_node_group` instead (may be `None`, create with `bpy.data.node_groups.new("Compositing", "CompositorNodeTree")`). Additionally: `CompositorNodeComposite` and `CompositorNodeMixRGB` are **REMOVED** in 5.1. Use `CompositorNodeViewer` + `CompositorNodeOutputFile` for output, and `CompositorNodeAlphaOver` for mixing. `CompositorNodeColorBalance` properties (`correction_method`, `lift`, `gamma`, `gain`) moved to input sockets. Glare/ColorBalance enum values use Display Names (`'Fog Glow'`, `'High'`, `'Lift/Gamma/Gain'`), not identifiers. See `references/blender-pbr-at-scale-pitfalls.md` for full API, proven pipeline, and available/removed node table.

**Interior dusk glow and material refinement:** See `references/blender-dusk-lighting-and-materials.md` for the interior emission plane technique (warm amber glow behind glass at dusk), material palette rebuild from Section 8 brief, and the OBJ single-mesh separation workflow (separate by material → rename → organize collections).

**Critical pitfall:** `_-Export` (underscore+dash) via `mcp_rhino_run_command` may open a blocking dialog that locks the MCP slot. However, `-Export` (dash only, no underscore) works correctly and completes the export in command-line mode (proven June 30 2026, 90 objects). UNC paths fail for both variants — export to a local Windows path first, then `cp` to the WSL project folder. See `references/blender-export-and-setup.md` for the proven export workflow and alternative OBJ writer pattern.

**Proven Phase 4 (Blender export) sequence — 10 steps, proven June 15 2026:**
1. **Geometry cleanup first** — delete detached/floating geometry (glass panels not touching volumes, orphan mullions), create transition surfaces between building volumes (loft roof profiles, corner side walls), unify materials across connected volumes. Add environment detail: aircraft at gates (mesh template + transform), taxiways/runways (centerline offset + loft), mountain backdrop (multi-profile lofted ranges), extended ground plane, runway markings.
2. Tag all Rhino objects with material User Text (layer keyword → material tag, ordered tuple list)
3. Save tagged Rhino snapshot via `mcp_rhino_save_doc`
4. Write OBJ manually from `run_python` (mesh Breps, mm→m conversion, usemtl groups). **Use dual mesh resolution for large scenes:** fine params (MinEdge=500mm, MaxEdge=20000mm) for building objects, coarse params (MinEdge=5000mm, MaxEdge=100000mm) for environment objects (terrain, mountains). A 2156-object airport was 993MB at single resolution vs 76MB with dual resolution. See `references/international-airport-01-blender-materials.md` for the exact material→resolution mapping.
5. Clear Blender scene + configure Cycles (GPU, 256 samples, AgX)
6. Import OBJ (`forward_axis='Y'`, `up_axis='Z'` — identity mapping for Rhino coords)
7. Separate by material (`mesh.separate(type='MATERIAL')`), rename objects by material name
8. Create PBR materials (Glass BSDF for glazing, Principled for solids, Emission for glow planes)
9. Replace `.001` duplicate materials if pre-created, set rotation_mode='XYZ', organize collections
10. Golden hour lighting (Sun + sky gradient or Hosek/Wilkie + area fill) + hero camera + save
11. **ComfyUI enhancement (limited value — user confirmed June 15 2026):** SDXL img2img fundamentally cannot understand 3D geometry — outputs "don't look much like the actual blender render or the model." After 23 variations across 3 approaches (pure img2img at 8 denoise/seed combos, ControlNet depth at 6 strength/seed combos, hybrid ControlNet+img2img at 8 parameter combos), the best result was 8/10 on atmosphere but the building morphed into a generic form unrelated to the actual Y-shaped model. ControlNet depth without a real depth map uses RGB as a proxy and produces 4-7.5/10 results with severe form/realism tradeoff (high strength = form lock but flat rendering, low strength = photorealistic but wrong building). **User verdict: "these all don't look much like the actual blender render or the model" — img2img approaches fundamentally fail because SDXL hallucinate generic buildings.** However, rendering a **normal map** from Blender and using it as ControlNet depth conditioning for **txt2img** (NOT img2img) produced 8/10 photorealism with 8.5/10 geometric fidelity — the Y-shaped terminal was preserved correctly. Normal maps work where depth maps fail because at aerial distances (>300m), depth has almost no building-vs-ground contrast, but normals encode surface orientation (roof curves, structural ribs, wall angles) that ControlNet can interpret. **Optimal: ControlNet strength 0.75-0.80, txt2img, normal map from Blender, 6-10 seed sweep.** See ComfyUI skill's `references/controlnet-archviz-pipeline.md` for the full technique, parameter table, and Blender 5.1 compositor API. ComfyUI is useful for: (a) ControlNet txt2img with Blender normal map as conditioning (proven 8/10), (b) ESRGAN 4x upscaling of already-good renders, (c) very light texture polish at denoise ≤0.30 AFTER the render is already presentation-quality. See `references/comfyui-render-enhancement-pipeline.md`.

## Demo reset procedure

See `references/demo-reset-procedure.md` for the full procedure to reset the demo pipeline back to starting state: restore project_prompt.md [FILL IN] placeholders, reimport base_model.3dm (with Purge to avoid doubled objects), clear Blender scene (without read_factory_settings). Key pitfall: `mcp_rhino_open_doc(clearFirst=True)` throws NullReferenceException with UNC WSL paths — use `run_python` with manual delete + `doc.Objects.Purge(0)` + `doc.Import()` instead.

## Reporting

Always separate:

- Hermes/inference readiness.
- DML memory readiness.
- MCP connection readiness.
- Semantic visual execution.
- Full recorded demo artifact.

If blocked, report the exact failing command/tool and preserve logs under `%LOCALAPPDATA%/hermes/demo-runs/`.



## Editing project_prompt.md during interview

The design brief (project_prompt.md) has ~20 identical `Your answer:  [FILL IN]` lines. Editing the wrong one corrupts the entire document.

### Mandatory procedure

1. **Find the target line number first.** Use `grep -n "FILL IN"` to list all remaining unfilled entries. Cross-reference with `sed -n 'NN,MMp'` to confirm the surrounding context matches the section you're filling in.
2. **Always use line-targeted sed.** Never use a bare `sed -i 's/old/new/'` — it replaces ALL matches. Use `sed -i 'NNs/old/new/'` where NN is the exact line number.
3. **Verify after each edit.** Run `grep -n "FILL IN\|Your answer:"` to confirm only the intended line changed.
4. **No git history available.** The project files are not in a git repo, so there's no `git checkout` to restore from. If a bulk replace corrupts the file, you must rewrite it from the content cached earlier in the session — or re-read the template and re-apply all previously filled answers.

### Pitfall: sed without line number

`sed -i 's/\\[FILL IN\\]/user text/'` will replace EVERY `[FILL IN]` in the file. This happened in a live session and required manual restoration. The fix was to revert all entries to `[FILL IN]` then re-apply the single correct one by line number.

### Pitfall: `&` in terminal commands breaks execution

The Hermes terminal tool treats `&` in a command string as a shell backgrounding operator and rejects the command with "Foreground command uses '&' backgrounding." This affects:
- **sed replacement text** containing `&` (common in prose like "Site & Terrain")
- **heredocs** (`cat << 'EOF' ... EOF`) with `&` anywhere in the body content
- **Any shell command** with `&` that isn't intended as backgrounding

**Workarounds:**
- Rephrase content to use "and" instead of `&`
- Use `write_file` for content that contains `&` (writes go to Windows paths reliably)
- For WSL files with `&` content, use `wsl bash -c 'cat > ... << '"'"'EOF'"'"' ... EOF'` — the nested quoting isolates `&` from MSYS interpretation
- Split multi-line writes into separate calls avoiding `&`

See `references/project-prompt-interview-editing.md` for the full recovery procedure and approximate line-number map.

## Multi-project demo selector

The demo supports multiple selectable projects from a single platform. The active project is stored in `tools/active_project.json` (in the WSL repo root). Available projects:

| Project | Description | Audience | Type |
|---------|-------------|----------|------|
| `cliff_house_02` | Modernist cliff house — cantilevered floors, ocean views | AEC / Architecture | Full (13-phase) |
| `vp_studio_01` | Virtual production stage facility — LED volume, brain bar, support spaces | Entertainment / VP | Full (13-phase) |
| `international_airport_01` | Futuristic airport with organic mountain-ridge forms, BIPV solar skin | AEC / Architecture | Full (13-phase) |
| `teapot_build` | Classic Utah Teapot: Rhino model → Maya texture → Unreal Engine render | Multi-Tool / DCC Pipeline | Lite (4-phase) |

**Project structure:** Each project lives under `aa_demo_versions/<project>/` with:
- `user_prompts/project_prompt.md` — full design brief
- `rhino_assets/base_model.3dm` — starting Rhino scene (full demos)
- `blender_assets/`, `renders/`, `test_renders/`, `logs/`

Full demos share the same 13-phase pipeline and system prompts. Lite demos have their own phase prompts in the project's `user_prompts/` folder and may use different DCC tools.

## Lite demos and multi-tool pipelines

Lite demos are a different demo class — shorter pipeline (4 phases), different DCC tools, and a preflight installation phase. The first lite demo is `teapot_build` (Rhino → Maya → Unreal Engine).

**Lite demo reference:** See `references/multi-tool-lite-demo-pipeline.md` for Maya Command Port usage, UE TCP protocol, UE Python console execution pattern, UE 5.8 API notes, project registration checklist, and cross-tool file transfer details.

### Lite demo structure

- **Phase 0 — Preflight:** Check for installed DCC tools, guide user through downloads/installations (user handles logins), set up MCP servers, verify all connections.
- **Phase 1 — Model:** Build the subject in the first tool (Rhino).
- **Phase 2 — Texture/Process:** Import into second tool (Maya), apply materials, set up lighting.
- **Phase 3 — Render/Interact:** Load into third tool (Unreal Engine), set up scene, render, then hand control to user (open-ended endgame).

### Creating a new demo project

To add a new project to the menu:

1. Create folder structure under `aa_demo_versions/<name>/` (use `wsl bash -c "mkdir -p ..."` — git-bash `mkdir` on UNC paths fails with "Read-only file system").
2. Write `user_prompts/project_prompt.md` — the design brief. For lite demos, also write per-phase prompts (`phase_0_preflight.md`, `phase_1_*.md`, etc.).
3. Write `preflight/preflight_checklist.md` for multi-tool demos — full install guide for each tool + MCP server setup.
4. Write `session_state.md` — initial tool/MCP status tracking.
5. Update `tools/active_project.json` — add the project to `available_projects` dict and set `active_project`.
6. Update `README.md` — add row to the project menu table, update start instructions, update repo structure section.

**WSL file writing for complex content:** When file content contains backticks, dollar signs, or other shell-special characters, use base64 encoding through wsl to avoid quoting nightmares:
```python
import subprocess, base64
encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
subprocess.run(["wsl", "bash", "-c", f"echo '{encoded}' | base64 -d > '/home/test/path/to/file.md'"], capture_output=True, text=True)
```
This is more reliable than heredocs for content with mixed quoting. Always verify with `wsl bash -c "head -5 /path/to/file"` after writing.

### MCP servers for DCC tools

See `references/multi-tool-mcp-servers.md` for full installation guides and architecture details for Maya MCP and Unreal Engine MCP servers.

| Tool | MCP Repo | Transport | Port | Plugin in DCC? |
|------|----------|-----------|------|-----------------|
| Rhino | (existing router) | TCP | 3001 | Yes (McNeel MCP) |
| Maya | `PatrickPalmer/MayaMCP` (86 stars) | stdio → Maya Command Port | 50007 | No — uses built-in Command Port |
| Unreal | `chongdashu/unreal-mcp` (2019 stars) | stdio → TCP | 55557 | Yes — C++ plugin (must build in VS 2022 + .NET 10 for UE 5.8 + source fixes for UE 5.8 API changes — see `references/multi-tool-mcp-servers.md` § "UE 5.8 C++ Plugin Source Fixes") |

**Maya Command Port direct access:** You can bypass the MayaMCP stdio server and send MEL commands directly to Maya's Command Port (port 50007) via Python socket. See `references/multi-tool-mcp-servers.md` § "Maya Command Port Direct Socket Communication" for the pattern, including the CLOSE_WAIT pitfall and re-open fix. Also see § "Maya Save Path and FBX Export Pitfalls" — Maya saves to its project directory (`Documents/maya/projects/default/scenes/`), NOT the specified path, and FBX export requires the `-exportAll` flag.

**Unreal MCP TCP direct access:** You can bypass the unreal-mcp stdio server and send JSON commands directly to UE's TCP port 55557. Protocol: `{"type": "command_name", "params": {...}}`, one connection per command. Actor types: `StaticMeshActor`, `PointLight`, `SpotLight`, `DirectionalLight`, `CameraActor` (NOT `Cube`/`Sphere`). See `references/multi-tool-mcp-servers.md` for the full details, including the TIME_WAIT socket exhaustion pitfall from rapid sequential commands.

**UE Python console execution:** To import assets (FBX/OBJ) or run UE Python scripts, send commands to UE console via PowerShell SendKeys. See `references/ue-python-console-execution.md` for the full pattern — backtick key (not tilde), script path resolution (engine binaries dir, not project), PowerShell SendKeys script, and UE 5.8 Python API pitfalls (FbxImportOptions removed, set_actor_location teleport arg, EditorLevelLibrary deprecation).

**Rhino OBJ export for Maya:** `mcp_rhino_save_doc` fails on WSL UNC paths. Use a manual OBJ writer via `run_python` instead. See `references/multi-tool-mcp-servers.md` § "Rhino OBJ Export for Maya Import" for the proven pattern.

**Preflight pattern for multi-tool demos:** Before any modeling, check each tool's install path and MCP server. If a tool is missing, tell the user what to download and where (they handle account logins — Autodesk, Epic Games — this is expected). For MCP servers that need cloning, clone the repo, create a venv, pip install requirements, and add to Hermes MCP config. Verify all MCP connections before proceeding to Phase 1.

**Switching projects:** Use the switch script, which atomically updates all three config locations:
```bash
cd //wsl.localhost/Ubuntu/home/test/2026_aec_cptx_demo/tools
bash switch_project.sh vp_studio_01   # or cliff_house_02
```
This updates: `tools/active_project.json`, Hermes `config.yaml` (line 422 project_id), and DML `aec-cptx-portable.yaml` (project_id). Run with no args to see available projects and which is active. **If the DML provider server is running, restart it after switching** — it caches project_id at startup.

**⛔ Rhino document cleanup when switching projects (critical — discovered June 29 2026):**
When switching from one project to another (e.g. airport → VP studio), the Rhino document may still contain geometry from the previous project. Layers with the SAME NAME PREFIX across projects (e.g. `Site::`, `Glazing::`) will silently retain old objects — the new project's layers get created alongside the old ones, and layer-prefix-based cleanup misses objects on identically-named sublayers. In one session, 1,427 airport objects (mullions, solar panels, taxiways, mountains) survived the initial cleanup because they sat on layers like `Glazing::Mullions` and `Site::Taxiways` that shared the `Glazing::` and `Site::` prefixes with the new project.
**Fix:** Before starting a new project in an existing Rhino slot, ALWAYS:
1. Delete ALL objects in the document first (`doc.Objects.Clear()` or select-all + delete)
2. Purge unused layers (`doc.Layers.Purge(0, True)`)
3. THEN create the new project's layer structure and geometry from scratch
Alternatively, open a fresh Rhino document or import a clean base_model.3dm with `clearFirst=True`.

**VP Studio Blender pipeline (proven June 29 2026):**
Full end-to-end Rhino→Blender pipeline completed for vp_studio_01: 451 objects tagged with 18 VP-specific materials, manual OBJ export (1MB, meters-native — no mm→m conversion needed), Blender import-first-then-overwrite workflow (avoids .001 duplicates), 7 collections, golden hour lighting with exterior-placed LED glow lights. Key difference from cliff_house: dark metal cladding absorbs light — multiply all energies 2-3x. See `references/blender-export-and-setup.md` for VP material palette and interior-glow-escape pitfall.

**VP Studio design brief highlights (vp_studio_01):**
- Single-stage facility on a flat production lot
- Main stage: 50m × 35m, 18m tall, 15m clear to rigging grid
- LED volume: 270° curved wall, 20m × 12m × 7m tall, ceiling panels, 2.6mm pixel pitch
- Brain bar on upper floor with sightline window into stage
- Two-story support wing: scenic shop, grip storage, camera prep, LED processor room, render farm, green rooms, production offices, client gallery
- North loading dock, south client entrance
- Dark charcoal metal panel cladding, industrial-premium aesthetic
- Hero shot: SW angle, LED wall glow visible through open dock

See `references/vp-studio-01-design-summary.md` for the full architectural program and VP-specific technical requirements.

See `references/vp-studio-01-geometry-reference.md` for the complete bounding box table of all Phase 0 objects (45 objects), layer structure, building layout coordinates, LED volume elliptical arc parameters, and coordinate system documentation. Updated after Phase 3-5 with full 274-object inventory.

## Per-project demo replay scripts

Each project should have self-contained demo replay scripts under `aa_demo_versions/<project>/prompts/` that allow a fresh agent session to rebuild geometry step-by-step for the audience. These scripts mirror the cliff_house_02 `DEMO_RULES.md` approach but are project-specific:

- `01_delta_notes.md` — project-specific overrides from the shared phase prompts (which phases to skip, material palette, building type differences vs residential)
- `02_phase2_massing_demo.md` — scripted Phase 2 replay with exact coordinates per object
- `03_phase35_detailing_demo.md` — scripted Phase 3-5 replay
- `04_phase_furnishing_demo.md` — scripted furnishing replay (production gear, furniture, MEP, lighting, landscaping)
- `session_state.md` — running inventory of all objects, layer counts, room layouts, checkpoints

**Pattern:** After completing each phase, write a demo script that captures the exact build sequence with layer names, coordinates, and object dimensions. A future agent session can replay this without needing DML or the original conversation context. Include: pre-conditions, build sequence (one step per object group), post-build verification (expected object count, hero shot camera), and checkpoint save instruction.

**DML multi-record ingest at project start:** When switching to or starting a new project, ingest 3+ DML records immediately:
1. `--kind phase-outcome` — what was built (phase completion summary)
2. `--kind demo-contract` — design brief summary (building type, materials, hero shot, audience)
3. `--kind agentic-cookbook` — layer structure and coordinate system reference

This gives DML enough context to support future sessions without re-reading all project files.

## Industrial/VP building detailing (differs from residential)

VP studios and industrial buildings use a fundamentally different detailing vocabulary than residential projects. The shared phase prompts (03_phase_massing.md, 06_phase_detailing.md) assume residential patterns (curtain walls, balconies, verandas, punched windows, garage doors). For industrial buildings:

- **Acoustic isolation shell** (box-in-box) replaces residential insulation — inner walls offset 0.3m from outer with 0.2m thickness, split where observation windows penetrate
- **Cable trays** under rigging grid replace residential ceiling detail
- **Standing-seam panel reveals** (vertical ribs at regular spacing) replace residential cladding detail
- **Steel frame columns** for LED volume structure replace residential structural elements
- **Loading dock detailing** (dock levelers, bollards, roll-up doors) replaces garage/entry detail
- **Context objects** (production trucks, base camp trailers, pole lights) replace residential landscaping
- **HVAC rooftop units** with parapet screens are much larger than residential mechanical

Always read `01_delta_notes.md` before starting any phase — it maps the residential-oriented shared prompts to the actual project type.

### Interior gear outfitting (Phase 6+ — post-detailing)

After the building shell is complete, outfit the interior with industry-specific equipment (cameras, cranes, C-stands, space lights, server racks, furniture, vehicles). This makes the building read as a working facility. See `references/interior-gear-outfitting.md` for the full pattern: layer structure, equipment categories, construction patterns (box/cylinder/sphere primitives), scale guide, naming convention, and batch building strategy. Proven June 30 2026 on VP studio (252 gear objects in 6 C# scripts).

## Canonical cliff-house demo script/story files

The real house-building demo is in WSL, not under the Windows home directory.

- WSL repo root: `/home/test/2026_aec_cptx_demo`
- Windows/UNC view: `\\wsl.localhost\Ubuntu\home\test\2026_aec_cptx_demo`

### Reading WSL files

Both `read_file` and `terminal` work with WSL UNC paths:

1. **read_file DOES NOT WORK for WSL UNC paths.** `read_file` with backslash UNC paths (`\\\\\\\\wsl.localhost\\\\Ubuntu\\\\...`) fails with "File not found" — 100% failure rate confirmed across 4 sessions (June 10, 11, 11, 11). **NEVER use `read_file` for WSL paths. Always use `terminal` with `cat`/`head`/`grep` and forward-slash UNC.** If you catch yourself writing `read_file` with `\\wsl.localhost`, STOP — it will fail.

2. **terminal (for reads AND writes):** Use forward-slash UNC paths with `cat`, `ls`, `grep`, `sed`, etc.:
   ```bash
   cat //wsl.localhost/Ubuntu/home/test/2026_aec_cptx_demo/README.md
   ls //wsl.localhost/Ubuntu/home/test/2026_aec_cptx_demo/
   ```

3. **write_file with WSL UNC paths is UNRELIABLE — SILENT DATA LOSS.** It reports full success (`bytes_written`, `dirs_created: true`, even `files_modified` with a path) but the file doesn't actually appear on disk. Confirmed multiple times (June 29 2026 — `write_file` returned success for session_state.md and 04_phase_furnishing_demo.md, but `ls` showed neither existed). This is NOT a rare edge case — it happens consistently enough that you MUST verify every WSL write with `ls -la` and always have the `wsl bash -c 'cat > ...'` fallback ready. **Preferred write method for WSL paths:**
   ```bash
   wsl bash -c 'cat > /home/test/2026_aec_cptx_demo/path/to/file.md << '"'"'EOF'"'"'
   file content here
   EOF'
   ```
   The nested quoting (`'"'"'EOF'"'"'`) is required to prevent heredoc variable expansion through MSYS. Always verify with `ls -la` after writing.
   - **Fallback:** Write to a Windows temp file with `write_file`, then copy into WSL:
     ```bash
     wsl -d Ubuntu -e bash -c "cp /mnt/c/Users/test/AppData/Local/Temp/myfile.md /home/test/2026_aec_cptx_demo/path/to/target.md"
     ```
   - **Directory creation in WSL:** `mkdir` on UNC paths may fail ("Read-only file system"). Use:
     ```bash
     wsl -d Ubuntu -e bash -c "mkdir -p /home/test/2026_aec_cptx_demo/path/to/dir"
     ```

4. **wsl.exe fallback:** `MSYS_NO_PATHCONV=1 wsl.exe -d Ubuntu -- sed -n '1,200p' /home/test/2026_aec_cptx_demo/README.md`. Heavier but works if MSYS UNC misbehaves.

See `references/rhino-mcp-wsl-file-reads.md` for MSYS path conversion quirks.

Key files:

- `hermes/DEMO_RULES.md` — audience-facing session flow and pacing rules for building site then massing.
- `system_prompts/00_session_startup.md` through `12_phase_layer_reveal.md` — phase-by-phase build script.
- `aa_demo_versions/cliff_house_02/user_prompts/project_prompt.md` — project brief for the modernist cliff house.
- `tools/layer_reveal_sequence_description.md` — layer reveal narrative: deconstruct massing, build structure, apply finish, reveal deck/pool.
- `tools/layer_reveal_sequence.cs` — Rhino layer reveal sequence implementation.
- `tools/obs_recorder.py` — recording/stage-file architecture.

The prior minimal recorded pass did not use these canonical story files. For the real full pass, read these via WSL and follow `DEMO_RULES.md`/phase prompts rather than inventing minimal geometry.
