# Portable deployment templates

This directory contains sanitized configuration and launch templates. It does
not contain a captured machine installation, dependency source trees, model
weights, credentials, sessions, logs, or DML runtime stores.

## Contents

```text
deployment/
├── aec-cptx-profile/       Sanitized primary Hermes profile
├── bac-teapot-profile/     Sanitized Teapot profile
├── windows-launchers/      Launchers using %LOCALAPPDATA% and relative paths
├── wsl-vllm/               Two-container local vLLM deployment
└── SOURCE_VERSIONS.md      External source provenance
```

Run the root preflight before using a launcher:

```bash
python scripts/aec_setup.py --check --tier agent
```

## Profile paths

Hermes profiles are expected under the platform's Hermes home. The Windows
templates derive this from `%LOCALAPPDATA%\hermes`; no username or hostname is
embedded. Set `AEC_DEMO_ROOT` to the repository checkout.

The two reference profiles use `memory.provider: daystrom_dml` with DCN mode
`active_read`. After creating or cloning any profile, verify the plugin files
and runtime rather than trusting config alone:

```bash
hermes -p aec-cptx memory status
hermes -p bac_teapot memory status
```

Hermes profile cloning does not necessarily copy `plugins/`. Install or copy
the Daystrom plugin into each profile through the supported DML installation
flow, then repeat the status check.

## WSL2 vLLM

`wsl-vllm/` runs the chat model on port 8000 and the vision model on port 8001.
Read `wsl-vllm/AGENTS.md`, provision once, and use its start/status/stop scripts.
The scripts do not depend on a particular Windows username or host.

The sanitized profile examples may describe either a remote OpenAI-compatible
provider or local vLLM. Select one deployment posture deliberately and update
the local, untracked profile config; do not assume an example URL represents
the active machine.

## Security and source ownership

Never commit live `.env`, auth files, provider keys, OBS passwords, `state.db`,
sessions, logs, caches, model data, DML stores, or full installations. Obtain
Hermes and DML from the sources recorded in `SOURCE_VERSIONS.md`.
