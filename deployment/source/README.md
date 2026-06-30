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
└── profiles/aec-cptx/
```

## Excluded from capture

The remote snapshot is intended to track the live installation state while keeping credentials out of Git. The 2026-06-30 refresh excluded:

- `.git/`
- Python virtualenvs: `venv/`, `.venv/`, `.venv-dml/`
- JavaScript dependencies: `node_modules/`
- live profile secrets/config: `.env`, `*.env`, `config.yaml`, `config.yaml.*`, private keys
- high-risk runtime transcript/state containers: `state.db`, `state.db-*`, `sessions/`, `logs/`, `.hermes_history`

DML runtime stores under `integrations/daystrom-dml/stores/` are included when they pass secret scanning and GitHub file-size limits, because the demo repo is now meant to preserve the remote DML posture as well as source code.

## Why this exists

The live remote deployment included local patches to the Daystrom DML foreground wrapper path and the active Hermes Daystrom plugin behavior. This captured source tree preserves the working code state alongside the AEC demo prompts, profile, and launchers so the deployment can be audited or reconstructed from this private repository.


## Best-code refresh

Refreshed on 2026-06-15 from the live remote AEC Hermes profile plus `mmckeen-nv/DML` main at `dbd3803` (`dbd3803c7513f74452280fd98c1b2fba824e5ea0`). This includes the corrected full-enabled DML default posture, first-class lattice placement metadata, summarizer preface cleanup, and Hermes gateway-wrapper hygiene so recent-channel preludes and injected `<memory-context>` / DPM scaffolding do not get stored as user memory.

Fresh remote verification on `2026-06-15` confirmed `memory.provider: daystrom_dml`, `retrieval_policy: always`, plugin status `available`, wrapper stripping active, and `hermes -p aec-cptx chat -q` returned `REMOTE_DML_PATCH_OK`.

## Remote live-state refresh

Refreshed again on 2026-06-30 from `DESKTOP-14FNBB2` after live remote Hermes changes. The capture hash for the sanitized remote bundle was:

```text
SHA256 8496bfd41daef5da0d5b2816ecb1b0ee08ca221ee9bbccab247d9f77492a71dc
```

Notable live-state facts at capture:

- Remote Hermes source had local modifications and unresolved website/package merge-conflict files; those are preserved here as part of the remote snapshot rather than silently reset.
- Remote profile model default remained `azure/anthropic/claude-opus-4-6` via the custom NVIDIA-compatible endpoint.
- Remote profile also carried NVIDIA GLM 5.2 as an available/vision model option: `nvidia/zai-org/glm-5.2`.
- Remote DML store health for `stores/aec-cptx-runtime-store` was `status: ok`, `record_count: 123`, `active_continuity_count: 23`, and checksum OK.

## Secret hygiene

This is a private repo, but do not add live secrets here. Keep provider API keys, OAuth tokens, OBS passwords, auth stores, live profile `config.yaml`, session DBs/logs, and credential-bearing files outside Git. DML runtime stores may be captured only after secret scanning and file-size checks.
