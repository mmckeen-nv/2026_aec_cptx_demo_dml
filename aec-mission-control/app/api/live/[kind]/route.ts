import { promises as fs } from "node:fs";
import { createHash } from "node:crypto";
import path from "node:path";
import { artifactPath, residentAgentState, visualWallIsStandby } from "@/lib/local-aec";
import { blenderHasOnlyDefaultScene, captureBlender, captureRhino } from "@/lib/live-capture";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
const STANDBY_CARD = path.join(process.cwd(), "public", "standby-nvidia-aec.png");

type ResponseHeaders = Record<string, string>;

function imageResponse(
  body: Buffer,
  contentType: string,
  mode: string,
  extraHeaders: ResponseHeaders = {},
) {
  const bytes = new Uint8Array(body);
  return new Response(bytes, {
    headers: {
      "Content-Type": contentType,
      "Cache-Control": "no-store, max-age=0",
      "X-AEC-Mode": mode,
      "X-AEC-Signal": createHash("sha1").update(body).digest("hex").slice(0, 12),
      ...extraHeaders,
    },
  });
}

async function waiting() {
  return fileResponse(STANDBY_CARD, "standby");
}

async function fileResponse(file: string, mode: string, extraHeaders: ResponseHeaders = {}) {
  const extension = path.extname(file).toLowerCase();
  return imageResponse(
    await fs.readFile(file),
    extension === ".jpg" || extension === ".jpeg" ? "image/jpeg" : "image/png",
    mode,
    extraHeaders,
  );
}

type ComfyQueueItem = [
  number,
  string,
  Record<string, { class_type?: string; inputs?: Record<string, unknown> }>,
  { client_id?: string },
  string[],
];

async function fluxQueueHeaders(): Promise<ResponseHeaders> {
  try {
    const response = await fetch("http://127.0.0.1:8188/queue", {
      cache: "no-store",
      signal: AbortSignal.timeout(1_200),
    });
    if (!response.ok) return {};
    const queue = await response.json() as {
      queue_running?: ComfyQueueItem[];
      queue_pending?: ComfyQueueItem[];
    };
    const isFlux = (item: ComfyQueueItem) => (
      item[3]?.client_id === "aec-flux2-direct"
      || Object.values(item[2] ?? {}).some((node) => (
        node.class_type === "Flux2Scheduler"
        || (
          node.class_type === "UNETLoader"
          && String(node.inputs?.unet_name ?? "").toLowerCase().includes("flux")
        )
      ))
    );
    const running = queue.queue_running?.find(isFlux);
    const pending = queue.queue_pending?.find(isFlux);
    const item = running ?? pending;
    if (!item) return { "X-AEC-Flux-State": "idle" };
    const nodes = Object.values(item[2] ?? {});
    const scheduler = nodes.find((node) => node.class_type === "Flux2Scheduler");
    const steps = Number(scheduler?.inputs?.steps ?? 0);
    return {
      "X-AEC-Flux-State": running ? "processing" : "queued",
      "X-AEC-Flux-Prompt": item[1],
      "X-AEC-Flux-Nodes": String(nodes.length),
      "X-AEC-Flux-Steps": Number.isFinite(steps) ? String(steps) : "0",
      "X-AEC-Flux-Ahead": String(
        pending
          ? Math.max(0, (queue.queue_pending?.findIndex((queued) => queued[1] === item[1]) ?? 0))
          : 0,
      ),
    };
  } catch {
    return {};
  }
}

export async function GET(_request: Request, { params }: { params: Promise<{ kind: string }> }) {
  const { kind } = await params;
  try {
    if (await visualWallIsStandby()) return waiting();
    if (kind === "rhino") {
      const capture = await captureRhino();
      return imageResponse(capture.body, capture.contentType, "live");
    }
    if (kind === "blender") {
      // A completed current-run beauty frame is the most useful Blender
      // signal and is written before the depth pass. Prefer it immediately so
      // the visual wall cannot show Depth while Blender is still waiting on a
      // competing viewport request.
      const rendered = await artifactPath("blender");
      if (rendered) return fileResponse(rendered, "final");

      // Blender recreates Cube/Camera/Light when a new factory scene opens.
      // That baseline is an idle state, not fresh pipeline output. Never run
      // this inspection while Hermes is active: viewer polling must not compete
      // with the production Blender MCP workload.
      const resident = await residentAgentState();
      if (resident?.status === "running") return waiting();
      if (await blenderHasOnlyDefaultScene()) return waiting();
      const capture = await captureBlender();
      return imageResponse(capture.body, capture.contentType, "live");
    }
    if (kind === "depth") {
      // Depth is downstream of Blender. Do not reveal it unless the current
      // run's Blender render is already available to the preceding viewer.
      if (!(await artifactPath("blender"))) return waiting();
      const depth = await artifactPath("depth");
      if (depth) return fileResponse(depth, "final");
      return waiting();
    }
    if (kind === "comfy") {
      // Check the live queue even when a previous final exists. During an
      // operator-requested regeneration the old final remains the preview,
      // while these headers keep the progress overlay visible until the new
      // frame replaces it.
      const queueHeaders = await fluxQueueHeaders();
      const final = await artifactPath("comfy");
      if (final) return fileResponse(final, "final", queueHeaders);
      const source = await artifactPath("comfy-source");
      if (source) {
        const extension = path.extname(source).toLowerCase();
        return imageResponse(
          await fs.readFile(source),
          extension === ".jpg" || extension === ".jpeg" ? "image/jpeg" : "image/png",
          "source",
          queueHeaders,
        );
      }
      return waiting();
    }
  } catch {
    const fallback = await artifactPath(kind);
    if (fallback) return fileResponse(fallback, "fallback");
  }
  return waiting();
}
