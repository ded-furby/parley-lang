import { serve } from "@hono/node-server";
import { serveStatic } from "@hono/node-server/serve-static";
import { Hono } from "hono";
import { z } from "zod";

import { assessRelease } from "./scoring.js";


declare const process: { env: Record<string, string | undefined> };

const maxBodyBytes = 16_384;
const publicRoot = process.env.RELEASE_RADAR_PUBLIC ?? "../../../examples/release-radar/public";
const browserModule = process.env.RELEASE_RADAR_BROWSER ?? "./dist/scoring.js";
const releaseSchema = z.object({
  version: z.string(),
  tests_passed: z.number().int(),
  tests_total: z.number().int(),
  checklist_done: z.number().int(),
  checklist_total: z.number().int(),
  package_ready: z.boolean(),
}).strict();

const response = (value: unknown, status = 200) => new Response(JSON.stringify(value), {
  status,
  headers: { "content-type": "application/json" },
});
const error = (code: string, status: number, detail: string) => (
  response({ error: code, detail }, status)
);

const app = new Hono();

app.get("/api/status", () => response({
  service: "Release Radar",
  milestone: "typed-http-json-plus-browser-wasm",
  typed_routes: 2,
  browser_exports: 1,
  ready: true,
}));

app.post("/api/assess", async (context) => {
  const mediaType = (context.req.header("content-type") ?? "").split(";", 1)[0]!.trim().toLowerCase();
  if (mediaType !== "application/json" && !mediaType.endsWith("+json")) {
    return error("json_content_type_required", 415, "expected application/json");
  }
  const declared = context.req.header("content-length");
  if (declared && (!/^\d+$/.test(declared) || Number(declared) > maxBodyBytes)) {
    return error("body_too_large", 413, "request body exceeds 16384 bytes");
  }
  const raw = await context.req.arrayBuffer();
  if (raw.byteLength > maxBodyBytes) {
    return error("body_too_large", 413, "request body exceeds 16384 bytes");
  }
  try {
    const value: unknown = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(raw));
    const parsed = releaseSchema.safeParse(value);
    if (!parsed.success) return error("invalid_json", 400, parsed.error.message);
    return response(assessRelease(parsed.data));
  } catch (caught) {
    return error("invalid_json", 400, String(caught));
  }
});

app.all("/api/*", (context) => error("not_found", 404, `no API route ${context.req.path}`));
app.get("/parley.js", serveStatic({ path: browserModule }));
app.get("/*", serveStatic({ root: publicRoot }));

serve({
  fetch: app.fetch,
  hostname: "127.0.0.1",
  port: Number(process.env.PARLEY_WEB_PORT ?? "8787"),
});
