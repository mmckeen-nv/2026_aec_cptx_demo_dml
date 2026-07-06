# Daystrom Platform Smoke Test Procedure

Full-platform health verification covering all four Daystrom subsystems: DML (Memory Lattice), DCN (Cognition Network), DPM (Personality Matrix), and CMA (Compressed Memory Archive).

## Prerequisites

- Ollama running on localhost:11434 with models: qwen3-embedding:0.6b, llama3:8b
- DML venv at: `C:/Users/test/AppData/Local/hermes/integrations/daystrom-dml/.venv-dml`
- DML store at: `C:/Users/test/AppData/Local/hermes/integrations/daystrom-dml/stores/aec-cptx-runtime-store`
- DML config at: `C:/Users/test/AppData/Local/hermes/integrations/daystrom-dml/config/aec-cptx-portable.yaml`

## Two CLI entry points

### 1. hermes-dml-memory.cmd (wrapper script — no provider server needed)

Path: `C:/Users/test/AppData/Local/hermes/integrations/daystrom-dml/bin/hermes-dml-memory.cmd`

Bash alias:
```bash
DML="/c/Users/test/AppData/Local/hermes/integrations/daystrom-dml/bin/hermes-dml-memory.cmd"
```

Commands: `health`, `verify`, `report`, `retrieve`, `ingest`, `backend-proof`, `audit-tail`, `backup`, `schema`, `export`, `verify-export`, `import`, `conflicts`, `resolve-conflict`, `curate`, `migration-status`, `migrate-embeddings`, `session`, `handoff`, `resume`

