import { spawn } from "node:child_process";
import { promises as fs } from "node:fs";
import net from "node:net";
import path from "node:path";
import {
  CONTROL_DIR,
  DASHBOARD_RUN_FILE,
  residentAgentState,
} from "@/lib/local-aec";

export const SCENE_STATE_FILE = path.join(CONTROL_DIR, "scene-state.json");
export const RESTART_STATE_FILE = path.join(CONTROL_DIR, "restart-state.json");

type RhinoPayload = {
  result?: {
    isError?: boolean;
    content?: Array<{ type?: string; text?: string }>;
  };
  error?: { message?: string };
};

function runProcess(file: string, args: string[], timeoutMs = 12_000) {
  return new Promise<{ code: number; stdout: string; stderr: string }>((resolve) => {
    const child = spawn(file, args, { windowsHide: true, stdio: ["ignore", "pipe", "pipe"] });
    let stdout = "";
    let stderr = "";
    let finished = false;
    const finish = (code: number) => {
      if (finished) return;
      finished = true;
      clearTimeout(timer);
      resolve({ code, stdout, stderr });
    };
    child.stdout.on("data", (chunk) => { stdout += String(chunk); });
    child.stderr.on("data", (chunk) => { stderr += String(chunk); });
    child.once("error", (error) => {
      stderr += error.message;
      finish(1);
    });
    child.once("exit", (code) => finish(code ?? 1));
    const timer = setTimeout(() => {
      child.kill();
      finish(124);
    }, timeoutMs);
  });
}

export async function rhinoTool(name: string, args: Record<string, unknown> = {}): Promise<RhinoPayload> {
  const response = await fetch("http://127.0.0.1:10500/", {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({
      jsonrpc: "2.0",
      id: Date.now(),
      method: "tools/call",
      params: { name, arguments: args },
    }),
    cache: "no-store",
    signal: AbortSignal.timeout(12_000),
  });
  if (!response.ok) throw new Error(`Rhino MCP returned ${response.status}`);
  const payload = await response.json() as RhinoPayload;
  if (payload.error || payload.result?.isError) {
    throw new Error(payload.error?.message ?? payload.result?.content?.[0]?.text ?? "Rhino MCP call failed");
  }
  const text = payload.result?.content?.find((item) => item.type === "text")?.text;
  if (text) {
    try {
      const nested = JSON.parse(text) as { error?: string | null };
      if (nested.error) throw new Error(nested.error);
    } catch (error) {
      if (error instanceof SyntaxError) {
        // Most Rhino tools return ordinary text or a different JSON shape.
      } else {
        throw error;
      }
    }
  }
  return payload;
}

export function blenderCommand(command: object): Promise<{ status?: string; result?: { result?: string }; message?: string }> {
  return new Promise((resolve, reject) => {
    const socket = net.createConnection({ host: "127.0.0.1", port: 9876 });
    const chunks: Buffer[] = [];
    let settled = false;
    const finish = (error?: Error) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      socket.destroy();
      if (error) reject(error);
      else {
        try { resolve(JSON.parse(Buffer.concat(chunks).toString("utf8"))); }
        catch (parseError) { reject(parseError); }
      }
    };
    const timer = setTimeout(() => finish(new Error("Blender MCP timed out")), 12_000);
    socket.once("connect", () => socket.write(JSON.stringify(command)));
    socket.on("data", (chunk) => {
      chunks.push(Buffer.from(chunk));
      try {
        JSON.parse(Buffer.concat(chunks).toString("utf8"));
        finish();
      } catch {
        // Wait for a complete JSON response.
      }
    });
    socket.once("error", (error) => finish(error));
  });
}

const rhinoDeepEnumerator = [
  "var settings = new Rhino.DocObjects.ObjectEnumeratorSettings();",
  "settings.ActiveObjects = true;",
  "settings.NormalObjects = true;",
  "settings.LockedObjects = true;",
  "settings.HiddenObjects = true;",
  "settings.ReferenceObjects = false;",
  "settings.IdefObjects = false;",
  "settings.DeletedObjects = false;",
  "settings.IncludeLights = true;",
  "settings.IncludeGrips = false;",
  "settings.IncludePhantoms = true;",
].join("\n");

