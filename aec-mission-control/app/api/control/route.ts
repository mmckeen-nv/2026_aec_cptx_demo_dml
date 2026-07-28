import { spawn } from "node:child_process";
import { promises as fs } from "node:fs";
import path from "node:path";
import { CONTROL_DIR, DASHBOARD_RUN_FILE, REPO_ROOT, residentAgentState, VISUAL_EPOCH_FILE } from "@/lib/local-aec";
import { SCENE_STATE_FILE, verifySceneCounts } from "@/lib/scene-control";
import { ensureResidentWithoutPreflight } from "@/lib/resident-control";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type LaunchReceipt = {
  pid: number;
  mode: string;
  started_at: string;
  stdout: string | null;
  stderr: string | null;
};
const RESIDENT_WORKER_VERSION = "warm-agent-v5";

function runBroker(args: string[]): Promise<{ code: number; stdout: string; stderr: string }> {
  return new Promise((resolve) => {
    const child = spawn("powershell.exe", args, {
      windowsHide: true,
      cwd: REPO_ROOT,
      stdio: ["ignore", "pipe", "pipe"],
    });
    let stdout = "";
    let stderr = "";
    let settled = false;
    const finish = (code: number) => {
      if (settled) return;
      settled = true;
      resolve({ code, stdout, stderr });
    };
    child.stdout.on("data", (chunk) => { stdout += String(chunk); });
    child.stderr.on("data", (chunk) => { stderr += String(chunk); });
    child.once("error", (error) => {
      stderr = `${stderr}\n${error.message}`;
      finish(1);
    });
    // `close` waits for handles inherited by the launched Hermes process.
    // `exit` is the broker receipt boundary and returns immediately.
    child.once("exit", (code) => finish(code ?? 1));
  });
}

