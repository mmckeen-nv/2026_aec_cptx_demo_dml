import { promises as fs } from "node:fs";
import path from "node:path";
import { artifactPath } from "@/lib/local-aec";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(_request: Request, { params }: { params: Promise<{ kind: string }> }) {
  const { kind } = await params;
  const file = await artifactPath(kind);
  if (!file) {
    const label = kind === "comfy" ? "FLUX.2" : kind.toUpperCase();
    const placeholder = `
      <svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900">
        <rect width="1600" height="900" fill="#111712"/>
        <path d="M0 450h1600M800 0v900" stroke="#263127" stroke-width="1"/>
        <circle cx="800" cy="405" r="18" fill="none" stroke="#c6f66f" stroke-width="4" opacity=".9"/>
        <path d="M800 387a18 18 0 0 1 18 18" fill="none" stroke="#111712" stroke-width="6"/>
        <text x="800" y="470" fill="#c6f66f" font-family="monospace" font-size="28" text-anchor="middle">${label}</text>
        <text x="800" y="515" fill="#7f8b81" font-family="monospace" font-size="18" text-anchor="middle">WAITING FOR CURRENT RUN OUTPUT</text>
      </svg>`;
    return new Response(placeholder, {
      headers: {
        "Content-Type": "image/svg+xml",
        "Cache-Control": "no-store, max-age=0",
        "X-AEC-Artifact": "waiting-current-run",
      },
    });
  }
  const body = await fs.readFile(file);
  const extension = path.extname(file).toLowerCase();
  const contentType = extension === ".jpg" || extension === ".jpeg" ? "image/jpeg" : "image/png";
  return new Response(body, {
    headers: {
      "Content-Type": contentType,
      "Cache-Control": "no-store, max-age=0",
      "X-AEC-Artifact": path.basename(file),
    },
  });
}
