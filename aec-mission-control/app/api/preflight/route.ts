import { spawn } from "node:child_process";
import { promises as fs } from "node:fs";
import path from "node:path";
import { CONTROL_DIR, REPO_ROOT, residentAgentState } from "@/lib/local-aec";
import {
  getSystemDiagnostics,
  invalidateDiagnostics,
  PREFLIGHT_STATE_FILE,
  readPreflightReceipt,
} from "@/lib/system-diagnostics";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function runPreflight(receiptPath: string) {
  const script = path.join(REPO_ROOT, "deployment", "rtx-pro-profile", "Test-RTX-Pro-Preflight.ps1");
  const args = [
    "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script,
    "-StartServices", "-SkipRhinoLaunch", "-SingleVlm",
    "-ProfileName", "aec-cptx",
    "-ProjectId", "cliff-house-01",
    "-DmlStoreName", "cliff-house-01-rhino-store",
    "-CmaStoreName", "cma-cliff-house-01",
    "-DmlLauncherName", "dml_mcp_server_cliff_house.cmd",
    "-CmaLauncherName", "cma_mcp_server_cliff_house.cmd",
    "-DisplayName", "Cliff House",
    "-ReceiptPath", receiptPath,
  ];
  return new Promise<{ code: number; stdout: string; stderr: string }>((resolve) => {
    const child = spawn("powershell.exe", args, {
      cwd: REPO_ROOT,
      windowsHide: true,
      stdio: ["ignore", "pipe", "pipe"],
    });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => { stdout += String(chunk); });
    child.stderr.on("data", (chunk) => { stderr += String(chunk); });
    child.once("error", (error) => resolve({ code: 1, stdout, stderr: `${stderr}\n${error.message}` }));
    child.once("exit", (code) => resolve({ code: code ?? 1, stdout, stderr }));
  });
}

export async function GET() {
  return Response.json({
    preflight: await readPreflightReceipt(),
    services: await getSystemDiagnostics(),
  }, { headers: { "Cache-Control": "no-store" } });
}

export async function POST() {
  const resident = await residentAgentState();
  if (resident?.status === "running") {
    return Response.json({ error: "Preflight cannot run during an active workload. Stop the run first." }, { status: 409 });
  }

  await fs.mkdir(CONTROL_DIR, { recursive: true });
  const startedAt = new Date().toISOString();
  await fs.writeFile(PREFLIGHT_STATE_FILE, JSON.stringify({ status: "running", startedAt }), "utf8");
  const receiptPath = path.join(CONTROL_DIR, `preflight-${Date.now()}.json`);
  const logPath = path.join(CONTROL_DIR, "preflight-latest.log");
  const result = await runPreflight(receiptPath);
  await fs.writeFile(logPath, `${result.stdout}\n${result.stderr}`.trim(), "utf8");

  let receipt;
  try {
    receipt = JSON.parse((await fs.readFile(receiptPath, "utf8")).replace(/^\uFEFF/, ""));
  } catch {
    receipt = {
      status: "failed",
      startedAt,
      completedAt: new Date().toISOString(),
      failedRequired: 1,
      totalChecks: 1,
      checks: [{
        id: "preflight-runner",
        label: "Preflight runner",
        state: "fail",
        required: true,
        detail: result.stderr.trim() || `Preflight exited with code ${result.code}`,
      }],
    };
  }
  receipt.logPath = logPath;
  if (result.code !== 0 && receipt.status !== "failed") receipt.status = "failed";
  await fs.writeFile(PREFLIGHT_STATE_FILE, JSON.stringify(receipt, null, 2), "utf8");
  invalidateDiagnostics();
  const services = await getSystemDiagnostics(true);
  return Response.json({
    ok: receipt.status === "passed",
    preflight: receipt,
    services,
    message: receipt.status === "passed"
      ? `Preflight passed · ${receipt.totalChecks} checks verified.`
      : `Preflight failed · ${receipt.failedRequired ?? "one or more"} required checks need attention.`,
  }, { status: receipt.status === "passed" ? 200 : 409 });
}
