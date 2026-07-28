import { execFile } from "node:child_process";
import { promises as fs } from "node:fs";
import path from "node:path";
import { CONTROL_DIR, residentAgentState } from "@/lib/local-aec";
import { blenderSceneReceipt, rhinoObjectCount } from "@/lib/scene-control";

export type DiagnosticState = "pass" | "fail" | "warn";
export type DiagnosticCheck = {
  id: string;
  label: string;
  state: DiagnosticState;
  required?: boolean;
  detail: string;
  latencyMs?: number;
};
export type ServiceDiagnostic = {
  id: "hermes" | "rhino" | "blender" | "comfy" | "memory";
  name: string;
  online: boolean;
  status: "healthy" | "degraded" | "offline";
  detail: string;
  resolvable: boolean;
  checkedAt: string;
  checks: DiagnosticCheck[];
};
export type PreflightReceipt = {
  status: "idle" | "running" | "passed" | "failed";
  startedAt?: string;
  completedAt?: string;
  failedRequired?: number;
  totalChecks?: number;
  checks?: DiagnosticCheck[];
  error?: string;
};

export const PREFLIGHT_STATE_FILE = path.join(CONTROL_DIR, "preflight-state.json");

function processRunning(name: string) {
  return new Promise<boolean>((resolve) => {
    execFile("tasklist.exe", ["/FI", `IMAGENAME eq ${name}`, "/FO", "CSV", "/NH"], { windowsHide: true }, (error, stdout) => {
      resolve(!error && stdout.toLowerCase().includes(`"${name.toLowerCase()}"`));
    });
  });
}

async function timed<T>(operation: () => Promise<T>) {
  const started = performance.now();
  try {
    return { ok: true as const, value: await operation(), latencyMs: Math.round(performance.now() - started) };
  } catch (error) {
    return {
      ok: false as const,
      error: error instanceof Error ? error.message : String(error),
      latencyMs: Math.round(performance.now() - started),
    };
  }
}

async function httpProbe(url: string) {
  const response = await fetch(url, { cache: "no-store", signal: AbortSignal.timeout(3_500) });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response;
}

function service(
  id: ServiceDiagnostic["id"],
  name: string,
  checks: DiagnosticCheck[],
  resolvable: boolean,
): ServiceDiagnostic {
  const failed = checks.filter((check) => check.state === "fail");
  const online = failed.length === 0;
  return {
    id,
    name,
    online,
    status: online ? "healthy" : checks.some((check) => check.state === "pass") ? "degraded" : "offline",
    detail: online
      ? checks.at(-1)?.detail ?? "Healthy"
      : failed[0]?.detail ?? "Health check failed",
    resolvable,
    checkedAt: new Date().toISOString(),
    checks,
  };
}

let cache: { at: number; value: ServiceDiagnostic[] } | null = null;
let pending: Promise<ServiceDiagnostic[]> | null = null;

async function collectDiagnostics(): Promise<ServiceDiagnostic[]> {
  const [resident, rhinoProcess, blenderProcess, rhinoMcp, blenderMcp, comfy, ollama] = await Promise.all([
    residentAgentState(),
    processRunning("Rhino.exe"),
    processRunning("blender.exe"),
    timed(() => rhinoObjectCount()),
    timed(() => blenderSceneReceipt()),
    timed(() => httpProbe("http://127.0.0.1:8188/system_stats")),
    timed(() => httpProbe("http://127.0.0.1:11434/api/version")),
  ]);
  const hermesAlive = Boolean(resident);
  const hermesHealthy = hermesAlive && resident?.status !== "error" && resident?.worker_version === "warm-agent-v5";
  return [
    service("hermes", "Hermes", [
      {
        id: "hermes-resident",
        label: "Resident coordinator",
        state: hermesAlive ? "pass" : "fail",
        detail: hermesAlive ? `PID ${resident?.pid} · ${resident?.status}` : "Resident process is not responding",
      },
      {
        id: "hermes-worker",
        label: "Warm worker contract",
        state: hermesHealthy ? "pass" : "fail",
        detail: hermesHealthy ? "warm-agent-v5 ready" : resident?.status === "error" ? "Resident reported an error" : "Warm worker version is missing or stale",
      },
    ], true),
    service("rhino", "Rhino", [
      { id: "rhino-process", label: "Rhino application", state: rhinoProcess ? "pass" : "fail", detail: rhinoProcess ? "Rhino.exe is running" : "Rhino.exe is not running" },
      {
        id: "rhino-mcp",
        label: "Rhino MCP round trip",
        state: rhinoMcp.ok ? "pass" : "fail",
        detail: rhinoMcp.ok
          ? `Functional · ${rhinoMcp.value.activeCount} active objects · ${rhinoMcp.latencyMs} ms`
          : `MCP 10500 failed: ${rhinoMcp.error}`,
        latencyMs: rhinoMcp.latencyMs,
      },
    ], true),
    service("blender", "Blender", [
      { id: "blender-process", label: "Blender application", state: blenderProcess ? "pass" : "fail", detail: blenderProcess ? "blender.exe is running" : "blender.exe is not running" },
      {
        id: "blender-mcp",
        label: "Blender MCP round trip",
        state: blenderMcp.ok ? "pass" : "fail",
        detail: blenderMcp.ok
          ? `Functional · ${blenderMcp.value.count} scene objects · ${blenderMcp.latencyMs} ms`
          : `MCP 9876 failed: ${blenderMcp.error}`,
        latencyMs: blenderMcp.latencyMs,
      },
    ], true),
    service("comfy", "ComfyUI", [{
      id: "comfy-rest",
      label: "ComfyUI system API",
      state: comfy.ok ? "pass" : "fail",
      detail: comfy.ok ? `REST functional · ${comfy.latencyMs} ms` : `REST 8188 failed: ${comfy.error}`,
      latencyMs: comfy.latencyMs,
    }], false),
    service("memory", "DML / Ollama", [{
      id: "ollama-rest",
      label: "Ollama memory backend",
      state: ollama.ok ? "pass" : "fail",
      detail: ollama.ok ? `Memory backend functional · ${ollama.latencyMs} ms` : `Ollama 11434 failed: ${ollama.error}`,
      latencyMs: ollama.latencyMs,
    }], false),
  ];
}

export async function getSystemDiagnostics(force = false) {
  if (!force && cache && Date.now() - cache.at < 4_000) return cache.value;
  if (!force && pending) return pending;
  pending = collectDiagnostics();
  try {
    const value = await pending;
    cache = { at: Date.now(), value };
    return value;
  } finally {
    pending = null;
  }
}

export function invalidateDiagnostics() {
  cache = null;
}

export async function readPreflightReceipt(): Promise<PreflightReceipt> {
  try {
    return JSON.parse((await fs.readFile(PREFLIGHT_STATE_FILE, "utf8")).replace(/^\uFEFF/, ""));
  } catch {
    return { status: "idle" };
  }
}
