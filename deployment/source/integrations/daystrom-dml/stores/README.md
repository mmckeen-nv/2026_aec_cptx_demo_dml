# Daystrom DML transport stores

This directory carries portable Daystrom DML memory-store snapshots for the AEC demo bundle.

## `hermes-runtime-store/`

Snapshot source:

```text
/Users/markmckeen/.hermes/hermes-agent/integrations/daystrom-dml/stores/hermes-runtime-store
```

Purpose:

- Transport the Citizen Snips / Hermes Daystrom DML memory state with the demo repository.
- Preserve the active DML state, RAG index metadata, personality/evolution graphs, audit trail, and historical store backup files that were present in the source store at capture time.
- Exclude only high-confidence secrets/credentials if they are detected during capture. The committed snapshot was scanned before commit and no high-confidence credential patterns were found.

Validation command used from `deployment/source/integrations/daystrom-dml/source`:

```bash
PYTHONPATH="$PWD/dml_core:$PWD" \
  python openclaw-wrapper/scripts/dml_memory.py \
  --storage-dir ../stores/hermes-runtime-store \
  --no-require-gpu health
```

Expected active-state shape at capture:

- DML contract: `dml-agent-memory-v1`
- `dml_state.jsonl` records: 99
- active continuity records: 57
- audit events: 303
- embedding dimensions: 1024
