# Rhino 8 DML retrieval policy

status: ACTIVE
retrieval_tags: DML Rhino docs query before tool call stop retry loop

Before authoring any Rhino script, query Daystrom DML as procedural tool
history. For geometry work, ask:

`Have I made successful Rhino geometry tool calls before? How exactly did I do
that? Return the exact tool name, argument shape, validated script scaffold,
and verified result. Exclude failed attempts.`

For inspection or capture, use:

`Rhino Python MCP read only inspection capture payload error traceback`

Read the returned context before composing the tool call. Prefer prior verified
tool calls over general documentation. Do not ask DML a generic project
question, and do not rely on a generic session-start recall for API signatures.

After each Rhino call, inspect the nested result:

- Empty `payload.error` plus expected stdout/evidence: continue.
- Non-empty `payload.error`, exception, or traceback: the call failed.
- The same failure twice: stop and report it; do not keep improvising.

Never grant or request iteration extension merely because the MCP transport
completed. Progress requires verified geometry, a changed object count, a
validated bounding box, or another explicit artifact.
