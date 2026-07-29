import { promises as fs } from "node:fs";
import net from "node:net";
import os from "node:os";
import path from "node:path";
import { execFile } from "node:child_process";

export const HERMES_HOME = path.join(process.env.LOCALAPPDATA ?? "C:\\Users\\test\\AppData\\Local", "hermes");
export const REPO_ROOT = process.env.AEC_DEMO_ROOT ?? "C:\\Users\\test\\Documents\\RX Spark AEC\\2026_aec_cptx_demo_dml";
export const RUN_ROOT = path.join(REPO_ROOT, "aa_demo_versions", "cliff_house_single_frame_01");
export const LOG_DIR = path.join(HERMES_HOME, "profiles", "aec-cptx", "logs");
export const COMFY_OUTPUT = path.join(process.env.COMFYUI_ROOT ?? path.join(os.homedir(), "ComfyUI"), "output");
export const CONTROL_DIR = path.join(REPO_ROOT, "aec-mission-control", ".control");
export const VISUAL_EPOCH_FILE = path.join(CONTROL_DIR, "visual-epoch.json");
export const DASHBOARD_RUN_FILE = path.join(CONTROL_DIR, "dashboard-run.json");

export async function pathExists(target: string) {
  try { await fs.access(target); return true; } catch { return false; }
}

export async function visualWallIsStandby() {
  try {
    const epoch = JSON.parse(await fs.readFile(VISUAL_EPOCH_FILE, "utf8")) as { started_at?: string };
    const resetAt = new Date(epoch.started_at ?? 0).getTime();
    if (!resetAt) return false;
    try {
      const run = JSON.parse(await fs.readFile(DASHBOARD_RUN_FILE, "utf8")) as { started_at?: string };
      return new Date(run.started_at ?? 0).getTime() <= resetAt;
    } catch {
      return true;
    }
  } catch {
    return false;
  }
}

export async function dashboardRunStartedAt(): Promise<number | null> {
  try {
    const run = JSON.parse(await fs.readFile(DASHBOARD_RUN_FILE, "utf8")) as { started_at?: string };
    const startedAt = new Date(run.started_at ?? 0).getTime();
    return startedAt > 0 ? startedAt : null;
  } catch {
    return null;
  }
}

export function testPort(port: number, host = "127.0.0.1", timeout = 650): Promise<boolean> {
  return new Promise((resolve) => {
    const socket = net.createConnection({ port, host });
    const finish = (result: boolean) => { socket.destroy(); resolve(result); };
    socket.setTimeout(timeout);
    socket.once("connect", () => finish(true));
    socket.once("timeout", () => finish(false));
    socket.once("error", () => finish(false));
  });
}

let hermesProcessCache = { checkedAt: 0, running: false };

export function hermesRunning(): Promise<boolean> {
  if (Date.now() - hermesProcessCache.checkedAt < 3_000) {
    return Promise.resolve(hermesProcessCache.running);
  }
  return new Promise((resolve) => {
    execFile("powershell.exe", [
      "-NoProfile",
      "-Command",
      "$p=Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -ne $PID -and (($_.Name -eq 'hermes.exe') -or ($_.Name -eq 'powershell.exe' -and $_.CommandLine -match 'Start-Hermes-AEC-Rhino-DML\\.ps1.+-RunMode')) }; if($p){'RUNNING'}",
    ], { windowsHide: true }, (error, stdout) => {
      const running = !error && /RUNNING/i.test(stdout);
      hermesProcessCache = { checkedAt: Date.now(), running };
      resolve(running);
    });
  });
}

export type ResidentAgentState = {
  pid: number;
  status: "running" | "idle" | "error" | "stopped";
  session_id?: string | null;
  updated_at?: number;
  job_id?: string;
  last_job_id?: string;
  job_started_at?: number;
  last_job_started_at?: number;
  last_job_completed_at?: number;
  prompt_preview?: string;
  worker_version?: string;
};

export async function residentAgentState(): Promise<ResidentAgentState | null> {
  try {
    const state = JSON.parse(await fs.readFile(path.join(CONTROL_DIR, "resident-agent.json"), "utf8")) as ResidentAgentState;
    if (!state.pid || state.status === "stopped") return null;
    // The resident wrapper writes a heartbeat every five seconds. Trust a
    // fresh heartbeat on Windows, where process.kill(pid, 0) is not a reliable
    // existence probe for a process launched outside the Node process tree.
    if (state.updated_at && Date.now() - (state.updated_at * 1000) < 20_000) {
      return state;
    }
    process.kill(state.pid, 0);
    return state;
  } catch {
    return null;
  }
}

