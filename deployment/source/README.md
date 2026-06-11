# Captured remote Hermes + Daystrom DML source

This directory contains the source code captured from the working remote AEC demo server deployment.

## Source paths on the remote server

- Hermes Agent source:
  - `C:\Users\test\AppData\Local\hermes\hermes-agent`
- Daystrom DML integration source:
  - `C:\Users\test\AppData\Local\hermes\integrations\daystrom-dml`
- Active profile Daystrom plugin copy:
  - `C:\Users\test\AppData\Local\hermes\profiles\aec-cptx\plugins\daystrom_dml`

## Repo paths

```text
deployment/source/
├── hermes-agent/
├── integrations/daystrom-dml/
└── profiles/aec-cptx/plugins/daystrom_dml/
```

## Excluded from capture

The source snapshot intentionally excludes dependency/runtime/private state:

- `.git/`
- Python virtualenvs: `venv/`, `.venv/`, `.venv-dml/`
- JavaScript dependencies: `node_modules/`
- Python caches: `__pycache__/`, `.pytest_cache/`, `*.pyc`
- DML stores/runtime state: `stores/`
- logs, sessions, SQLite state, auth files, `.env`, provider credentials, model caches

## Why this exists

The live remote deployment included local patches to the Daystrom DML foreground wrapper path and the active Hermes Daystrom plugin behavior. This captured source tree preserves the working code state alongside the AEC demo prompts, profile, and launchers so the deployment can be audited or reconstructed from this private repository.

## Secret hygiene

This is a private repo, but do not add live secrets here. Keep provider API keys, OAuth tokens, OBS passwords, auth stores, and DML runtime data outside Git.
