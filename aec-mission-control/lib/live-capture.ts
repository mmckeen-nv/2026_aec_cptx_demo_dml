import { promises as fs } from "node:fs";
import net from "node:net";
import path from "node:path";
import { CONTROL_DIR } from "@/lib/local-aec";

type Capture = {
  body: Buffer;
  contentType: string;
  capturedAt: number;
};

const CACHE_MS = 850;
const BLENDER_BASELINE_CACHE_MS = 5_000;
const captureCache = new Map<string, Capture>();
const inflight = new Map<string, Promise<Capture>>();
let blenderBaselineCache: { checkedAt: number; isDefault: boolean } | null = null;

async function cached(key: string, producer: () => Promise<Capture>): Promise<Capture> {
  const existing = captureCache.get(key);
  if (existing && Date.now() - existing.capturedAt < CACHE_MS) return existing;
  const active = inflight.get(key);
  if (active) return active;
  const task = producer()
    .then((capture) => {
      captureCache.set(key, capture);
      return capture;
    })
    .finally(() => inflight.delete(key));
  inflight.set(key, task);
  return task;
}

export async function captureRhino(): Promise<Capture> {
  return cached("rhino", async () => {
    const response = await fetch("http://127.0.0.1:10500/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json, text/event-stream",
      },
      body: JSON.stringify({
        jsonrpc: "2.0",
        id: Date.now(),
        method: "tools/call",
        params: {
          name: "get_viewport_image",
          arguments: {
            width: 1280,
            height: 720,
            view: "perspective",
            displayMode: "Shaded",
            boxMin: { x: -15, y: -20, z: -1.25 },
            boxMax: { x: 25, y: 16, z: 10 },
            zoom: 0.88,
          },
        },
      }),
      cache: "no-store",
      signal: AbortSignal.timeout(3500),
    });
    if (!response.ok) throw new Error(`Rhino capture returned ${response.status}`);
    const payload = await response.json() as {
      result?: { content?: Array<{ type?: string; data?: string; mimeType?: string }> };
    };
    const image = payload.result?.content?.find((item) => item.type === "image" && item.data);
    if (!image?.data) throw new Error("Rhino capture returned no image");
    return {
      body: Buffer.from(image.data, "base64"),
      contentType: image.mimeType ?? "image/jpeg",
      capturedAt: Date.now(),
    };
  });
}

function blenderCommand(command: object): Promise<unknown> {
  return new Promise((resolve, reject) => {
    const socket = net.createConnection({ host: "127.0.0.1", port: 9876 });
    const chunks: Buffer[] = [];
    const timer = setTimeout(() => {
      socket.destroy();
      reject(new Error("Blender capture timed out"));
    }, 4500);
    socket.once("connect", () => socket.write(JSON.stringify(command)));
    socket.on("data", (chunk) => chunks.push(Buffer.from(chunk)));
    socket.once("end", () => {
      clearTimeout(timer);
      try {
        resolve(JSON.parse(Buffer.concat(chunks).toString("utf8")));
      } catch (error) {
        reject(error);
      }
    });
    // Blender keeps the connection open for reuse. Its response is a complete
    // JSON document, so parse as soon as a full object arrives.
    socket.on("data", () => {
      try {
        const parsed = JSON.parse(Buffer.concat(chunks).toString("utf8"));
        clearTimeout(timer);
        socket.end();
        resolve(parsed);
      } catch {
        // Wait for the remaining response bytes.
      }
    });
    socket.once("error", (error) => {
      clearTimeout(timer);
      reject(error);
    });
  });
}

export async function blenderHasOnlyDefaultScene(): Promise<boolean> {
  if (
    blenderBaselineCache
    && Date.now() - blenderBaselineCache.checkedAt < BLENDER_BASELINE_CACHE_MS
  ) {
    return blenderBaselineCache.isDefault;
  }
  const response = await blenderCommand({
    type: "execute_code",
    params: {
      code: [
        "import bpy, json",
        "objects = [{'name': obj.name, 'type': obj.type} for obj in bpy.data.objects]",
        "print('AEC_LIVE_SCENE=' + json.dumps(objects, separators=(',', ':')))",
      ].join("\n"),
    },
  }) as { status?: string; result?: { result?: string }; message?: string };
  if (response.status !== "success") {
    throw new Error(response.message ?? "Blender scene inspection failed");
  }
  const match = response.result?.result?.match(/AEC_LIVE_SCENE=(\[[^\r\n]*\])/);
  if (!match) throw new Error("Blender scene inspection returned no receipt");
  const objects = JSON.parse(match[1]) as Array<{ name: string; type: string }>;
  const defaults = new Map([
    ["Cube", "MESH"],
    ["Camera", "CAMERA"],
    ["Light", "LIGHT"],
  ]);
  const names = new Set(objects.map((object) => object.name));
  const isDefault = (
    objects.length <= defaults.size
    && names.size === objects.length
    && objects.every((object) => defaults.get(object.name) === object.type)
  );
  blenderBaselineCache = { checkedAt: Date.now(), isDefault };
  return isDefault;
}

export async function captureBlender(): Promise<Capture> {
  return cached("blender", async () => {
    const liveDir = path.join(CONTROL_DIR, "live");
    const filepath = path.join(liveDir, "blender-viewport.jpg");
    await fs.mkdir(liveDir, { recursive: true });
    const response = await blenderCommand({
      type: "get_viewport_screenshot",
      params: { max_size: 1280, filepath, format: "jpg" },
    }) as { status?: string; result?: { success?: boolean }; message?: string };
    if (response.status !== "success" || !response.result?.success) {
      throw new Error(response.message ?? "Blender capture failed");
    }
    return {
      body: await fs.readFile(filepath),
      contentType: "image/jpeg",
      capturedAt: Date.now(),
    };
  });
}
