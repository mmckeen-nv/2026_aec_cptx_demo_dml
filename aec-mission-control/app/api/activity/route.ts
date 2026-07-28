import path from "node:path";
import { LOG_DIR, tailLines } from "@/lib/local-aec";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const RHINO_TOOLS = new Set([
  "run_csharp",
  "run_python",
  "list_objects",
  "get_document_summary",
  "capture_viewport",
  "set_view",
  "zoom_extents",
  "save_document",
]);
const BLENDER_TOOLS = new Set([
  "get_scene_info",
  "get_object_info",
  "get_viewport_screenshot",
  "get_polyhaven_status",
  "set_texture",
]);

function mcpTool(tool: string) {
  const normalized = tool.split("__").at(-1) ?? tool;
  if (/daystrom_dml/i.test(tool)) return { service: "DML", tool: normalized };
  if (/rhino/i.test(tool) || RHINO_TOOLS.has(normalized)) return { service: "Rhino", tool: normalized };
  if (/blender/i.test(tool) || BLENDER_TOOLS.has(normalized)) return { service: "Blender", tool: normalized };
  return null;
}

function simplify(line: string) {
  const stamp = line.match(/^(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2}:\d{2})/);
  const text = line.replace(/^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2},?\d*\s+(INFO|WARN|WARNING|ERROR)\s+/, "");
  let kind = "system";
  if (/tool|mcp|execute_code|vision_analyze/i.test(text)) kind = "tool";
  if (/API call|OpenAI client|conversation_loop|model=/i.test(text)) kind = "model";

  const toolResult = text.match(/\btool\s+([A-Za-z0-9_:-]+)\s+(completed|returned error)\s+\(([^)]+)\)/i);
  if (toolResult) {
    const call = mcpTool(toolResult[1]);
    if (call) {
      const outcome = /completed/i.test(toolResult[2]) ? "success" : "failed";
      return {
        time: stamp?.[2] ?? "--:--:--",
        kind: "mcp",
        text: `${call.service} MCP · ${call.tool} · ${outcome} · ${toolResult[3]}`,
      };
    }
  }

  const registration = text.match(/MCP server '([^']+)'.*registered\s+(\d+)\s+tool/i);
  if (registration) {
    return {
      time: stamp?.[2] ?? "--:--:--",
      kind: "mcp",
      text: `${registration[1]} MCP · ${registration[2]} tools registered`,
    };
  }

  if (/Daystrom DCN active-read|Daystrom DML retrieved|Daystrom DML stored/i.test(text)) {
    kind = "memory";
  }
  return { time: stamp?.[2] ?? "--:--:--", kind, text: text.slice(0, 240) };
}

export async function GET() {
  const lines = await tailLines(path.join(LOG_DIR, "agent.log"));
  // Client-open/client-close messages occur twice per model turn and used to
  // crowd the application calls out of the visible stream. Preserve the model
  // call summary, but reserve enough history for every recent MCP completion.
  const relevant = lines.filter((line) => /tool|mcp|API call|conversation_loop|vision|DML|iteration/i.test(line));
  const simplified = relevant.map(simplify);
  const recentStart = Math.max(0, simplified.length - 48);
  const mcpIndexes = simplified
    .map((event, index) => event.kind === "mcp" ? index : -1)
    .filter((index) => index >= 0);
  const retainedMcpStart = mcpIndexes.slice(-24)[0] ?? Number.POSITIVE_INFINITY;
  const events = simplified.filter((event, index) =>
    index >= recentStart || (event.kind === "mcp" && index >= retainedMcpStart)
  );
  return Response.json({ events: events.reverse() }, {
    headers: { "Cache-Control": "no-store" },
  });
}
