# DML success and failure learning contract

Daystrom must remember how an operation behaved, not merely that a phase ended.
The unit of learning is one consequential attempt: an export, import, geometry
build, scene mutation, asset import, render, or ComfyUI workflow execution.

## Before an attempt

1. Construct an `approach_signature` from the phase, application, operation,
   format/tool, script or command name, unit policy, and important options.
2. Call `mcp_daystrom_dml_query` with the project identity, phase, operation,
   approach signature, expected gate, relevant error text, and the words
   `success failure avoidance fix`.
3. Cite applicable retrieved successes and failures. Call `mcp_cma_augment` with
   those records and the proposed approach.
4. If the same signature is recorded as failed against the same gate, do not run
   it again. Use a materially different method or stop with the blocker.

## After an attempt

Validate through the owning application before interpreting the result. Record
objective evidence such as counts, names, dimensions, topology statistics,
artifact paths, checksums, screenshots, and exact errors. A script that changed
state before failing is `FAILURE_PARTIAL_MUTATION`; inspect the current state
before any retry.

Write one UTF-8 Markdown file under `work/dml_events/` using this shape:

```text
# DML attempt event
event_id: <project>-<phase>-<UTC timestamp>-<short operation>
project: vp-studio-01
phase: <preflight|rhino|rhino-to-blender|blender|comfyui>
application: <Rhino|Blender|ComfyUI|pipeline>
operation: <stable operation name>
approach_signature: <stable, searchable signature>
outcome: <SUCCESS_VALIDATED|FAILURE_VALIDATED|FAILURE_PARTIAL_MUTATION>
validation_status: <PASSED|FAILED>
artifact_path: <absolute path or NONE>
source_provenance: <tool/script/source record>
expected_gate: <objective expectation>
observed_evidence: <objective result>
error: <exact error or NONE>
root_cause: <known cause or UNKNOWN>
avoidance_rule: <what must not be repeated, or NONE>
reusable_recipe: <validated steps, or NONE>
next_safe_action: <changed approach or STOP>
timestamp_utc: <ISO-8601>
```

Call `mcp_daystrom_dml_ingest` on that text file and require `files >= 1`. If the
record cannot be ingested, do not claim learning, do not retry a destructive
operation, and do not advance the phase.

## Promotion rules

- `SUCCESS_VALIDATED`: ingest into DML, then `mcp_cma_reinforce` the reusable
  recipe and its validation evidence.
- `FAILURE_VALIDATED`: ingest into DML; never reinforce it into CMA.
- `FAILURE_PARTIAL_MUTATION`: ingest into DML; never reinforce; inspect and either
  restore from the validated source or stop.
- Never ingest `.3dm`, `.blend`, image, or other binary files as the learning
  record. Refer to them from the Markdown event.
- Never label an attempt successful because a tool returned without throwing.
  The acceptance gate must pass.

## Retry and iteration policy

Additional iterations exist to test a changed hypothesis. Before granting or
using them, the latest failure record must have been ingested, retrieved, and
included in CMA augmentation. Two failures with the same approach signature and
gate are a hard stop. Camera, lighting, materials, normals, or render changes are
not valid recovery actions for failed topology, units, object identity, or import
gates.
