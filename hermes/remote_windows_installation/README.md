# Remote Windows Hermes installation snapshot

This directory captures the Hermes installation from the AEC Windows demo host (`C:\Users\test\AppData\Local\hermes`) for repository continuity.

Secret hygiene exclusions:
- `.env`, `*.env`, `auth.json`, auth locks, credential/token/secret-named files
- live SQLite session/memory stores (`state.db*`) and request/session dumps
- logs, caches, sandboxes, pairing artifacts

Rebuildable/heavy dependency exclusions required for GitHub compatibility:
- Python virtual environments (`venv/`, `.venv*`)
- `node_modules/`
- embedded Git repositories (`.git/`)
- portable Git runtime (`git/`)

Sanitized config shape and environment key inventories are under `_sanitized/` with secret values redacted or omitted.
