import { spawn } from "node:child_process";
import { promises as fs } from "node:fs";
import path from "node:path";
import {
  CONTROL_DIR,
  DASHBOARD_RUN_FILE,
  REPO_ROOT,
  residentAgentState,
  VISUAL_EPOCH_FILE,
} from "@/lib/local-aec";
import {
  emergencyStop,
  RESTART_STATE_FILE,
  resetScenes,
} from "@/lib/scene-control";
import { ensureResidentWithoutPreflight } from "@/lib/resident-control";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type RestartReceipt = {
  pid: number;
  mode: string;
  started_at: string;
  stdout: string;
  stderr: string;
};

async function startRestart(): Promise<RestartReceipt> {
  const receiptPath = path.join(CONTROL_DIR, `restart-${Date.now()}.json`);
  const broker = path.join(REPO_ROOT, "deployment", "aec-control-plane", "Start-Hermes-ControlRun.ps1");
  return new Promise((resolve, reject) => {
    const child = spawn("powershell.exe", [
      "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", broker,
      "-Mode", "Idle", "-ReceiptPath", receiptPath,
    ], {
      windowsHide: true,
      cwd: REPO_ROOT,
      stdio: ["ignore", "pipe", "pipe"],
    });
    let stderr = "";
    child.stderr.on("data", (chunk) => { stderr += String(chunk); });
    child.once("error", reject);
    child.once("exit", async (code) => {
      if (code !== 0) return reject(new Error(stderr || "Restart broker failed"));
      try {
        const receipt = JSON.parse((await fs.readFile(receiptPath, "utf8")).replace(/^\uFEFF/, ""));
        resolve(receipt);
      } catch (error) {
        reject(error);
      }
    });
  });
}

export async function POST(request: Request) {
  let body: { action?: string };
  try { body = await request.json(); } catch {
    return Response.json({ error: "Invalid request body" }, { status: 400 });
  }
  if (!["emergency-stop", "restart", "reset"].includes(body.action ?? "")) {
    return Response.json({ error: "Unsupported system action" }, { status: 400 });
  }

  try {
    if (body.action === "emergency-stop") {
      const receipt = await emergencyStop();
      return Response.json({
        ok: true,
        ...receipt,
        message: "EMERGENCY STOP complete — the active run and queued work are stopped.",
      });
    }

    if (body.action === "reset") {
      const resident = await residentAgentState();
      if (resident?.status === "running") await emergencyStop();
      await fs.rm(DASHBOARD_RUN_FILE, { force: true });
      await fs.rm(path.join(CONTROL_DIR, "automatic-reset-poke.json"), { force: true });
      await fs.writeFile(VISUAL_EPOCH_FILE, JSON.stringify({
        started_at: new Date().toISOString(),
        reason: "verified-direct-scene-reset",
      }), "utf8");
      const receipt = await resetScenes();
      // Reset is not a service preflight, but it must leave the control plane
      // able to accept the next Run Automatically click. If stopping an active
      // job took the resident down, bring back only the warm idle worker.
      const idleResident = await ensureResidentWithoutPreflight();
      return Response.json({
        ok: receipt.status === "empty",
        ...receipt,
        residentPid: idleResident.pid,
        message: receipt.status === "empty"
          ? receipt.blenderDefaultBaseline
            ? `Reset verified — Rhino 0 active / 0 retained records · Blender default baseline (${receipt.blenderCount} objects).`
            : "Reset verified — Rhino 0 active / 0 retained records · Blender 0 objects."
          : `Reset incomplete — Rhino ${receipt.rhinoCount} active / ${receipt.rhinoTableCount} retained records · Blender ${receipt.blenderCount}.`,
      }, { status: receipt.status === "empty" ? 200 : 409 });
    }

    await emergencyStop();
    // Restart establishes a fresh idle coordinator, not a continuation of the
    // prior workload. Clear its timer receipt so idle time is never presented
    // as additional run time while preserving the completed scene/artifacts.
    await fs.rm(DASHBOARD_RUN_FILE, { force: true });
    const receipt = await startRestart();
    await fs.writeFile(RESTART_STATE_FILE, JSON.stringify({
      status: "preflighting",
      ...receipt,
    }), "utf8");
    return Response.json({
      ok: true,
      ...receipt,
      message: "Restart initiated — full preflight is running; Hermes will remain idle when ready.",
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    if (body.action === "restart") {
      await fs.writeFile(RESTART_STATE_FILE, JSON.stringify({
        status: "error",
        error: message,
        completed_at: new Date().toISOString(),
      }), "utf8");
    }
    return Response.json({ error: message }, { status: 500 });
  }
}
