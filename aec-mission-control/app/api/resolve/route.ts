import { execFile } from "node:child_process";
import { residentAgentState } from "@/lib/local-aec";
import { ensureResidentWithoutPreflight } from "@/lib/resident-control";
import { emergencyStop } from "@/lib/scene-control";
import { getSystemDiagnostics, invalidateDiagnostics } from "@/lib/system-diagnostics";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type Target = "rhino" | "blender" | "hermes";

function powershell(script: string, timeout = 45_000) {
  return new Promise<void>((resolve, reject) => {
    execFile("powershell.exe", ["-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script], {
      windowsHide: true,
      timeout,
    }, (error, _stdout, stderr) => {
      if (error) reject(new Error(stderr.trim() || error.message));
      else resolve();
    });
  });
}

async function waitHealthy(target: Target) {
  const deadline = Date.now() + 45_000;
  while (Date.now() < deadline) {
    invalidateDiagnostics();
    const diagnostics = await getSystemDiagnostics(true);
    const service = diagnostics.find((item) => item.id === target);
    if (service?.online) return service;
    await new Promise((resolve) => setTimeout(resolve, 1_000));
  }
  throw new Error(`${target} did not pass its functional health check within 45 seconds.`);
}

export async function POST(request: Request) {
  let body: { service?: Target };
  try { body = await request.json(); } catch {
    return Response.json({ error: "Invalid request body" }, { status: 400 });
  }
  if (!["rhino", "blender", "hermes"].includes(body.service ?? "")) {
    return Response.json({ error: "Unsupported recovery target" }, { status: 400 });
  }
  const target = body.service as Target;
  const resident = await residentAgentState();
  if (resident?.status === "running") {
    return Response.json({ error: "Recovery is locked during an active workload. Use EMERGENCY STOP first." }, { status: 409 });
  }

  try {
    if (target === "hermes") {
      if (resident) await emergencyStop();
      await ensureResidentWithoutPreflight();
    } else if (target === "blender") {
      await powershell([
        "Get-Process blender -ErrorAction SilentlyContinue | Stop-Process -Force",
        "Start-Sleep -Milliseconds 800",
        "$exe = Get-ChildItem 'C:\\Program Files\\Blender Foundation' -Filter blender.exe -Recurse -ErrorAction Stop | Sort-Object FullName -Descending | Select-Object -First 1 -ExpandProperty FullName",
        "Start-Process -FilePath $exe",
      ].join("; "));
    } else {
      await powershell([
        "Get-Process Rhino -ErrorAction SilentlyContinue | Stop-Process -Force",
        "Start-Sleep -Milliseconds 800",
        "$shortcut = 'C:\\Users\\test\\Desktop\\Rhino 8.lnk'",
        "if (Test-Path $shortcut) { Start-Process $shortcut } else { Start-Process 'C:\\Program Files\\Rhino 8\\System\\Rhino.exe' -ArgumentList '/netfx' }",
      ].join("; "));
    }
    const service = await waitHealthy(target);
    return Response.json({
      ok: true,
      service,
      message: `${service.name} recovered and passed its functional health check.`,
    });
  } catch (error) {
    invalidateDiagnostics();
    return Response.json({
      error: error instanceof Error ? error.message : String(error),
      services: await getSystemDiagnostics(true),
    }, { status: 500 });
  }
}
