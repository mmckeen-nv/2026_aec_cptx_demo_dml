# Daystrom memory guidance

Daystrom DML is the memory harness behind the demo. It supplies compact prior
experience to the model; it does not control the modeling loop, impose a tool
sequence, or decide whether the agent may continue.

## During work

- Let automatic active-read provide normal continuity.
- Query DML when a prior success, failure, tool recipe, or resumed-session state
  can shorten the current plan.
- Use CMA augmentation when critique would improve a consequential plan. It is
  optional for routine geometry and scene edits.
- Never require stats, query, augmentation, ingestion, or reinforcement between
  ordinary MCP calls.
- Do not repeat an unchanged approach that memory identifies as a matching
  failure. Inspect current application state and change the hypothesis.

## What to remember

After a meaningful validated success or real failure, write and ingest one
compact Markdown record. Include:

- project and phase;
- intent and approach;
- important objects or scene state changed;
- objective evidence and artifact paths;
- outcome and exact error, if any;
- the reusable recipe or avoidance lesson;
- the next safe action.

One phase record is normally enough. Do not ingest raw transcripts, full object
listings, binary files, or a record for every successful tool call. Reinforce
only a success that was validated in the owning application and, when visual
quality matters, reviewed through vision. Failures remain retrieval knowledge
and are never reinforced as preferred behavior.

Extra iterations are advisory. DML/CMA/DCN may suggest that more work is useful,
but Hermes remains responsible for deciding whether a targeted correction is
making progress. A failed vision service or memory service must be reported; it
must not create an infinite retry loop or discard a geometrically valid scene.