export async function rhinoObjectCount() {
  // Audit from inside RhinoCommon. The MCP list_objects wrapper has omitted
  // objects on hidden layers on this host. ObjectTable.Count is also required:
  // Rhino retains force-deleted geometry in the undo/deleted-object table even
  // when every active-object enumerator reports zero.
  const payload = await rhinoTool("run_csharp", {
    script: [
      rhinoDeepEnumerator,
      "var objects = __rhino_doc__.Objects.FindByFilter(settings);",
      "System.Console.WriteLine(\"AEC_DEEP_OBJECT_COUNT=\" + objects.Length + \";TABLE_COUNT=\" + __rhino_doc__.Objects.Count);",
    ].join("\n"),
  });
  const text = payload.result?.content?.find((item) => item.type === "text")?.text;
  if (!text) throw new Error("Rhino returned no deep object-count receipt");
  const envelope = JSON.parse(text) as { stdout?: string };
  const match = envelope.stdout?.match(/AEC_DEEP_OBJECT_COUNT=(\d+);TABLE_COUNT=(\d+)/);
  if (!match) throw new Error("Rhino deep object-count receipt was invalid");
  return {
    activeCount: Number(match[1]),
    tableCount: Number(match[2]),
  };
}

export async function blenderSceneReceipt() {
  const payload = await blenderCommand({
    type: "execute_code",
    params: {
      code: [
        "import bpy, json",
        "objects = [{'name': obj.name, 'type': obj.type} for obj in bpy.data.objects]",
        "print('AEC_SCENE_RECEIPT=' + json.dumps(objects, separators=(',', ':')))",
      ].join("\n"),
    },
  });
  if (payload.status !== "success") throw new Error(payload.message ?? "Blender count failed");
  const match = payload.result?.result?.match(/AEC_SCENE_RECEIPT=(\[[^\r\n]*\])/);
  if (!match) throw new Error("Blender returned no scene receipt");
  const objects = JSON.parse(match[1]) as Array<{ name: string; type: string }>;
  const allowedDefaults = new Map([
    ["Cube", "MESH"],
    ["Camera", "CAMERA"],
    ["Light", "LIGHT"],
  ]);
  const uniqueNames = new Set(objects.map((object) => object.name));
  const defaultBaseline =
    objects.length > 0
    &&
    uniqueNames.size === objects.length
    && objects.every((object) => allowedDefaults.get(object.name) === object.type);
  return {
    count: objects.length,
    objects,
    defaultBaseline,
  };
}

export async function verifySceneCounts() {
  const [rhino, blender] = await Promise.all([rhinoObjectCount(), blenderSceneReceipt()]);
  const blenderClean = blender.count === 0 || blender.defaultBaseline;
  return {
    rhinoCount: rhino.activeCount,
    rhinoTableCount: rhino.tableCount,
    blenderCount: blender.count,
    blenderObjects: blender.objects,
    blenderDefaultBaseline: blender.defaultBaseline,
    empty: rhino.activeCount === 0 && rhino.tableCount === 0 && blenderClean,
  };
}

export async function resetScenes() {
  await fs.mkdir(CONTROL_DIR, { recursive: true });
  await fs.writeFile(SCENE_STATE_FILE, JSON.stringify({
    status: "verifying",
    startedAt: new Date().toISOString(),
  }), "utf8");

  const rhinoScript = [
    rhinoDeepEnumerator,
    "var objects = __rhino_doc__.Objects.FindByFilter(settings);",
    "var deleted = 0;",
    "foreach (var obj in objects) {",
    "  var layer = __rhino_doc__.Layers[obj.Attributes.LayerIndex];",
    "  if (layer != null && !layer.IsDeleted) {",
    "    layer.IsLocked = false;",
    "    layer.IsVisible = true;",
    "    layer.CommitChanges();",
    "  }",
    "  __rhino_doc__.Objects.Unlock(obj.Id, true);",
    "  __rhino_doc__.Objects.Show(obj.Id, true);",
    "  if (__rhino_doc__.Objects.Delete(obj.Id, true)) deleted++;",
    "}",
    "for (int i = __rhino_doc__.InstanceDefinitions.Count - 1; i >= 0; i--) {",
    "  var idef = __rhino_doc__.InstanceDefinitions[i];",
    "  if (idef != null && !idef.IsDeleted) __rhino_doc__.InstanceDefinitions.Delete(i, true, true);",
    "}",
    "// Force-deleted objects remain recoverable in Rhino's undo table. Purge",
    "// them so a reset is a truly blank scene, not merely zero active objects.",
    "__rhino_doc__.ClearUndoRecords(true);",
    "__rhino_doc__.Views.Redraw();",
    "var remaining = __rhino_doc__.Objects.FindByFilter(settings);",
    "System.Console.WriteLine(\"AEC_RESET_DELETED=\" + deleted + \";ENUMERATED=\" + objects.Length + \";REMAINING=\" + remaining.Length + \";TABLE_COUNT=\" + __rhino_doc__.Objects.Count);",
    "foreach (var obj in remaining) System.Console.WriteLine(\"AEC_RESET_REMAINS=\" + obj.Id + \"|\" + obj.Name + \"|\" + obj.Attributes.Mode);",
  ].join("\n");
  const blenderScript = [
    "import bpy",
    "deleted = len(bpy.data.objects)",
    "for obj in list(bpy.data.objects):",
    "    bpy.data.objects.remove(obj, do_unlink=True)",
    "for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):",
    "    for block in list(datablocks):",
    "        if block.users == 0: datablocks.remove(block)",
    "print('AEC_RESET_DELETED=' + str(deleted))",
  ].join("\n");

  try {
    await Promise.all([
      rhinoTool("run_csharp", { script: rhinoScript }),
      blenderCommand({ type: "execute_code", params: { code: blenderScript } }).then((payload) => {
        if (payload.status !== "success") throw new Error(payload.message ?? "Blender reset failed");
      }),
    ]);
    const counts = await verifySceneCounts();
    const receipt = {
      status: counts.empty ? "empty" : "occupied",
      ...counts,
      verifiedAt: new Date().toISOString(),
    };
    await fs.writeFile(SCENE_STATE_FILE, JSON.stringify(receipt), "utf8");
    return receipt;
  } catch (error) {
    const receipt = {
      status: "error",
      error: error instanceof Error ? error.message : String(error),
      verifiedAt: new Date().toISOString(),
    };
    await fs.writeFile(SCENE_STATE_FILE, JSON.stringify(receipt), "utf8");
    throw error;
  }
}

