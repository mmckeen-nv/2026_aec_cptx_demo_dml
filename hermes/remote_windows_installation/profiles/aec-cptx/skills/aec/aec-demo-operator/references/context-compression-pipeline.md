# Context Compression Pipeline — AEC CPTX

Established June 2026 after a session that consumed 22% of context
on startup file reads alone.

## Problem

The original startup sequence read 6 files in full (~40KB) before the
user's first action. Each phase then loaded another 4–18KB phase prompt.
Two phases into a session = 60–80KB of raw text in context, leaving
little room for actual tool calling and reasoning.

## Solution: DML-first everything

DML (Daystrom Memory Layer) has all project files ingested in compressed
form. The agent should never bulk-read files into context.

### File inventory and sizes

Phase prompts (system_prompts/):
  00_session_startup.md (DML-aware): 9KB
  00_session_startup_backup.md (original): 9KB
  01_phase_config.md: 7KB
  02_phase_site_prep.md: 5KB
  03_phase_massing.md: 4KB
  04_phase_floorplan_2d.md: 14KB
  05_phase_floorplan_3d.md: 18KB
  06_phase_detailing.md: 4KB
  07_phase_export_blender.md: 14KB
  08_phase_lighting_camera.md: 12KB
  09_phase_materials.md: 11KB
  10_phase_test_render.md: 4KB
  11_phase_final_render.md: 6KB
  12_phase_layer_reveal.md: 1KB
  13_phase_sun_study.md: 10KB
  APPENDIX_materials.md: 7KB
  APPENDIX_pitfalls.md: 3KB
  APPENDIX_segmentation.md: 3KB
  Total: ~152KB

Skills (skills/):
  INDEX.md: 7KB
  session_state.md: 2KB
  depth_and_segmentation.md: 10KB
  rhino_modeling.md: 8KB
  architectural_pipeline.md: 5KB
  obs_recording.md: 5KB
  rhino_prep.md: 5KB
  retaining_wall_footing.md: 6KB
  import_with_metadata.py: 5KB
  audit_active_document.py: 6KB
  derive_geometry.py: 3KB
  coplanar_detector.py: 3KB
  pre_export_validate.py: 3KB
  validate_blender_scene.py: 3KB
  VISUAL_ENGAGEMENT_RULE.md: 1KB
  BACKUP_RULE.md: 1KB
  Total: ~73KB

Project prompt: ~15KB
Grand total: ~240KB of reference material

### Retrieval hierarchy (all file types)

1. DML recall (free — already compressed in memory)
2. Targeted grep (tiny — just the lines needed)
3. head -40 (small — only if DML is blank on a whole phase)
4. Full file read NEVER (unless editing the file itself)

### Compression config

compression.target_ratio = 0.85 (not default 0.50)
Set via: hermes config set compression.target_ratio 0.85 --profile aec-cptx

### Startup file locations

- Active: system_prompts/00_session_startup.md (DML-aware, ~9KB)
- Backup: system_prompts/00_session_startup_backup.md (original bulk-read, 9KB)
- Auto-fallback to backup when DML is degraded or unavailable.

### WSL write pitfall

write_file does NOT reliably write to WSL UNC paths — it silently
writes to a different local path. Use terminal heredoc/cat for all
WSL filesystem writes.

## DML Agentic Learning Pipeline

Enabled June 2026 to make tool calls faster every session.

### What it does

DCN (Daystrom Cognition Network) in active_write mode with procedural
learning tracks:
- Tool call sequences that succeed (MCP commands, parameter patterns)
- Phase execution workflows (which tools, in what order, with what args)
- Error recovery patterns (what failed, what fixed it)
- Context budget adjustments (what queries needed more/less recall)

Over time, DML builds procedural profiles ("cookbooks") for recurring
task types. The agent recalls these instead of re-reading files.

### The learning loop

1. DML recalls relevant tool sequences for the current task type
2. Agent executes (using recalled patterns or discovering new ones)
3. DML ingests tool calls + outcomes as agentic memory items
4. Successful patterns promoted from scratch to durable storage
5. Next run for the same task type recalls the proven pattern

### Config: Hermes side (config.yaml)

```yaml
memory:
  daystrom_dml:
    dcn:
      mode: active_write          # was active_read — enables procedural learning
    top_k: 8                      # was 4 — more recall for richer cookbooks
    max_context_chars: 5000       # was 3500 — room for agentic patterns
    retrieval_policy: always
compression:
  target_ratio: 0.85              # was 0.50 — preserve more context during compaction
```

### Config: DML side (aec-cptx-portable.yaml)

```yaml
agentic_mode:
  enabled: true                   # was missing/false — activates agentic memory pipeline
  schema_validation: true
  promotion_pipeline: true        # scratch → verified → durable promotion
  scratch_to_durable_threshold: 0.7
dpm:
  mode: active-write              # preference graph (already was active-write)
```

### Key DML source modules (for debugging)

- agent_schema.py: MemoryKind (action/observation/plan/error), MemoryPhase, MemoryOutcome
- cognition/policy.py: DeterministicCognitionPolicy — rules-first DCN routing
- cognition/learning.py: ProceduralLearningPolicy — versioned, reversible overlay
  - ALLOWED_FIELDS: retrieval_query_template, memory_mode_preference,
    verification_requirement, tool_recommendation, context_budget_adjustment,
    writeback_strictness
  - FORBIDDEN_FIELDS: identity, persona, values, safety, permissions, secrets
  - apply_to_plan(): overlays learned profiles onto DCN cognition plans
- promotion_pipeline.py: ScratchStore → verified → durable memory promotion
- dml_adapter.py: ingest_agentic() — ingests tool calls with agentic metadata

### Expected behavior over time

Session 1: No cookbooks. Agent reads files, discovers patterns.
Session 2: DML recalls session 1 patterns. Agent refines.
Session 3+: Proven patterns promoted to durable. Agent executes from recall.
Session N: Repeated task types (site_prep, massing, export, render)
           should approach near-instant execution — DML surfaces the
           exact MCP command sequence with parameters.