export async function latestFile(root: string, predicate: (filename: string) => boolean): Promise<string | null> {
  if (!(await pathExists(root))) return null;
  const stack = [root];
  let newest: { file: string; mtime: number } | null = null;
  while (stack.length) {
    const current = stack.pop()!;
    let entries;
    try { entries = await fs.readdir(current, { withFileTypes: true }); } catch { continue; }
    for (const entry of entries) {
      const full = path.join(current, entry.name);
      if (entry.isDirectory()) stack.push(full);
      else if (predicate(entry.name)) {
        const stat = await fs.stat(full);
        if (!newest || stat.mtimeMs > newest.mtime) newest = { file: full, mtime: stat.mtimeMs };
      }
    }
  }
  return newest?.file ?? null;
}

async function currentRunArtifact(file: string | null): Promise<string | null> {
  if (!file) return null;
  const resident = await residentAgentState();
  let minimumMtime = 0;
  try {
    const epoch = JSON.parse(await fs.readFile(VISUAL_EPOCH_FILE, "utf8")) as { started_at?: string };
    minimumMtime = new Date(epoch.started_at ?? 0).getTime();
  } catch {
    // A dashboard created before visual epochs should continue showing its
    // latest completed artifacts until the first explicit reset.
  }
  // The dashboard run is the visual epoch. Follow-up chat instructions are
  // separate resident jobs in the same run and must not invalidate completed
  // Blender/depth/FLUX frames while a refinement is being produced.
  const dashboardStartedAt = await dashboardRunStartedAt();
  if (dashboardStartedAt) {
    minimumMtime = Math.max(minimumMtime, dashboardStartedAt - 2000);
  } else if (resident?.status === "running" && resident.job_started_at) {
    // Legacy/non-dashboard launches have no run receipt, so retain the
    // resident job start as a safe fallback.
    minimumMtime = Math.max(minimumMtime, (resident.job_started_at * 1000) - 2000);
  }
  const stat = await fs.stat(file);
  if (stat.mtimeMs < minimumMtime) return null;
  return file;
}

export async function tailLines(file: string, maxBytes = 90000): Promise<string[]> {
  try {
    const handle = await fs.open(file, "r");
    const stat = await handle.stat();
    const size = Math.min(stat.size, maxBytes);
    const buffer = Buffer.alloc(size);
    await handle.read(buffer, 0, size, Math.max(0, stat.size - size));
    await handle.close();
    return buffer.toString("utf8").split(/\r?\n/).filter(Boolean);
  } catch { return []; }
}

export async function artifactPath(kind: string): Promise<string | null> {
  if (kind === "rhino") {
    return currentRunArtifact(
      await latestFile(path.join(RUN_ROOT, "rhino_captures"), (name) => /\.png$/i.test(name)),
    );
  }
  if (kind === "blender") {
    return currentRunArtifact(
      await latestFile(
        path.join(RUN_ROOT, "renders", "single_frame", "beauty"),
        (name) => /^frame_0000(?:_[^.]+)?\.png$/i.test(name),
      ),
    );
  }
  if (kind === "depth") {
    const preview = path.join(RUN_ROOT, "renders", "single_frame", "depth", "frame_0000_preview.png");
    const fixed = path.join(RUN_ROOT, "renders", "single_frame", "depth", "frame_0000.png");
    return currentRunArtifact(
      (await pathExists(preview))
        ? preview
        : (await pathExists(fixed))
          ? fixed
          : null,
    );
  }
  if (kind === "comfy") {
    return currentRunArtifact(
      await latestFile(
        path.join(RUN_ROOT, "renders", "single_frame", "flux2_enhanced"),
        (name) => /^frame_0000(?:_[^.]+)?\.png$/i.test(name),
      ),
    );
  }
  if (kind === "comfy-source") {
    return currentRunArtifact(
      await latestFile(
        path.join(RUN_ROOT, "renders", "single_frame", "comfy_source"),
        (name) => /^frame_0000(?:_[^.]+)?\.png$/i.test(name),
      ),
    );
  }
  return null;
}
