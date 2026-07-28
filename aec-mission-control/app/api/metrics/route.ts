import path from "node:path";
import { promises as fs } from "node:fs";
import { LOG_DIR, residentAgentState, tailLines, VISUAL_EPOCH_FILE } from "@/lib/local-aec";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const BUCKET_SECONDS = 1;
const POINT_COUNT = 20;
const CONTROLLER_LOG = path.join(LOG_DIR, "aec_demo_controller.jsonl");

function timestamp(line: string) {
  const structured = line.match(/"timestamp"\s*:\s*"([^"]+)"/);
  if (structured) {
    const parsed = Date.parse(structured[1]);
    if (Number.isFinite(parsed)) return parsed;
  }
  const match = line.match(/^(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2}:\d{2})(?:,(\d{3}))?/);
  if (!match) return 0;
  return new Date(`${match[1]}T${match[2]}.${match[3] ?? "000"}`).getTime();
}

export async function GET() {
  const [resident, rawLines, rawControllerLines, resetAt] = await Promise.all([
    residentAgentState(),
    // A single automatic run may contain a resident coordinator plus a nested
    // legacy worker. Keep enough of the local log to account for both streams.
    tailLines(path.join(LOG_DIR, "agent.log"), 3_000_000),
    // The controller records every attempted operation before execution,
    // including blocked and hanging calls that never emit a completion line.
    tailLines(CONTROLLER_LOG, 3_000_000),
    fs.readFile(VISUAL_EPOCH_FILE, "utf8")
      .then((value) => new Date((JSON.parse(value) as { started_at?: string }).started_at ?? 0).getTime())
      .catch(() => 0),
  ]);
  // A scene reset is also the operator's telemetry epoch. This keeps retries,
  // calls, and DML totals from leaking in from the previous run. Do not filter
  // by the resident session ID: MCP/model work from child sessions is still
  // part of the operator's run and must be counted.
  const lines = resetAt
    ? rawLines.filter((line) => timestamp(line) >= resetAt)
    : rawLines;
  const controllerLines = resetAt
    ? rawControllerLines.filter((line) => timestamp(line) >= resetAt)
    : rawControllerLines;
  const now = Date.now();
  const bucketMs = BUCKET_SECONDS * 1000;
  const firstBucket = Math.floor(now / bucketMs) * bucketMs - ((POINT_COUNT - 1) * bucketMs);
  const buckets = Array.from({ length: POINT_COUNT }, (_, index) => ({
    at: firstBucket + (index * bucketMs),
    generatedTokens: 0,
    toolCalls: 0,
    retries: 0,
  }));

  let latestTps = 0;
  let latestTpsAt = 0;
  let tokensGenerated = 0;
  let modelCalls = 0;
  let retryTotal = 0;
  let toolCallTotal = 0;
  let dmlCalls = 0;
  let memoryRecalls = 0;
  let memoriesAccessed = 0;
  let memoryStores = 0;
  let lastRecallAt = 0;
  let lastStoreAt = 0;
  const controllerAttempts = controllerLines.filter((line) =>
    /"event"\s*:\s*"(?:allowed|blocked)"/i.test(line)
  );
  const hasControllerAttempts = controllerAttempts.length > 0;
  const allowedSignatures = new Set(
    controllerLines
      .filter((line) => /"event"\s*:\s*"allowed"/i.test(line))
      .map((line) => line.match(/"signature"\s*:\s*"([^"]+)"/i)?.[1])
      .filter((value): value is string => Boolean(value)),
  );

  for (const line of controllerLines) {
    const at = timestamp(line);
    const bucketIndex = Math.floor((at - firstBucket) / bucketMs);
    const bucket = buckets[bucketIndex];
    // Controller records are agent decisions made before execution. Count
    // both accepted and rejected attempts as actions; rejected calls still
    // consumed an agent step and operator time.
    if (/"event"\s*:\s*"(?:allowed|blocked)"/i.test(line)) {
      toolCallTotal += 1;
      if (bucket) bucket.toolCalls += 1;
    }
    const blocked = /"event"\s*:\s*"blocked"/i.test(line);
    const toolError = /"event"\s*:\s*"tool_error"/i.test(line);
    const errorSignature = line.match(/"signature"\s*:\s*"([^"]+)"/i)?.[1];
    // A blocked attempt is also reported to the post-tool hook as an error.
    // Count that lifecycle once. A tool_error with an allowed signature is a
    // genuine execution failure and remains a retry.
    if (blocked || (toolError && Boolean(errorSignature && allowedSignatures.has(errorSignature)))) {
      retryTotal += 1;
      if (bucket) bucket.retries += 1;
    }
  }

  for (const line of lines) {
    const at = timestamp(line);
    const bucketIndex = Math.floor((at - firstBucket) / bucketMs);
    const bucket = buckets[bucketIndex];
    const api = line.match(/API call #\d+:.*\bout=(\d+).*?\blatency=([\d.]+)s/i);
    if (api) {
      const outputTokens = Number(api[1]);
      const latencySeconds = Math.max(Number(api[2]), 0.001);
      const rate = outputTokens / latencySeconds;
      const generationStartedAt = at - (latencySeconds * 1000);
      tokensGenerated += outputTokens;
      modelCalls += 1;
      // Spread the generated tokens across the response latency instead of
      // drawing a one-second spike only when the response completes.
      for (const point of buckets) {
        const overlapMs = Math.max(
          0,
          Math.min(at, point.at + bucketMs) - Math.max(generationStartedAt, point.at),
        );
        point.generatedTokens += rate * (overlapMs / 1000);
      }
      if (at >= latestTpsAt) {
        latestTpsAt = at;
        latestTps = rate;
      }
    }
    // Agent Actions is intentionally broader than successful tool calls.
    // Every agent.* or tools.* log event is observable work: model-loop
    // transitions, tool preparation/completion, environment setup, vision
    // processing, registry decisions, and MCP activity all count. DML
    // provider actions use a separate logger and are included explicitly.
    const isAgentAction =
      /\b(?:agent|tools)\.[A-Za-z0-9_.]+:/i.test(line)
      || /\bMCP\b.*\btools?\b/i.test(line)
      || /Daystrom DCN active-read|Daystrom DML retrieved memory|Daystrom DML stored turn/i.test(line);
    if (isAgentAction) {
      toolCallTotal += 1;
      if (bucket) bucket.toolCalls += 1;
    }
    if (!hasControllerAttempts && /agent\.tool_executor:.*(?:returned error|rejected|validation failed|timed out|cancelled|failed)/i.test(line)) {
      retryTotal += 1;
      if (bucket) bucket.retries += 1;
    }
    if (/Daystrom DCN active-read|tool mcp__daystrom_dml__\w+ completed|Daystrom DML stored turn/i.test(line)) {
      dmlCalls += 1;
    }
    const recalled = line.match(/Daystrom DML retrieved memory:.*\bitems=(\d+)/i);
    if (recalled) {
      memoryRecalls += 1;
      memoriesAccessed += Number(recalled[1]);
      lastRecallAt = Math.max(lastRecallAt, at);
    }
    if (/Daystrom DML stored turn/i.test(line)) {
      memoryStores += 1;
      lastStoreAt = Math.max(lastStoreAt, at);
    }
  }

  const series = buckets.map((bucket) => ({
    at: new Date(bucket.at).toISOString(),
    tps: bucket.generatedTokens / BUCKET_SECONDS,
    toolRate: bucket.toolCalls / BUCKET_SECONDS,
    retries: bucket.retries,
  }));
  const recentToolCalls = series.reduce((sum, point) => sum + (point.toolRate * BUCKET_SECONDS), 0);

  return Response.json({
    series,
    current: {
      // During a live run this is the most recently observed generation rate;
      // completed runs decay to zero after the 20-second graph window.
      tps: resident?.status === "running" || now - latestTpsAt <= 20_000 ? latestTps : 0,
      toolRate: recentToolCalls / 20,
    },
    totals: {
      tokensGenerated,
      modelCalls,
      toolCalls: toolCallTotal,
      retries: retryTotal,
      dmlCalls,
      memoryRecalls,
      memoriesAccessed,
      memoryStores,
    },
    memoryActivity: {
      recallActive: now - lastRecallAt <= 10_000,
      writeActive: now - lastStoreAt <= 10_000,
      lastRecallAt: lastRecallAt ? new Date(lastRecallAt).toISOString() : null,
      lastStoreAt: lastStoreAt ? new Date(lastStoreAt).toISOString() : null,
    },
    windowSeconds: POINT_COUNT * BUCKET_SECONDS,
    updatedAt: new Date().toISOString(),
  }, { headers: { "Cache-Control": "no-store" } });
}
