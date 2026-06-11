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
└── windows-launchers/
    ├── Hermes-AEC-CPTX.bat
    └── START_HERMES_AEC_CPTX.cmd
```

## What is intentionally excluded

Do not commit or copy these from the live server:

- `.env`
- `auth.json` or OAuth/token stores
- live `config.yaml` with provider API keys
- `state.db`
- `sessions/`, `logs/`, `home/`, `cron/`
- DML runtime stores, caches, lock files, model caches, or Ollama data
- `.lnk` files; recreate them locally if needed because they are machine-specific Windows shell artifacts

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
sessions:
  write_json_snapshots: true
```

`AGENTS.md` reinforces that DML should be treated as the continuity spine and that degraded DML/Ollama should be reported explicitly rather than silently behaving stateless.

## Known caveat

Remote logs showed auxiliary auto-detect warnings:

```text
Compression, summarization, and memory flush will not work.
```

That means DML retrieval can be configured correctly while compression/summarization/memory-flush paths are still degraded until an auxiliary provider or local summarization model is configured.
