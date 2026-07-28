import path from "node:path";
import { promises as fs } from "node:fs";
import { dashboardRunStartedAt, DASHBOARD_RUN_FILE, hermesRunning, pathExists, residentAgentState, RUN_ROOT, VISUAL_EPOCH_FILE } from "@/lib/local-aec";
import { RESTART_STATE_FILE, SCENE_STATE_FILE } from "@/lib/scene-control";
import { getSystemDiagnostics, readPreflightReceipt } from "@/lib/system-diagnostics";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const phaseSpecs = [
  ["Reset proof", "Rhino & Blender empty", "__post_reset_poke__"],
  ["Rhino build", "Canonical geometry", "rhino_assets/base_model.3dm"],
  ["Geometry QA", "Compass & detail checks", "validation/hero_geometry_validation.json"],
  ["Blender scene", "Import, cleanup, camera", "blender_assets/base_model.blend"],
  ["Beauty render", "GPU scene output", "renders/single_frame/beauty/frame_0000.png"],
  ["Control pass", "Depth compositor output", "renders/single_frame/depth/frame_0000.png"],
  ["FLUX.2", "Final stylized frame", "renders/single_frame/flux2_enhanced/frame_0000.png"],
] as const;

function formatElapsed(startedAt: number, completedAt = Date.now()) {
  const seconds = Math.max(0, Math.floor((completedAt - startedAt) / 1000));
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainder = seconds % 60;
  return hours > 0
    ? `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(remainder).padStart(2, "0")}`
    : `${String(minutes).padStart(2, "0")}:${String(remainder).padStart(2, "0")}`;
}

async function elapsedFromRun(resident: Awaited<ReturnType<typeof residentAgentState>>) {
  try {
    const dashboard = JSON.parse(await fs.readFile(DASHBOARD_RUN_FILE, "utf8")) as {
      job_id?: string;
      started_at?: string;
      completed_at?: string;
    };
    const startedAt = new Date(dashboard.started_at ?? 0).getTime();
    if (startedAt > 0) {
      let validatedAt: number | undefined;
      try {
        const timeline = path.join(RUN_ROOT, "automatic_run_timeline.jsonl");
        const rows = (await fs.readFile(timeline, "utf8"))
          .trim()
          .split(/\r?\n/)
          .map((line) => JSON.parse(line) as { milestone?: string; timestamp?: string });
        validatedAt = rows
          .map((row) => ({
            milestone: row.milestone,
            timestamp: new Date(row.timestamp ?? 0).getTime(),
          }))
          .find((row) => row.milestone === "validation_complete" && row.timestamp >= startedAt)
          ?.timestamp;
      } catch {
        // A run in progress may not have a validation milestone yet.
      }
      const residentCompletedAt =
        resident && resident.last_job_id === dashboard.job_id
          ? resident.last_job_completed_at
          : undefined;
      const completedAt = dashboard.completed_at
        ? new Date(dashboard.completed_at).getTime()
        : validatedAt
          ? validatedAt
        : residentCompletedAt
          ? residentCompletedAt * 1000
          : Date.now();
      return formatElapsed(startedAt, completedAt);
    }
  } catch {
    // Older runs fall back to the workload timeline.
  }
  // A newly restarted resident has no workload receipt. Its idle lifetime is
  // not run time, even if an older automatic timeline remains on disk.
  if (resident && !resident.last_job_id) return "00:00";
  const timeline = path.join(RUN_ROOT, "automatic_run_timeline.jsonl");
  try {
    const rows = (await fs.readFile(timeline, "utf8")).trim().split(/\r?\n/).map((line) => JSON.parse(line));
    const start = [...rows].reverse().find((row) => row.event === "process_start");
    if (!start) return "00:00";
    const end = [...rows].reverse().find((row) => row.event === "process_end" && new Date(row.timestamp) >= new Date(start.timestamp));
    return formatElapsed(
      new Date(start.timestamp).getTime(),
      (end ? new Date(end.timestamp) : new Date()).getTime(),
    );
  } catch { return "00:00"; }
}

