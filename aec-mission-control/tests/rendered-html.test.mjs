import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const appRoot = new URL("../app/", import.meta.url);

test("renders the AEC Mission Control workflow", async () => {
  const [page, layout, styles] = await Promise.all([
    readFile(new URL("page.tsx", appRoot), "utf8"),
    readFile(new URL("layout.tsx", appRoot), "utf8"),
    readFile(new URL("globals.css", appRoot), "utf8"),
  ]);

  assert.match(layout, /Cliff House Control Plane/);
  assert.match(page, /Run automatically/i);
  assert.match(page, /Build manually/i);
  assert.match(page, /Reset scenes/i);
  assert.match(page, /EMERGENCY STOP/i);
  assert.match(page, /RESTART/i);
  assert.match(page, /Preflight Check/i);
  assert.match(page, /Agent Actions/i);
  assert.match(page, /Memory Harness Recall/i);
  assert.match(page, /FLUX\.2/i);
  assert.match(page, /standby/i);
  assert.match(styles, /scanline/);
  assert.match(styles, /signal-lock/);
});

test("exposes the required local control APIs", async () => {
  const routeNames = [
    "activity",
    "control",
    "metrics",
    "preflight",
    "resolve",
    "status",
    "system-control",
  ];

  for (const name of routeNames) {
    const route = await readFile(
      new URL(`api/${name}/route.ts`, appRoot),
      "utf8",
    );
    assert.match(route, /export async function (GET|POST)/);
  }

  const imageRoute = await readFile(
    new URL("api/image/[kind]/route.ts", appRoot),
    "utf8",
  );
  const liveRoute = await readFile(
    new URL("api/live/[kind]/route.ts", appRoot),
    "utf8",
  );
  assert.match(imageRoute, /export async function GET/);
  assert.match(liveRoute, /export async function GET/);
});