export async function POST(request: Request) {
  let body: { action?: string; query?: string };
  try { body = await request.json(); } catch {
    return Response.json({ error: "Invalid request body" }, { status: 400 });
  }
  if (!["manual", "automatic", "reset", "query"].includes(body.action ?? "")) {
    return Response.json({ error: "Unsupported Hermes action" }, { status: 400 });
  }
  const query = body.query?.trim();
  if (body.action === "query" && !query) {
    return Response.json({ error: "A Hermes instruction is required" }, { status: 400 });
  }

  const automaticPromptPath = path.join(REPO_ROOT, "deployment", "aec-cptx-profile", "cliff-house-automatic-run.txt");
  const automaticPrompt = body.action === "automatic"
    ? await fs.readFile(automaticPromptPath, "utf8")
    : "";
  const prompt = body.action === "reset"
    ? [
        "The operator explicitly authorizes this destructive live-scene reset.",
        "Use the registered Rhino and Blender MCP tools to delete every object from the currently open Rhino document and Blender scene.",
        "Do not delete saved project files, checkpoints, logs, DML memory, or run history.",
        "Verify the live Rhino object count is exactly zero and the live Blender object count is exactly zero.",
        "After verification, stop. Do not start construction. Leave both applications empty and ready for a fresh run.",
      ].join("\n")
    : body.action === "automatic"
      ? automaticPrompt
      : body.action === "manual"
      ? "Start the Cliff House demo manually. Use the numbered phase prompts, object-by-object Rhino pacing, and stop at every operator review gate."
      : query!;
  const controlDir = CONTROL_DIR;
  await fs.mkdir(controlDir, { recursive: true });
  if (body.action === "reset") {
    await fs.rm(DASHBOARD_RUN_FILE, { force: true });
    await fs.writeFile(VISUAL_EPOCH_FILE, JSON.stringify({
      started_at: new Date().toISOString(),
      reason: "explicit-scene-reset",
    }), "utf8");
  }
  const nonce = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  const dashboardStartedAt = new Date().toISOString();

  let resident = await residentAgentState();
  // Upgrade an idle legacy coordinator before accepting its next job. Active
  // work is never interrupted; the one-time restart happens only at an idle
  // button press and installs the in-process warm agent.
  if (resident && resident.status !== "running" && resident.worker_version !== RESIDENT_WORKER_VERSION) {
    await fs.writeFile(path.join(controlDir, "resident-agent.stop"), "upgrade", "utf8");
    const deadline = Date.now() + 8_000;
    while (Date.now() < deadline) {
      await new Promise((resolve) => setTimeout(resolve, 200));
      resident = await residentAgentState();
      if (!resident) break;
    }
    await fs.rm(path.join(controlDir, "resident-agent.stop"), { force: true });
    if (resident) {
      return Response.json({
        error: "The resident Hermes upgrade is still draining. Retry in a few seconds.",
      }, { status: 503 });
    }
  }
  if (body.action === "automatic") {
    if (!resident) {
      // Starting the configured warm resident is not preflight. This makes
      // the button deterministic after either Reset Scenes or an emergency
      // stop instead of rejecting the first click with a lifecycle error.
      resident = await ensureResidentWithoutPreflight();
    }
    if (resident.status === "running") {
      return Response.json({
        error: "Hermes is already running. Stop or finish the active job before starting an automatic run.",
      }, { status: 409 });
    }
    let resetReceipt: { status?: string } = {};
    try {
      resetReceipt = JSON.parse(await fs.readFile(SCENE_STATE_FILE, "utf8"));
    } catch {
      // The operator must establish the reset contract explicitly.
    }
    if (resetReceipt.status !== "empty") {
      return Response.json({
        error: "Reset Scenes must complete successfully before Run Automatically.",
      }, { status: 409 });
    }
    // This is the entire automatic-run readiness check: one direct live poke
    // to each application. It is not a Hermes/model preflight.
    const counts = await verifySceneCounts();
    const pokeReceipt = {
      status: counts.empty ? "ready" : "occupied",
      ...counts,
      verifiedAt: new Date().toISOString(),
      contract: "post-reset-live-poke",
    };
    await fs.writeFile(
      path.join(controlDir, "automatic-reset-poke.json"),
      JSON.stringify(pokeReceipt),
      "utf8",
    );
    if (!counts.empty) {
      return Response.json({
        error: `Post-reset live poke failed: Rhino ${counts.rhinoCount} active / ${counts.rhinoTableCount} retained records; Blender ${counts.blenderCount} objects.`,
        ...pokeReceipt,
      }, { status: 409 });
    }
  }
  if (body.action !== "reset") {
    await fs.writeFile(SCENE_STATE_FILE, JSON.stringify({
      status: "unknown",
      invalidatedAt: new Date().toISOString(),
      reason: `${body.action}-may-mutate-live-scenes`,
    }), "utf8");
  }
  if (resident) {
    const jobId = `job-${nonce}`;
    const temporary = path.join(controlDir, `${jobId}.tmp`);
    const destination = path.join(controlDir, `${jobId}.json`);
    await fs.writeFile(temporary, JSON.stringify({
      id: jobId,
      action: body.action,
      prompt,
      queued_at: new Date().toISOString(),
    }), "utf8");
    await fs.rename(temporary, destination);
    if (body.action === "automatic" || body.action === "manual") {
      await fs.writeFile(DASHBOARD_RUN_FILE, JSON.stringify({
        action: body.action,
        job_id: jobId,
        started_at: dashboardStartedAt,
      }), "utf8");
    }
    return Response.json({
      ok: true,
      queued: true,
      pid: resident.pid,
      session_id: resident.session_id,
      message: body.action === "reset"
        ? resident.status === "running"
          ? `Scene reset queued behind the active Hermes turn (PID ${resident.pid})`
          : `Scene reset sent to the resident Hermes agent (PID ${resident.pid}); the visual wall is cleared`
        : resident.status === "running"
        ? `Instruction queued behind the active Hermes turn (PID ${resident.pid})`
        : `Instruction sent to the resident Hermes agent (PID ${resident.pid}); preflight skipped`,
    });
  }

  if (body.action === "automatic") {
    return Response.json({
      error: "Hermes is not resident. Press Restart once; automatic runs never invoke the launcher or preflight path.",
    }, { status: 503 });
  }

  const runMode = body.action === "automatic" ? "Automatic" : "Query";
  const receiptPath = path.join(controlDir, `launch-${nonce}.json`);
  const queryPath = path.join(controlDir, `query-${nonce}.txt`);
  if (runMode === "Query") await fs.writeFile(queryPath, prompt, "utf8");

  const broker = path.join(REPO_ROOT, "deployment", "aec-control-plane", "Start-Hermes-ControlRun.ps1");
  const args = [
    "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", broker,
    "-Mode", runMode, "-ReceiptPath", receiptPath,
  ];
  if (runMode === "Query") args.push("-QueryFile", queryPath);
  const result = await runBroker(args);
  if (result.code !== 0) {
    return Response.json({
      error: "Hermes launch broker failed.",
      detail: (result.stderr || result.stdout).trim().slice(-1200),
    }, { status: 500 });
  }

  let receipt: LaunchReceipt;
  try {
    receipt = JSON.parse((await fs.readFile(receiptPath, "utf8")).replace(/^\uFEFF/, ""));
  } catch {
    return Response.json({ error: "Hermes launch broker returned no process receipt." }, { status: 500 });
  }
  if (body.action === "automatic" || body.action === "manual") {
    await fs.writeFile(DASHBOARD_RUN_FILE, JSON.stringify({
      action: body.action,
      job_id: "initial",
      started_at: dashboardStartedAt,
      pid: receipt.pid,
    }), "utf8");
  }

  return Response.json({
    ok: true,
    ...receipt,
    message: runMode === "Automatic"
      ? `Automatic Cliff House run started with a resident agent (PID ${receipt.pid})`
      : body.action === "reset"
        ? `Authorized scene reset started (PID ${receipt.pid})`
        : `Resident Hermes agent started (PID ${receipt.pid})`,
  });
}
