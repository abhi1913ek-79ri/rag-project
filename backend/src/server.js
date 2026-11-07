import express from "express";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, "..");
const clientDir = path.resolve(rootDir, process.env.CLIENT_DIR ?? "../client");
const ragUrl = (process.env.RAG_SERVICE_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");
const port = Number(process.env.PORT ?? 3000);
const app = express();
const requestCounts = new Map();

app.disable("x-powered-by");
app.use(express.json({ limit: "64kb" }));
app.use((request, response, next) => {
  const origin = process.env.ALLOWED_ORIGIN ?? "http://127.0.0.1:3000";
  response.setHeader("Access-Control-Allow-Origin", origin);
  response.setHeader("Access-Control-Allow-Methods", "GET,POST,DELETE,OPTIONS");
  response.setHeader("Access-Control-Allow-Headers", "Content-Type");
  if (request.method === "OPTIONS") return response.sendStatus(204);
  next();
});

function rateLimit(request, response, next) {
  const now = Date.now();
  const key = request.ip;
  const recent = (requestCounts.get(key) ?? []).filter((timestamp) => now - timestamp < 60_000);
  if (recent.length >= 30) return response.status(429).json({ detail: "Too many requests. Try again shortly." });
  recent.push(now);
  requestCounts.set(key, recent);
  next();
}

async function forward(request, response, targetPath, init = {}) {
  try {
    const upstream = await fetch(`${ragUrl}${targetPath}`, {
      ...init,
      signal: AbortSignal.timeout(120_000),
    });
    const body = await upstream.text();
    response.status(upstream.status);
    response.type(upstream.headers.get("content-type") ?? "application/json");
    response.send(body);
  } catch (error) {
    console.error("RAG service unavailable:", error instanceof Error ? error.message : "unknown error");
    response.status(503).json({ detail: "The RAG service is unavailable. Start the Python service and try again." });
  }
}

app.get("/api/health", (_request, response) => response.json({ status: "ok", service: "gateway" }));
app.get("/api/documents", rateLimit, (request, response) => forward(request, response, "/documents"));
app.get("/api/documents/:documentId", rateLimit, (request, response) => forward(request, response, `/documents/${encodeURIComponent(request.params.documentId)}`));
app.delete("/api/documents/:documentId", rateLimit, (request, response) => forward(request, response, `/documents/${encodeURIComponent(request.params.documentId)}`, { method: "DELETE" }));
app.post("/api/audit", rateLimit, (request, response) => forward(request, response, "/audit", {
  method: "POST",
  headers: { "content-type": "application/json" },
  body: JSON.stringify(request.body),
}));

app.post("/api/upload", rateLimit, express.raw({ type: "multipart/form-data", limit: "12mb" }), (request, response) => {
  forward(request, response, "/upload", {
    method: "POST",
    headers: { "content-type": request.headers["content-type"] ?? "multipart/form-data" },
    body: request.body,
  });
});

app.use(express.static(clientDir));
app.get("*splat", (_request, response) => response.sendFile(path.join(clientDir, "index.html")));

app.listen(port, () => console.log(`Gateway listening on http://127.0.0.1:${port}`));