**⛔ The command is `health`, NOT `status`.** `status` is not a valid subcommand for the wrapper script (it's only valid for `dml.exe` provider CLI). Using `hermes-dml-memory.cmd status` returns `error: invalid choice: 'status'`.

### 2. dml.exe (provider CLI — needs provider server for most commands)

Path: `C:/Users/test/AppData/Local/hermes/integrations/daystrom-dml/.venv-dml/Scripts/dml.exe`

Commands: `serve`, `status`, `dcn`, `remember`, `recall`, `resume`, `search`, `fetch`

DCN subcommands: `observe`, `packet`, `eval-smoke` (alias: `readiness`), `policy show/export/import/checkpoint/checkpoints/rollback`, `feedback`, `audit-tail`, `promotions`, `promote`, `seed-propose`, `seed-trial`, `seed-loop`

## Smoke test sequence

### Phase 1: Infrastructure (no server needed)

```bash
DML="/c/Users/test/AppData/Local/hermes/integrations/daystrom-dml/bin/hermes-dml-memory.cmd"

# Ollama alive
curl -s http://localhost:11434/api/tags | python -m json.tool

# DML core health
"$DML" health          # checksum, record count, errors, latency
"$DML" verify          # full state verification
"$DML" report          # conflicts, curation candidates, schema version
"$DML" backend-proof   # embedder + LLM backend readiness
"$DML" migration-status  # embedding dimension migration state
"$DML" audit-tail --limit 5  # recent audit events
```

**What to check:**
- `status: ok` on all commands
- `checksum_ok: true` and `count_ok: true` in verify
- `embedder_ready: true` in backend-proof
- `conflicts.count: 0` in report
- `mismatched: 0` and `failed: 0` in migration-status

### Phase 2: DML retrieval (no server needed)

```bash
"$DML" retrieve --query "cliff house architectural design" --top-k 3
```

**What to check:**
- Returns items with relevant summaries
- `memory_confidence` above threshold (currently 0.46)
- `ground_truth_triggered: false` (confidence OK)
- `embedding_model: ollama:qwen3-embedding:0.6b`
- Latency ~2000-3000ms (first call; subsequent faster)

### Phase 3: Provider server + DCN + DPM (needs server)

Start the provider:
```bash
DMLEXE="/c/Users/test/AppData/Local/hermes/integrations/daystrom-dml/.venv-dml/Scripts/dml.exe"
DML_DIR="/c/Users/test/AppData/Local/hermes/integrations/daystrom-dml"

# Start in background
"$DMLEXE" serve \
  --storage-dir "$DML_DIR/stores/aec-cptx-runtime-store" \
  --config-path "$DML_DIR/config/aec-cptx-portable.yaml" &

# Wait 10-15s for startup, then verify
sleep 15
"$DMLEXE" status
```

**Setup pitfall:** `uvicorn` may not be installed in the venv. If `serve` fails with `ModuleNotFoundError: No module named 'uvicorn'`, install it:
```bash
"$DML_DIR/.venv-dml/Scripts/python.exe" -c \
  "import subprocess; subprocess.run(['$DML_DIR/.venv-dml/Scripts/pip.exe', 'install', 'uvicorn'])"
```
(The terminal tool may reject bare `pip install uvicorn` as a long-lived process — use the subprocess wrapper.)

#### DCN tests:
```bash
# Intent classification + plan generation
"$DMLEXE" dcn observe --text "What rendering approach works best for the cliff house?"

# Full cognitive packet assembly
"$DMLEXE" dcn packet --text "What rendering approach works best for the cliff house?"

# Eval smoke: 9 fixture cases covering all task types, retrieval modes, risk levels
"$DMLEXE" dcn eval-smoke

# Policy inspection
"$DMLEXE" dcn policy show

# Audit/promotion history
"$DMLEXE" dcn audit-tail --limit 5
"$DMLEXE" dcn promotions --limit 5
```

**What to check (DCN):**
- `eval-smoke`: 9/9 cases passed, 15/15 readiness gates passed, 0 violations
- Pollution score: 0.0 across all cases
- Precision@k and recall@k: 1.0 average
- Redaction policy: all false (no leaks)
- Policy version: `dcn-policy-v0`, mode: `deterministic_v0`
- Coverage spans: 6 task types, 4 retrieval modes, 3 writeback modes, 2 risk levels, 12 reason codes

#### DPM tests:
```bash
# Resume/continuity retrieval
"$DMLEXE" resume --session-id "smoke-test-session"

# Semantic search through provider
"$DMLEXE" search --query "personality preferences design style" --top-k 3
```

DPM Python API test (preference pattern detection):
```python
# Run via: "$DML_DIR/.venv-dml/Scripts/python.exe" -c "..."
import sys; sys.path.insert(0, '<DML_DIR>/source/dml_core')
from daystrom_dml.personality_matrix import PersonalityMatrix, PREFERENCE_PATTERNS

test_inputs = [
    'I prefer using depth maps',        # MATCH
    'Please use flowing organic forms',  # MATCH
    'Always save checkpoints',           # MATCH
    "Don't use revolution surfaces",     # MATCH
    'Just run the next phase',           # NO MATCH (correct)
]
for text in test_inputs:
    matched = any(pat.search(text) for pat in PREFERENCE_PATTERNS)
    print(f"[{'MATCH' if matched else 'NO MATCH'}] {text}")
```

**What to check (DPM):**
- Config: `enabled=true`, `mode=active-write`, `active=true`, `write_enabled=true`
- Scoping: `relationship:mark-aec-cptx`, `project:cliff-house-02`
- Pattern detection: 4/5 match, 1/5 correctly rejected
- Preference graph: may be `None` if no DPM-active sessions have run yet (expected)

### Phase 4: Round-trip canary (write + read through provider)

```bash
"$DMLEXE" remember --text "DML smoke test canary: ran $(date -u +%Y-%m-%dT%H:%M:%SZ)" --kind observation
"$DMLEXE" search --query "smoke test canary" --top-k 1
```

**What to check:**
- Record count increments by 1
- Search returns the canary with matching snippet

### Phase 5: CMA (no server needed)

CMA has its own Python adapter — test directly:
```python
import sys, json, tempfile, os; sys.path.insert(0, '<DML_DIR>/source/dml_core')
from cma.adapter import CMAAdapter; from pathlib import Path

tmp = tempfile.mktemp(suffix='.json')
Path(tmp).write_text('[]')
adapter = CMAAdapter(storage_path=Path(tmp))
adapter.ingest('Test memory item one')
adapter.ingest('Test memory item two')
preamble = adapter.augment_prompt('Query text', top_k=2)
print(preamble)  # Should show "=== Concept Memory ===" block
store = json.loads(Path(tmp).read_text())
print(f'{len(store)} items')  # Should be 2
os.remove(tmp)
```

### Cleanup

Kill the provider server after testing (it's not needed for normal DML wrapper operations).

## DPM config reference (from aec-cptx-portable.yaml)

```yaml
dpm:
  enable: true
  mode: active-write           # active-read | active-write | observe-only | disabled
  preference_graph_path: ./dpm_preference_graph.json
  relationship_id: relationship:mark-aec-cptx
  project_id: project:cliff-house-02
  token_budget: 80
```

## DCN capabilities (from policy show)

12 capabilities: observe, plan_context, cognitive_packet, feedback, policy_export, policy_import, policy_checkpoints, policy_checkpoint, policy_rollback, mode_promote, promotion_audit, eval_smoke

Writeback forbidden classes: raw_transcript, tool_log, secret, prompt_scaffold

## Resolved: DML ingest persistence gap (2026-06-29, fixed same day)

The wrapper script (`hermes-dml-memory.cmd ingest`) was reporting `chunks_ingested > 0` and writing audit events, but the state file (`dml_state.jsonl`) was not growing. **This bug was fixed on 2026-06-29.**

**Root cause (confirmed):** `adapter.ingest(chunk, persist=False)` was adding items to an internal processing path (embedding, summarization, lattice placement) but NOT to `self.store` — the in-memory store that `items()` iterates over. When `_persist_all()` ran afterward, it serialized `self.store.items()` which returned only the pre-loaded set, effectively writing the same data back.

**How to detect if it recurs:**
- Dedup index (`.ingest_dedup_sha256.txt`) line count exceeds state file line count
- `wc -l` on state file doesn't change after an ingest reporting `chunks_ingested > 0`
- State file timestamp updates but size/line count stays the same

**Recovery from a past persistence failure:**
If data was ingested during the bug period (dedup hashes exist but records don't):
1. Trim the dedup index back to match the state record count: `head -N .ingest_dedup_sha256.txt > trimmed.txt && mv trimmed.txt .ingest_dedup_sha256.txt`
2. Re-ingest the lost content with `--no-filter-noise`
3. Verify with `wc -l` before/after

**Post-fix verification procedure (use after any critical ingest):**
```bash
echo "BEFORE:"; wc -l "$DML_DIR/stores/aec-cptx-runtime-store/dml_state.jsonl"
"$DML" ingest --kind phase-outcome --no-filter-noise --text "..."
echo "AFTER:"; wc -l "$DML_DIR/stores/aec-cptx-runtime-store/dml_state.jsonl"
# Line count should increase by number of chunks_ingested + 0 (header is line 1)
```

## Store stats reference (as of 2026-06-29, post-fix)

- Records: 94 (61 aec-cptx, 33 openclaw)
- Active continuity: 19 (all aec-cptx)
- Quarantined: 0
- Summary ratio: 1.0 (all records have summaries)
- Embedding dims: 1024
- Audit events: 172+
- Dedup index: present and synced
- Health latency: ~35ms
