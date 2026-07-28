# External source provenance

This repository intentionally does not vendor complete Hermes Agent or Daystrom
DML installations. Those snapshots previously duplicated thousands of files,
included generated runtime state, and made dependency and security ownership
ambiguous.

Reconstruct deployments from the upstream repositories and the sanitized
profile/configuration files kept under `deployment/`.

| Component | Source | Reference captured by this demo |
|---|---|---|
| Hermes Agent | https://github.com/NousResearch/hermes-agent | Use a current tagged release compatible with the profile schema |
| Daystrom DML | https://github.com/mmckeen-nv/DML | `dbd3803c7513f74452280fd98c1b2fba824e5ea0` |

The old Windows installation and DML runtime-store snapshots are deliberately
excluded. Runtime stores may contain session-specific context and must be
backed up outside Git only when explicitly required.

`deployment/daystrom-dml/aec-agent-memory.patch` is applied idempotently by the
Windows installer to the recorded Daystrom revision. It contains the verified
low-latency MCP preload, compact recall, cross-session procedural-memory,
RAG-separation, and bounded iteration-extension fixes used by this demo.