export async function GET() {
  const resident = await residentAgentState();
  let sceneState: {
    status: "unknown" | "verifying" | "empty" | "occupied" | "error";
    rhinoCount?: number;
    rhinoTableCount?: number;
    blenderCount?: number;
    blenderDefaultBaseline?: boolean;
    verifiedAt?: string;
    error?: string;
  } = { status: "unknown" };
  let restartState: {
    status?: "preflighting" | "error";
    pid?: number;
    started_at?: string;
    stderr?: string;
    error?: string;
  } | null = null;
  try { sceneState = JSON.parse(await fs.readFile(SCENE_STATE_FILE, "utf8")); } catch {}
  try { restartState = JSON.parse(await fs.readFile(RESTART_STATE_FILE, "utf8")); } catch {}
  let restartProcessAlive = false;
  if (restartState?.pid) {
    try {
      process.kill(restartState.pid, 0);
      restartProcessAlive = true;
    } catch {}
  }
  const restartAge = Date.now() - new Date(restartState?.started_at ?? 0).getTime();
  const restartExitedEarly =
    restartState?.status === "preflighting"
    && !resident
    && !restartProcessAlive
    && restartAge > 5_000;
  let restartError = restartState?.status === "error" ? restartState.error : null;
  if (restartExitedEarly && !restartError) {
    try {
      const detail = (await fs.readFile(restartState?.stderr ?? "", "utf8")).trim();
      restartError = detail.slice(-500) || "Preflight process exited before Hermes became ready.";
    } catch {
      restartError = "Preflight process exited before Hermes became ready.";
    }
  }
  const restarting = restartState?.status === "preflighting" && !resident && !restartExitedEarly;
  const [legacyRunning, diagnostics, preflight] = await Promise.all([
    resident ? Promise.resolve(false) : hermesRunning(),
    getSystemDiagnostics(),
    readPreflightReceipt(),
  ]);
  const running = resident ? resident.status === "running" : legacyRunning;
  let visualEpoch: number | null = null;
  try {
    const epoch = JSON.parse(await fs.readFile(VISUAL_EPOCH_FILE, "utf8")) as { started_at?: string };
    visualEpoch = new Date(epoch.started_at ?? 0).getTime();
  } catch {
    // No explicit reset has established a visual epoch yet.
  }
  const dashboardStartedAt = await dashboardRunStartedAt();
  const runStartedAt = Math.max(
    visualEpoch ?? 0,
    dashboardStartedAt
      ? dashboardStartedAt - 2000
      : resident?.status === "running" && resident.job_started_at
        ? (resident.job_started_at * 1000) - 2000
        : 0,
  ) || null;
  const completed = await Promise.all(phaseSpecs.map(async (spec, index) => {
    if (index === 0) {
      if (sceneState.status === "empty") return true;
      try {
        const poke = JSON.parse(
          await fs.readFile(path.join(path.dirname(SCENE_STATE_FILE), "automatic-reset-poke.json"), "utf8"),
        ) as { status?: string; verifiedAt?: string };
        const verifiedAt = new Date(poke.verifiedAt ?? 0).getTime();
        return poke.status === "ready" && (visualEpoch === null || verifiedAt >= visualEpoch);
      } catch {
        return false;
      }
    }
    const file = path.join(RUN_ROOT, spec[2]);
    if (!(await pathExists(file))) return false;
    // Every material build artifact must belong to the current run.
    if (runStartedAt === null) return true;
    return (await fs.stat(file)).mtimeMs >= runStartedAt;
  }));
  // A later current-run artifact proves the pipeline has advanced beyond all
  // earlier visual stages even if an optional/intermediate receipt was not
  // written. Keep the dashboard phase monotonic instead of pinning it to an
  // earlier missing QA file while Blender, depth, or FLUX output is visible.
  const effectiveCompleted = completed.map(
    (done, index) => done || completed.slice(index + 1).some(Boolean),
  );
  let current = effectiveCompleted.findIndex((done) => !done);
  if (current < 0) current = phaseSpecs.length - 1;
  const phases = phaseSpecs.map((spec, index) => ({
    id: index + 1,
    name: spec[0],
    detail: spec[1],
    state: effectiveCompleted[index] ? "done" : index === current && running ? "active" : "waiting",
  }));

  return Response.json({
    running,
    runLabel: running
      ? `Phase ${Math.min(current + 1, phaseSpecs.length)} · Running`
      : restarting
        ? "Preflight running"
      : restartError
        ? "Restart failed"
      : resident
        ? sceneState.status === "empty"
          ? "Agent ready · scenes reset"
          : "Agent ready"
        : "Ready",
    restart: {
      status: resident && restartState?.status === "preflighting"
        ? "ready"
        : restartError
          ? "error"
          : restarting
            ? "preflighting"
            : "idle",
      error: restartError,
    },
    preflight,
    sceneState,
    elapsed: await elapsedFromRun(resident),
    currentPhase: current + 1,
    phases,
    services: diagnostics.map((service) =>
      service.id === "hermes" && running
        ? { ...service, detail: "Agent active" }
        : service.id === "hermes" && restarting
          ? { ...service, detail: "Restart preflight running" }
          : service
    ),
    updatedAt: new Date().toISOString(),
  }, { headers: { "Cache-Control": "no-store" } });
}
