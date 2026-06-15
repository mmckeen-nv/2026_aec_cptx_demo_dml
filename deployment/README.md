# Remote AEC CPTX deployment snapshot

This directory captures the working remote deployment posture from the Windows AEC demo server.

## Verified remote

- Host: `DESKTOP-14FNBB2`
- Windows user: `test`
- Hermes profile: `aec-cptx`
- Profile path: `C:\Users\test\AppData\Local\hermes\profiles\aec-cptx`
- Desktop path: `C:\Users\test\Desktop`

## What is included

```text
deployment/
├── aec-cptx-profile/
│   ├── AGENTS.md
│   ├── SOUL.md                  # redacted; no live OBS password
│   ├── profile.yaml
│   ├── config.example.yaml      # sanitized excerpt, not live config
│   └── Start-Hermes-AEC-Rhino-DML.ps1
├── source/
│   ├── hermes-agent/            # captured Hermes source, no venv/node_modules/.git
│   ├── integrations/daystrom-dml/
│   └── profiles/aec-cptx/plugins/daystrom_dml/
└── windows-launchers/
    ├── Hermes-AEC-CPTX.bat
    └── START_HERMES_AEC_CPTX.cmd
```

## Repository privacy

This repository was changed to private before adding the captured Hermes/DML source snapshot.

## What is intentionally excluded

Do not commit or copy these from the live server:

- `.env`
- `auth.json` or OAuth/token stores
- live `config.yaml` with provider API keys
- `state.db`
- `sessions/`, `logs/`, `home/`, `cron/`
- DML runtime stores, caches, lock files, model caches, or Ollama data
- `.lnk` files; recreate them locally if needed because they are machine-specific Windows shell artifacts


## Best-code refresh

Deployment source was refreshed on 2026-06-15 from the live remote AEC Hermes profile plus `mmckeen-nv/DML` main at `dbd3803` (`dbd3803c7513f74452280fd98c1b2fba824e5ea0`). The repository snapshot now includes first-class DML lattice placement metadata, summarizer preface cleanup, and gateway-wrapper hygiene for Discord/Hermes payloads while keeping the corrected default posture: DML runtime features are enabled by default because they work; opt-outs are explicit and should only be used for constrained, evidence-backed paths.

## Launcher behavior

The verified manual launcher is:

```cmd
C:\Users\test\Desktop\START_HERMES_AEC_CPTX.cmd
```

It calls:

```cmd
C:\Users\test\Desktop\Hermes AEC CPTX.bat
```

The batch file starts:

```cmd
%LOCALAPPDATA%\hermes\hermes-agent\venv\Scripts\hermes.exe -p aec-cptx
```

from:

```cmd
%LOCALAPPDATA%\hermes\profiles\aec-cptx
```

This was verified via an interactive TTY and reached:

```text
aec-cptx ❯
```

## DML posture

The live profile was verified with:

```yaml
memory:
  provider: daystrom_dml
  daystrom_dml:
    retrieval_policy: always
    timeout_seconds: 8
    dcn:
      mode: active_read
sessions:
  write_json_snapshots: true
```

`AGENTS.md` reinforces that DML should be treated as the continuity spine and that degraded DML/Ollama should be reported explicitly rather than silently behaving stateless.

Runtime fix verified on `2026-06-11`/`2026-06-12`: the active `daystrom_dml` plugin now treats Windows `.cmd` launchers as available even when POSIX `os.access(..., X_OK)` returns false, and the profile uses valid DCN mode `active_read` instead of invalid `active_write`. Fresh smoke session `20260611_235216_a1dc22` logged:

```text
Memory provider 'daystrom_dml' registered
Memory provider 'daystrom_dml' activated
Daystrom DCN active-read ... "decision": "retrieve" ... "retrieve_dml": true ... "reason_codes": ["configured_always", "retrieve_dml"]
```

No fresh `Memory provider 'daystrom_dml' loaded but no provider instance found`, health-timeout, auxiliary-provider, or compression/memory-flush warnings were present after that smoke.

Runtime refresh verified on `2026-06-15` after syncing the latest DML/Hermes profile code to the remote server:

```text
HAS_RECENT_STRIP True
POLICY_DEFAULT always
STRIPPED [Mark_NV] real request
Status: available ✓
retrieval_policy: always
REMOTE_DML_PATCH_OK
```

## Auxiliary summarization/compression posture

The earlier remote logs showed auxiliary auto-detect warnings:

```text
Compression, summarization, and memory flush will not work.
```

That warning meant DML retrieval could be configured correctly while Hermes side-task LLM paths were still degraded. This is now resolved in the live `aec-cptx` profile by explicitly pinning auxiliary tasks to the same working custom NVIDIA-compatible endpoint/model as the main chat model:

```yaml
compression:
  enabled: true
  threshold: 0.85

auxiliary:
  compression:
    provider: custom
    model: azure/anthropic/claude-opus-4-6
    context_length: 200000
  title_generation:
    provider: custom
    model: azure/anthropic/claude-opus-4-6
  web_extract:
    provider: custom
    model: azure/anthropic/claude-opus-4-6
  goal_judge:
    provider: custom
    model: azure/anthropic/claude-opus-4-6
```

Additional aux task blocks (`approval`, `mcp`, `skills_hub`, `profile_describer`, `triage_specifier`, `kanban_decomposer`, `curator`, `tts_audio_tags`) are also pinned to `provider: custom` / `model: azure/anthropic/claude-opus-4-6` in the sanitized config example.

Verification run on `2026-06-11`:

```text
compression.threshold 0.85
resolved compression True azure/anthropic/claude-opus-4-6 https://inference-api.nvidia.com/v1/
resolved title_generation True azure/anthropic/claude-opus-4-6 https://inference-api.nvidia.com/v1/
resolved web_extract True azure/anthropic/claude-opus-4-6 https://inference-api.nvidia.com/v1/
resolved goal_judge True azure/anthropic/claude-opus-4-6 https://inference-api.nvidia.com/v1/
AUX_RESOLVE_OK
session_id: 20260611_212123_572fed
AUXOK
RECENT_AUX_WARNINGS_AFTER_SMOKE=
```

`RECENT_AUX_WARNINGS_AFTER_SMOKE=` was empty, meaning no fresh `Auxiliary auto-detect: no provider available` / `Compression, summarization, and memory flush will not work` warnings were emitted by the smoke run.