async function cancelQueuedJobs() {
  let entries: string[] = [];
  try { entries = await fs.readdir(CONTROL_DIR); } catch { return 0; }
  let cancelled = 0;
  for (const name of entries) {
    if (!/^job-.+\.(json|processing)$/.test(name)) continue;
    const source = path.join(CONTROL_DIR, name);
    const target = `${source}.cancelled`;
    try {
      await fs.rename(source, target);
      cancelled++;
    } catch {
      // A worker may have completed the queue move between listing and rename.
    }
  }
  return cancelled;
}

async function isAecProcess(pid: number) {
  const script = [
    `$p = Get-CimInstance Win32_Process -Filter "ProcessId=${pid}" -ErrorAction SilentlyContinue`,
    "if ($p) { $p.CommandLine }",
  ].join("; ");
  const result = await runProcess("powershell.exe", ["-NoProfile", "-Command", script]);
  return result.code === 0
    && /hermes_resident_worker|Start-Hermes-AEC-Rhino-DML|Start-Hermes-ControlRun|hermes\.exe/i.test(result.stdout);
}

export async function emergencyStop() {
  await fs.mkdir(CONTROL_DIR, { recursive: true });
  const resident = await residentAgentState();
  let dashboard: { pid?: number; job_id?: string; started_at?: string } = {};
  try { dashboard = JSON.parse(await fs.readFile(DASHBOARD_RUN_FILE, "utf8")); } catch {}
  const pids = new Set<number>();
  if (resident?.pid) pids.add(resident.pid);
  if (dashboard.pid) pids.add(dashboard.pid);

  const killed: number[] = [];
  for (const pid of pids) {
    if (!(await isAecProcess(pid))) continue;
    const result = await runProcess("taskkill.exe", ["/PID", String(pid), "/T", "/F"]);
    if (result.code === 0) killed.push(pid);
  }
  const cancelled = await cancelQueuedJobs();
  const stoppedAt = new Date().toISOString();
  await fs.writeFile(path.join(CONTROL_DIR, "resident-agent.json"), JSON.stringify({
    pid: resident?.pid ?? 0,
    status: "stopped",
    updated_at: Date.now() / 1000,
    last_job_id: resident?.job_id ?? resident?.last_job_id ?? null,
    emergency_stop_at: stoppedAt,
  }), "utf8");
  await Promise.all([
    fs.rm(path.join(CONTROL_DIR, "resident-agent.lock"), { force: true }),
    fs.rm(path.join(CONTROL_DIR, "resident-agent.stop"), { force: true }),
  ]);
  await fs.writeFile(DASHBOARD_RUN_FILE, JSON.stringify({
    ...dashboard,
    status: "aborted",
    completed_at: stoppedAt,
    emergency_stop: true,
  }), "utf8");
  return { killed, cancelled, stoppedAt };
}
