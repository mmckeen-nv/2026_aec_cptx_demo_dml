---
project: vp-studio-01
memory_class: failure_event
phase: rhino
outcome: FAILURE_VALIDATED
source: observed local-Qwen run on 2026-07-15
validation: agent log showed 110 calls without a checkpoint, repeated local script patch/replay, one-object mutation churn, and an external GLM compaction attempt
---

# Qwen VP execution-rail failure and recovery

The geometry model was capable of recognizable VP Studio components, but the
run failed operationally because contradictory guidance encouraged one object
per call, local Python/C# file creation and replay, and auxiliary requests to an
external model. This consumed context without producing phase checkpoints.

For VP Studio 01, keep every reasoning and compression request on local Qwen at
`http://localhost:8000/v1`; use local Nemotron only for viewport vision. Execute
geometry only through inline `mcp_rhino_run_csharp(script=...)`, copying the
current phase's tested `Func<>`/`Action<>` scaffold. Python is read-only
inspection/capture through `mcp_rhino_run_python`. Never launch a language
interpreter, Rhino editor, desktop file association, or external script replay.

Read the locked scene manifest before geometry. Create one coherent scheduled
assembly per mutation, using a few coherent assembly mutations and targeted
corrections per phase without a hard turn limit. Then
run one numeric manifest validator. Only the literal
`NUMERIC_PASS` permits a fresh viewport and local vision review. Make targeted
corrections, revalidate, and save one checkpoint. After context rotation,
rehydrate from the compact project state plus DML and inspect Rhino before the
next mutation.

DML is advisory memory: retrieve useful prior evidence and record meaningful
validated successes or failures. It must not force ordinary tool turns or
replace the manifest.
