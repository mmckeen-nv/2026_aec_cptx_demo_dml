import { spawn } from "node:child_process";
import { promises as fs } from "node:fs";
import path from "node:path";
import { CONTROL_DIR, REPO_ROOT, residentAgentState } from "@/lib/local-aec";

const RESIDENT_WORKER_VERSION = "warm-agent-v5";

export async function ensureResidentWithoutPreflight() {
  const existing = await residentAgentState();
  if (existing) return existing;

  const localAppData = process.env.LOCALAPPDATA;
  if (!localAppData) throw new Error("LOCALAPPDATA is unavailable.");
  const scripts = path.join(localAppData, "hermes", "hermes-agent", "venv", "Scripts");
  const python = path.join(scripts, "python.exe");
  const hermes = path.join(scripts, "hermes.exe");
  const worker = path.join(REPO_ROOT, "deployment", "aec-control-plane", "hermes_resident_worker.py");

  await Promise.all([
    fs.access(python),
    fs.access(hermes),
    fs.access(worker),
    fs.mkdir(CONTROL_DIR, { recursive: true }),
  ]);
  await Promise.all([
    fs.rm(path.join(CONTROL_DIR, "resident-agent.stop"), { force: true }),
    fs.rm(path.join(CONTROL_DIR, "resident-agent.lock"), { force: true }),
  ]);

  const child = spawn(python, [
    worker,
    "--hermes-exe", hermes,
    "--profile", "aec-cptx",
    "--repo", REPO_ROOT,
    "--queue-dir", CONTROL_DIR,
    "--start-idle",
  ], {
    cwd: REPO_ROOT,
    windowsHide: true,
    detached: true,
    stdio: "ignore",
    env: {
      ...process.env,
      HERMES_HOME: path.join(localAppData, "hermes"),
    },
  });
  child.unref();

  const deadline = Date.now() + 20_000;
  while (Date.now() < deadline) {
    await new Promise((resolve) => setTimeout(resolve, 200));
    const resident = await residentAgentState();
    if (resident?.worker_version === RESIDENT_WORKER_VERSION) return resident;
  }
  throw new Error("Hermes resident did not become idle within 20 seconds.");
}
